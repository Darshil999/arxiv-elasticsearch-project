#!/usr/bin/env python3
"""
Ingest data into Elasticsearch.

This script connects to the Elasticsearch cluster, creates the index with proper
mapping, and bulk indexes the papers with their embeddings.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Generator
from tqdm import tqdm
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def get_elasticsearch_client() -> Elasticsearch:
    """
    Create and return an Elasticsearch client.
    
    Returns:
        Elasticsearch client instance
    """
    hosts = os.getenv('ELASTICSEARCH_HOSTS', 'http://localhost:9200').split(',')
    username = os.getenv('ELASTICSEARCH_USERNAME', '')
    password = os.getenv('ELASTICSEARCH_PASSWORD', '')
    
    logger.info(f"Connecting to Elasticsearch at {hosts}...")
    
    if username and password:
        client = Elasticsearch(
            hosts=hosts,
            basic_auth=(username, password),
            verify_certs=False,
            request_timeout=60
        )
    else:
        client = Elasticsearch(
            hosts=hosts,
            verify_certs=False,
            request_timeout=60
        )
    
    # Check connection
    if not client.ping():
        raise ConnectionError("Could not connect to Elasticsearch")
    
    info = client.info()
    logger.info(f"Connected to Elasticsearch cluster: {info['cluster_name']} (version {info['version']['number']})")
    
    return client


def load_index_mapping(mapping_file: str = './config/index_mapping.json') -> Dict[str, Any]:
    """
    Load index mapping from JSON file.
    
    Args:
        mapping_file: Path to the mapping JSON file
        
    Returns:
        Index mapping configuration
    """
    logger.info(f"Loading index mapping from {mapping_file}...")
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    return mapping


def create_index(client: Elasticsearch, index_name: str, mapping: Dict[str, Any]):
    """
    Create Elasticsearch index with mapping.
    
    Args:
        client: Elasticsearch client
        index_name: Name of the index to create
        mapping: Index mapping configuration
    """
    # Check if index exists
    if client.indices.exists(index=index_name):
        logger.info(f"Index '{index_name}' already exists")
        response = input("Do you want to delete and recreate the index? (y/N): ")
        if response.lower() == 'y':
            logger.info(f"Deleting index '{index_name}'...")
            client.indices.delete(index=index_name)
        else:
            return
    
    logger.info(f"Creating index '{index_name}'...")
    client.indices.create(
        index=index_name,
        settings=mapping.get('settings', {}),
        mappings=mapping.get('mappings', {})
    )
    logger.info(f"Index '{index_name}' created successfully")


def load_papers(input_file: str) -> List[Dict[str, Any]]:
    """
    Load papers with embeddings from JSON file.
    
    Args:
        input_file: Path to the papers JSON file
        
    Returns:
        List of paper dictionaries
    """
    logger.info(f"Loading papers from {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    logger.info(f"Loaded {len(papers)} papers")
    return papers


def generate_actions(
    papers: List[Dict[str, Any]],
    index_name: str
) -> Generator[Dict[str, Any], None, None]:
    """
    Generate bulk index actions for papers.
    
    Args:
        papers: List of paper dictionaries
        index_name: Name of the target index
        
    Yields:
        Bulk action dictionaries
    """
    for paper in papers:
        action = {
            '_index': index_name,
            '_id': paper.get('id', ''),
            '_source': {
                'paper_id': paper.get('id', ''),
                'title': paper.get('title', ''),
                'abstract': paper.get('abstract', ''),
                'categories': paper.get('categories', []),
                'authors': paper.get('authors', ''),
                'update_date': paper.get('update_date', ''),
                'abstract_vector': paper.get('abstract_vector', [])
            }
        }
        yield action


def bulk_index_papers(
    client: Elasticsearch,
    papers: List[Dict[str, Any]],
    index_name: str,
    batch_size: int = 500
) -> int:
    """
    Bulk index papers into Elasticsearch.
    
    Args:
        client: Elasticsearch client
        papers: List of papers with embeddings
        index_name: Name of the target index
        batch_size: Number of documents per batch
        
    Returns:
        Number of successfully indexed documents
    """
    logger.info(f"Indexing {len(papers)} papers into '{index_name}'...")
    
    total_indexed = 0
    total_errors = 0
    
    # Process in batches with progress bar
    for i in tqdm(range(0, len(papers), batch_size), desc="Indexing batches"):
        batch = papers[i:i + batch_size]
        
        try:
            success, failed = bulk(
                client,
                generate_actions(batch, index_name),
                raise_on_error=False,
                stats_only=True
            )
            total_indexed += success
            total_errors += failed
            
        except BulkIndexError as e:
            logger.error(f"Bulk index error: {e}")
            total_errors += len(batch)
            
        except Exception as e:
            logger.error(f"Error indexing batch: {e}")
            total_errors += len(batch)
    
    logger.info(f"Indexed {total_indexed} documents, {total_errors} errors")
    
    # Refresh index to make documents searchable
    client.indices.refresh(index=index_name)
    
    return total_indexed


def verify_index(client: Elasticsearch, index_name: str):
    """
    Verify the index was created correctly.
    
    Args:
        client: Elasticsearch client
        index_name: Name of the index to verify
    """
    logger.info(f"Verifying index '{index_name}'...")
    
    # Get index stats
    stats = client.indices.stats(index=index_name)
    doc_count = stats['indices'][index_name]['primaries']['docs']['count']
    store_size = stats['indices'][index_name]['primaries']['store']['size_in_bytes']
    
    logger.info(f"Index '{index_name}' stats:")
    logger.info(f"  - Documents: {doc_count}")
    logger.info(f"  - Store size: {store_size / (1024*1024):.2f} MB")
    
    # Get shard info
    shards = client.cat.shards(index=index_name, format='json')
    primary_shards = [s for s in shards if s['prirep'] == 'p']
    replica_shards = [s for s in shards if s['prirep'] == 'r']
    
    logger.info(f"  - Primary shards: {len(primary_shards)}")
    logger.info(f"  - Replica shards: {len(replica_shards)}")


def main():
    """Main function to ingest data."""
    data_dir = os.getenv('DATA_DIR', './data')
    index_name = os.getenv('INDEX_NAME', 'arxiv-papers')
    batch_size = int(os.getenv('BATCH_SIZE', '500'))
    
    input_file = os.path.join(data_dir, 'cs_papers_with_embeddings.json')
    mapping_file = './config/index_mapping.json'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.info("Please run generate_embeddings.py first")
        return
    
    # Connect to Elasticsearch
    client = get_elasticsearch_client()
    
    # Load index mapping
    mapping = load_index_mapping(mapping_file)
    
    # Create index
    create_index(client, index_name, mapping)
    
    # Load papers
    papers = load_papers(input_file)
    
    # Bulk index papers
    bulk_index_papers(client, papers, index_name, batch_size)
    
    # Verify index
    verify_index(client, index_name)
    
    logger.info("Data ingestion complete!")


if __name__ == '__main__':
    main()
