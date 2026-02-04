#!/usr/bin/env python3
"""
Generate embeddings for arXiv paper abstracts.

This script loads the filtered CS papers dataset and generates dense vector
embeddings using sentence-transformers for semantic search capabilities.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def load_papers(input_file: str) -> List[Dict[str, Any]]:
    """
    Load papers from JSON file.
    
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


def generate_embeddings(
    papers: List[Dict[str, Any]],
    model_name: str = 'all-MiniLM-L6-v2',
    batch_size: int = 32
) -> List[Dict[str, Any]]:
    """
    Generate embeddings for paper abstracts using sentence-transformers.
    
    Args:
        papers: List of paper dictionaries
        model_name: Name of the sentence-transformer model to use
        batch_size: Number of papers to process in each batch
        
    Returns:
        List of papers with added embedding vectors
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
        raise
    
    logger.info(f"Loading model: {model_name}...")
    model = SentenceTransformer(model_name)
    
    # Get embedding dimension
    embedding_dim = model.get_sentence_embedding_dimension()
    logger.info(f"Embedding dimension: {embedding_dim}")
    
    # Extract abstracts
    abstracts = [paper.get('abstract', '') for paper in papers]
    
    logger.info(f"Generating embeddings for {len(abstracts)} papers...")
    
    # Generate embeddings in batches with progress bar
    all_embeddings = []
    for i in tqdm(range(0, len(abstracts), batch_size), desc="Generating embeddings"):
        batch = abstracts[i:i + batch_size]
        batch_embeddings = model.encode(batch, show_progress_bar=False)
        all_embeddings.extend(batch_embeddings)
    
    # Add embeddings to papers
    logger.info("Adding embeddings to papers...")
    for paper, embedding in zip(papers, all_embeddings):
        # Convert numpy array to list for JSON serialization
        paper['abstract_vector'] = embedding.tolist()
    
    return papers


def save_papers_with_embeddings(papers: List[Dict[str, Any]], output_file: str):
    """
    Save papers with embeddings to JSON file.
    
    Args:
        papers: List of papers with embeddings
        output_file: Path to save the output file
    """
    logger.info(f"Saving papers with embeddings to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f)
    
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    logger.info(f"Saved {len(papers)} papers ({file_size_mb:.2f} MB)")


def main():
    """Main function to generate embeddings."""
    data_dir = os.getenv('DATA_DIR', './data')
    model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    batch_size = int(os.getenv('BATCH_SIZE', '32'))
    
    input_file = os.path.join(data_dir, 'cs_papers.json')
    output_file = os.path.join(data_dir, 'cs_papers_with_embeddings.json')
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.info("Please run download_dataset.py first")
        return
    
    # Check if output already exists
    if os.path.exists(output_file):
        logger.info(f"Embeddings file already exists: {output_file}")
        response = input("Do you want to regenerate embeddings? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Load papers
    papers = load_papers(input_file)
    
    # Generate embeddings
    papers_with_embeddings = generate_embeddings(
        papers,
        model_name=model_name,
        batch_size=batch_size
    )
    
    # Save papers with embeddings
    save_papers_with_embeddings(papers_with_embeddings, output_file)
    
    logger.info("Embedding generation complete!")


if __name__ == '__main__':
    main()
