#!/usr/bin/env python3
"""
Download and filter arXiv dataset from Kaggle.

This script downloads the arXiv dataset and filters for Computer Science (cs.*) papers only.
The dataset is saved to the data directory for further processing.

Requirements:
    - Kaggle API credentials configured (~/.kaggle/kaggle.json)
    - kaggle package installed (pip install kaggle)
"""

import os
import json
import logging
from pathlib import Path
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


def download_kaggle_dataset(data_dir: str = "./data") -> str:
    """
    Download the arXiv dataset from Kaggle.
    
    Note: This requires Kaggle API credentials to be set up.
    See: https://www.kaggle.com/docs/api#authentication
    
    Args:
        data_dir: Directory to save the downloaded dataset
        
    Returns:
        Path to the downloaded file
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        logger.info("Authenticating with Kaggle API...")
        api = KaggleApi()
        api.authenticate()
        
        logger.info("Downloading arXiv dataset from Kaggle...")
        api.dataset_download_files(
            'Cornell-University/arxiv',
            path=data_dir,
            unzip=True
        )
        
        logger.info(f"Dataset downloaded to {data_dir}")
        return os.path.join(data_dir, "arxiv-metadata-oai-snapshot.json")
        
    except ImportError:
        logger.error("Kaggle package not installed. Install with: pip install kaggle")
        raise
    except Exception as e:
        logger.error(f"Error downloading dataset: {e}")
        raise


def filter_cs_papers(input_file: str, output_file: str, max_papers: int = None) -> int:
    """
    Filter the arXiv dataset to only include Computer Science papers.
    
    Args:
        input_file: Path to the full arXiv dataset JSON
        output_file: Path to save the filtered dataset
        max_papers: Maximum number of papers to include (None for all)
        
    Returns:
        Number of papers in the filtered dataset
    """
    logger.info(f"Filtering CS papers from {input_file}...")
    
    cs_papers = []
    total_processed = 0
    
    # Read and filter papers line by line (JSON Lines format)
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Processing papers"):
            try:
                paper = json.loads(line)
                total_processed += 1
                
                # Check if any category starts with 'cs.'
                categories = paper.get('categories', '')
                if isinstance(categories, str):
                    categories = categories.split()
                
                if any(cat.startswith('cs.') for cat in categories):
                    # Extract relevant fields
                    cs_paper = {
                        'id': paper.get('id', ''),
                        'title': paper.get('title', '').replace('\n', ' ').strip(),
                        'abstract': paper.get('abstract', '').replace('\n', ' ').strip(),
                        'categories': [cat for cat in categories if cat.startswith('cs.')],
                        'authors': paper.get('authors', ''),
                        'update_date': paper.get('update_date', '')
                    }
                    cs_papers.append(cs_paper)
                    
                    if max_papers and len(cs_papers) >= max_papers:
                        logger.info(f"Reached maximum of {max_papers} papers")
                        break
                        
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing line: {e}")
                continue
    
    # Save filtered papers
    logger.info(f"Saving {len(cs_papers)} CS papers to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cs_papers, f, indent=2)
    
    logger.info(f"Processed {total_processed} total papers, kept {len(cs_papers)} CS papers")
    return len(cs_papers)


def create_sample_dataset(output_file: str, num_samples: int = 100) -> int:
    """
    Create a sample dataset for testing without downloading the full dataset.
    
    Args:
        output_file: Path to save the sample dataset
        num_samples: Number of sample papers to generate
        
    Returns:
        Number of sample papers created
    """
    logger.info(f"Creating sample dataset with {num_samples} papers...")
    
    sample_papers = []
    
    # Sample CS categories
    cs_categories = [
        'cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.NE', 
        'cs.DB', 'cs.DC', 'cs.SE', 'cs.PL', 'cs.CR'
    ]
    
    # Sample topics for generating realistic abstracts
    topics = [
        ("deep learning", "neural networks", "training"),
        ("natural language processing", "transformers", "attention"),
        ("computer vision", "image classification", "convolutional"),
        ("distributed systems", "consensus", "replication"),
        ("database systems", "query optimization", "indexing"),
        ("machine learning", "gradient descent", "optimization"),
        ("reinforcement learning", "policy", "reward"),
        ("graph neural networks", "node embeddings", "aggregation"),
        ("knowledge graphs", "reasoning", "embeddings"),
        ("federated learning", "privacy", "aggregation")
    ]
    
    for i in range(num_samples):
        topic = topics[i % len(topics)]
        category = cs_categories[i % len(cs_categories)]
        
        paper = {
            'id': f'{2000 + i // 100:04d}.{i % 10000:05d}',
            'title': f'Advances in {topic[0].title()}: A Study of {topic[1].title()} and {topic[2].title()}',
            'abstract': f'This paper presents a comprehensive study of {topic[0]} with focus on {topic[1]}. '
                       f'We propose a novel approach using {topic[2]} that achieves state-of-the-art results. '
                       f'Our method is evaluated on multiple benchmark datasets and demonstrates significant '
                       f'improvements over existing baselines. The experimental results show the effectiveness '
                       f'of our approach in various scenarios and highlight the importance of {topic[0]} '
                       f'in modern computer science applications.',
            'categories': [category],
            'authors': f'Author {i % 5 + 1}, Author {(i + 1) % 5 + 1}, Author {(i + 2) % 5 + 1}',
            'update_date': f'2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}'
        }
        sample_papers.append(paper)
    
    # Save sample papers
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_papers, f, indent=2)
    
    logger.info(f"Created sample dataset with {num_samples} papers at {output_file}")
    return num_samples


def main():
    """Main function to download and process the dataset."""
    data_dir = os.getenv('DATA_DIR', './data')
    max_documents = int(os.getenv('MAX_DOCUMENTS', '50000'))
    
    # Create data directory if it doesn't exist
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    output_file = os.path.join(data_dir, 'cs_papers.json')
    
    # Check if dataset already exists
    if os.path.exists(output_file):
        logger.info(f"Dataset already exists at {output_file}")
        with open(output_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        logger.info(f"Dataset contains {len(papers)} papers")
        return
    
    # Try to download from Kaggle
    try:
        arxiv_file = os.path.join(data_dir, 'arxiv-metadata-oai-snapshot.json')
        
        if not os.path.exists(arxiv_file):
            download_kaggle_dataset(data_dir)
        
        filter_cs_papers(arxiv_file, output_file, max_papers=max_documents)
        
    except Exception as e:
        logger.warning(f"Could not download from Kaggle: {e}")
        logger.info("Creating sample dataset for demonstration purposes...")
        create_sample_dataset(output_file, num_samples=min(1000, max_documents))


if __name__ == '__main__':
    main()
