#!/usr/bin/env python3
"""
Demo queries for demonstrating distributed system features.

This script demonstrates the three key distributed system features:
1. Sharding and Replication - Data distribution across multiple shards
2. HNSW ANN Vector Indexing - Semantic search using k-NN
3. Snapshot/Restore - Backup and recovery capabilities
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

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
    
    if not client.ping():
        raise ConnectionError("Could not connect to Elasticsearch")
    
    return client


def demo_sharding_replication(client: Elasticsearch, index_name: str):
    """
    Demonstrate sharding and replication feature.
    
    Args:
        client: Elasticsearch client
        index_name: Name of the index
    """
    print("\n" + "="*60)
    print("FEATURE 1: SHARDING AND REPLICATION")
    print("="*60)
    
    # 1. Cluster Health
    print("\n[1.1] Cluster Health")
    print("-" * 40)
    health = client.cluster.health()
    print(f"Cluster name: {health['cluster_name']}")
    print(f"Status: {health['status']}")
    print(f"Number of nodes: {health['number_of_nodes']}")
    print(f"Number of data nodes: {health['number_of_data_nodes']}")
    print(f"Active primary shards: {health['active_primary_shards']}")
    print(f"Active shards: {health['active_shards']}")
    print(f"Relocating shards: {health['relocating_shards']}")
    print(f"Unassigned shards: {health['unassigned_shards']}")
    
    # 2. Node Information
    print("\n[1.2] Cluster Nodes")
    print("-" * 40)
    nodes = client.cat.nodes(format='json', h='name,ip,role,master,heap.percent,ram.percent')
    for node in nodes:
        master_indicator = "★" if node.get('master') == '*' else " "
        print(f"  {master_indicator} {node['name']} ({node['ip']}) - Roles: {node['role']}")
    
    # 3. Index Settings (Shard Configuration)
    print("\n[1.3] Index Shard Configuration")
    print("-" * 40)
    try:
        settings = client.indices.get_settings(index=index_name)
        index_settings = settings[index_name]['settings']['index']
        print(f"Index: {index_name}")
        print(f"  - Number of primary shards: {index_settings.get('number_of_shards', 'N/A')}")
        print(f"  - Number of replicas: {index_settings.get('number_of_replicas', 'N/A')}")
    except Exception as e:
        logger.warning(f"Could not get index settings: {e}")
    
    # 4. Shard Allocation
    print("\n[1.4] Shard Allocation Across Nodes")
    print("-" * 40)
    try:
        shards = client.cat.shards(index=index_name, format='json')
        
        # Group shards by node
        node_shards = {}
        for shard in shards:
            node = shard.get('node', 'unassigned')
            if node not in node_shards:
                node_shards[node] = {'primary': 0, 'replica': 0}
            if shard['prirep'] == 'p':
                node_shards[node]['primary'] += 1
            else:
                node_shards[node]['replica'] += 1
        
        print(f"Total shards for '{index_name}':")
        for node, counts in node_shards.items():
            print(f"  - {node}: {counts['primary']} primary, {counts['replica']} replica")
        
        # Detailed shard allocation
        print("\nDetailed shard allocation:")
        print(f"{'Shard':<6} {'Type':<8} {'State':<12} {'Docs':<10} {'Node':<15}")
        print("-" * 55)
        for shard in sorted(shards, key=lambda x: (x['shard'], x['prirep'])):
            shard_type = 'Primary' if shard['prirep'] == 'p' else 'Replica'
            print(f"{shard['shard']:<6} {shard_type:<8} {shard['state']:<12} {shard.get('docs', 'N/A'):<10} {shard.get('node', 'unassigned'):<15}")
    except Exception as e:
        logger.warning(f"Could not get shard allocation: {e}")
    
    print("\n" + "="*60)
    print("SHARDING AND REPLICATION DEMO COMPLETE")
    print("="*60)


def demo_hnsw_vector_search(client: Elasticsearch, index_name: str):
    """
    Demonstrate HNSW ANN vector search feature.
    
    Args:
        client: Elasticsearch client
        index_name: Name of the index
    """
    print("\n" + "="*60)
    print("FEATURE 2: HNSW ANN VECTOR INDEXING")
    print("="*60)
    
    # 1. Index mapping info
    print("\n[2.1] Vector Field Configuration")
    print("-" * 40)
    try:
        mapping = client.indices.get_mapping(index=index_name)
        vector_config = mapping[index_name]['mappings']['properties'].get('abstract_vector', {})
        print(f"Vector field: abstract_vector")
        print(f"  - Type: {vector_config.get('type', 'N/A')}")
        print(f"  - Dimensions: {vector_config.get('dims', 'N/A')}")
        print(f"  - Similarity: {vector_config.get('similarity', 'N/A')}")
        if 'index_options' in vector_config:
            print(f"  - Index type: {vector_config['index_options'].get('type', 'N/A')}")
            print(f"  - HNSW m: {vector_config['index_options'].get('m', 'N/A')}")
            print(f"  - HNSW ef_construction: {vector_config['index_options'].get('ef_construction', 'N/A')}")
    except Exception as e:
        logger.warning(f"Could not get vector field configuration: {e}")
    
    # 2. Get a sample document to use as query vector
    print("\n[2.2] Sample Semantic Search")
    print("-" * 40)
    
    try:
        # Get a sample document
        sample = client.search(
            index=index_name,
            body={
                "size": 1,
                "query": {"match_all": {}}
            }
        )
        
        if sample['hits']['hits']:
            source_doc = sample['hits']['hits'][0]['_source']
            query_vector = source_doc.get('abstract_vector', [])
            
            if query_vector:
                print(f"Query document: '{source_doc['title'][:60]}...'")
                print(f"Query vector dimensions: {len(query_vector)}")
                
                # k-NN search
                print("\n[2.3] k-NN Search Results (Top 5 similar papers)")
                print("-" * 40)
                
                knn_results = client.search(
                    index=index_name,
                    body={
                        "size": 5,
                        "knn": {
                            "field": "abstract_vector",
                            "query_vector": query_vector,
                            "k": 5,
                            "num_candidates": 100
                        },
                        "_source": ["title", "categories", "authors"]
                    }
                )
                
                print("\nSimilar papers found:")
                for i, hit in enumerate(knn_results['hits']['hits'], 1):
                    print(f"\n{i}. Score: {hit['_score']:.4f}")
                    print(f"   Title: {hit['_source']['title'][:70]}...")
                    print(f"   Categories: {', '.join(hit['_source'].get('categories', []))}")
            else:
                logger.warning("No vector found in sample document")
        else:
            logger.warning("No documents found in index")
            
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
    
    # 3. Hybrid search (text + vector)
    print("\n[2.4] Hybrid Search (Text + Vector)")
    print("-" * 40)
    
    try:
        search_text = "deep learning neural network"
        print(f"Search query: '{search_text}'")
        
        # First, get embedding for search text (we'll use a document that matches)
        text_match = client.search(
            index=index_name,
            body={
                "size": 1,
                "query": {
                    "match": {
                        "abstract": search_text
                    }
                }
            }
        )
        
        if text_match['hits']['hits']:
            query_vector = text_match['hits']['hits'][0]['_source'].get('abstract_vector', [])
            
            if query_vector:
                # Hybrid search combining text and vector
                hybrid_results = client.search(
                    index=index_name,
                    body={
                        "size": 5,
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "match": {
                                            "abstract": {
                                                "query": search_text,
                                                "boost": 1.0
                                            }
                                        }
                                    }
                                ]
                            }
                        },
                        "knn": {
                            "field": "abstract_vector",
                            "query_vector": query_vector,
                            "k": 5,
                            "num_candidates": 100,
                            "boost": 1.0
                        },
                        "_source": ["title", "categories"]
                    }
                )
                
                print("\nHybrid search results:")
                for i, hit in enumerate(hybrid_results['hits']['hits'], 1):
                    print(f"  {i}. [{hit['_score']:.2f}] {hit['_source']['title'][:60]}...")
                    
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
    
    print("\n" + "="*60)
    print("HNSW VECTOR SEARCH DEMO COMPLETE")
    print("="*60)


def demo_snapshot_restore(client: Elasticsearch, index_name: str):
    """
    Demonstrate snapshot/restore feature.
    
    Args:
        client: Elasticsearch client
        index_name: Name of the index
    """
    print("\n" + "="*60)
    print("FEATURE 3: SNAPSHOT/RESTORE")
    print("="*60)
    
    repo_name = os.getenv('SNAPSHOT_REPO_NAME', 'arxiv_backup')
    repo_path = os.getenv('SNAPSHOT_REPO_PATH', '/usr/share/elasticsearch/snapshots')
    
    # 1. Register Repository
    print("\n[3.1] Snapshot Repository")
    print("-" * 40)
    
    try:
        # Check if repository exists
        repos = client.snapshot.get_repository(name=repo_name)
        print(f"Repository '{repo_name}' already registered")
        print(f"  - Type: {repos[repo_name]['type']}")
        print(f"  - Location: {repos[repo_name]['settings']['location']}")
    except Exception:
        try:
            # Create repository
            client.snapshot.create_repository(
                name=repo_name,
                body={
                    "type": "fs",
                    "settings": {
                        "location": repo_path,
                        "compress": True
                    }
                }
            )
            print(f"Repository '{repo_name}' created successfully")
            print(f"  - Type: fs")
            print(f"  - Location: {repo_path}")
        except Exception as e:
            logger.error(f"Could not create repository: {e}")
            return
    
    # 2. Create Snapshot
    print("\n[3.2] Create Snapshot")
    print("-" * 40)
    
    snapshot_name = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        print(f"Creating snapshot '{snapshot_name}'...")
        response = client.snapshot.create(
            repository=repo_name,
            snapshot=snapshot_name,
            body={"indices": index_name},
            wait_for_completion=True
        )
        print(f"Snapshot created successfully!")
        print(f"  - State: {response['snapshot']['state']}")
        print(f"  - Duration: {response['snapshot'].get('duration_in_millis', 0)}ms")
        print(f"  - Indices: {response['snapshot']['indices']}")
        shards = response['snapshot'].get('shards', {})
        print(f"  - Total shards: {shards.get('total', 0)}")
        print(f"  - Successful shards: {shards.get('successful', 0)}")
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        snapshot_name = None
    
    # 3. List Snapshots
    print("\n[3.3] List Snapshots")
    print("-" * 40)
    
    try:
        snapshots = client.snapshot.get(repository=repo_name, snapshot='*')
        
        print(f"Snapshots in '{repo_name}':")
        print(f"{'Name':<30} {'State':<12} {'Indices':<20} {'Start Time':<20}")
        print("-" * 82)
        
        for snap in snapshots.get('snapshots', []):
            indices = ', '.join(snap.get('indices', []))[:18]
            start_time = snap.get('start_time', 'N/A')[:18]
            print(f"{snap['snapshot']:<30} {snap['state']:<12} {indices:<20} {start_time:<20}")
            
    except Exception as e:
        logger.error(f"Error listing snapshots: {e}")
    
    # 4. Restore Demo (optional)
    print("\n[3.4] Restore Capability")
    print("-" * 40)
    print("To restore from a snapshot, use:")
    print(f"  POST _snapshot/{repo_name}/<snapshot_name>/_restore")
    print("  {")
    print(f'    "indices": "{index_name}",')
    print(f'    "rename_pattern": "{index_name}",')
    print(f'    "rename_replacement": "{index_name}_restored"')
    print("  }")
    
    print("\n" + "="*60)
    print("SNAPSHOT/RESTORE DEMO COMPLETE")
    print("="*60)


def run_sample_queries(client: Elasticsearch, index_name: str):
    """
    Run sample search queries.
    
    Args:
        client: Elasticsearch client
        index_name: Name of the index
    """
    print("\n" + "="*60)
    print("SAMPLE QUERIES")
    print("="*60)
    
    # 1. Basic text search
    print("\n[Query 1] Text Search - 'machine learning'")
    print("-" * 40)
    
    try:
        results = client.search(
            index=index_name,
            body={
                "size": 3,
                "query": {
                    "multi_match": {
                        "query": "machine learning",
                        "fields": ["title^2", "abstract"]
                    }
                },
                "_source": ["title", "categories"]
            }
        )
        
        print(f"Found {results['hits']['total']['value']} papers")
        for i, hit in enumerate(results['hits']['hits'], 1):
            print(f"  {i}. {hit['_source']['title'][:60]}...")
            
    except Exception as e:
        logger.error(f"Error in text search: {e}")
    
    # 2. Category filter
    print("\n[Query 2] Filter by Category - 'cs.AI'")
    print("-" * 40)
    
    try:
        results = client.search(
            index=index_name,
            body={
                "size": 3,
                "query": {
                    "term": {
                        "categories": "cs.AI"
                    }
                },
                "_source": ["title", "categories"]
            }
        )
        
        print(f"Found {results['hits']['total']['value']} papers")
        for i, hit in enumerate(results['hits']['hits'], 1):
            print(f"  {i}. {hit['_source']['title'][:60]}...")
            
    except Exception as e:
        logger.error(f"Error in category filter: {e}")
    
    # 3. Aggregation
    print("\n[Query 3] Aggregation - Papers by Category")
    print("-" * 40)
    
    try:
        results = client.search(
            index=index_name,
            body={
                "size": 0,
                "aggs": {
                    "categories": {
                        "terms": {
                            "field": "categories",
                            "size": 10
                        }
                    }
                }
            }
        )
        
        print("Top categories:")
        for bucket in results['aggregations']['categories']['buckets']:
            print(f"  - {bucket['key']}: {bucket['doc_count']} papers")
            
    except Exception as e:
        logger.error(f"Error in aggregation: {e}")


def main():
    """Main function to run demos."""
    index_name = os.getenv('INDEX_NAME', 'arxiv-papers')
    
    print("\n" + "#"*60)
    print("#  DISTRIBUTED SYSTEMS DEMO - arXiv Elasticsearch Project")
    print("#"*60)
    
    # Connect to Elasticsearch
    client = get_elasticsearch_client()
    
    info = client.info()
    print(f"\nConnected to: {info['cluster_name']} (ES {info['version']['number']})")
    
    # Check if index exists
    if not client.indices.exists(index=index_name):
        print(f"\nError: Index '{index_name}' does not exist.")
        print("Please run the data ingestion script first.")
        return
    
    print("\nDemo Menu:")
    print("1. Sharding and Replication Demo")
    print("2. HNSW Vector Search Demo")
    print("3. Snapshot/Restore Demo")
    print("4. Sample Queries")
    print("5. Run All Demos")
    print("6. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            demo_sharding_replication(client, index_name)
        elif choice == '2':
            demo_hnsw_vector_search(client, index_name)
        elif choice == '3':
            demo_snapshot_restore(client, index_name)
        elif choice == '4':
            run_sample_queries(client, index_name)
        elif choice == '5':
            demo_sharding_replication(client, index_name)
            demo_hnsw_vector_search(client, index_name)
            demo_snapshot_restore(client, index_name)
            run_sample_queries(client, index_name)
        elif choice == '6':
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    main()
