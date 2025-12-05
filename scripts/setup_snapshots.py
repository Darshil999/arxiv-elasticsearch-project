#!/usr/bin/env python3
"""
Setup and manage Elasticsearch snapshots.

This script demonstrates the Snapshot/Restore feature of Elasticsearch:
- Register snapshot repository
- Create snapshots
- List snapshots
- Restore from snapshots
"""

import os
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


def register_snapshot_repository(
    client: Elasticsearch,
    repo_name: str,
    repo_path: str
) -> Dict[str, Any]:
    """
    Register a snapshot repository.
    
    Args:
        client: Elasticsearch client
        repo_name: Name of the repository
        repo_path: Path to the repository (must be configured in elasticsearch.yml)
        
    Returns:
        Response from Elasticsearch
    """
    logger.info(f"Registering snapshot repository '{repo_name}'...")
    
    response = client.snapshot.create_repository(
        name=repo_name,
        body={
            "type": "fs",
            "settings": {
                "location": repo_path,
                "compress": True
            }
        }
    )
    
    logger.info(f"Repository '{repo_name}' registered successfully")
    return response


def create_snapshot(
    client: Elasticsearch,
    repo_name: str,
    snapshot_name: str = None,
    indices: List[str] = None,
    wait_for_completion: bool = True
) -> Dict[str, Any]:
    """
    Create a snapshot of indices.
    
    Args:
        client: Elasticsearch client
        repo_name: Name of the repository
        snapshot_name: Name for the snapshot (auto-generated if not provided)
        indices: List of indices to snapshot (all if not provided)
        wait_for_completion: Whether to wait for snapshot completion
        
    Returns:
        Snapshot response
    """
    if snapshot_name is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_name = f"snapshot_{timestamp}"
    
    logger.info(f"Creating snapshot '{snapshot_name}' in repository '{repo_name}'...")
    
    body = {}
    if indices:
        body["indices"] = ",".join(indices)
    
    response = client.snapshot.create(
        repository=repo_name,
        snapshot=snapshot_name,
        body=body,
        wait_for_completion=wait_for_completion
    )
    
    if wait_for_completion:
        logger.info(f"Snapshot '{snapshot_name}' created successfully")
        logger.info(f"  - State: {response['snapshot']['state']}")
        logger.info(f"  - Indices: {response['snapshot']['indices']}")
        logger.info(f"  - Shards: {response['snapshot']['shards']}")
    else:
        logger.info(f"Snapshot '{snapshot_name}' creation started")
    
    return response


def list_snapshots(client: Elasticsearch, repo_name: str) -> List[Dict[str, Any]]:
    """
    List all snapshots in a repository.
    
    Args:
        client: Elasticsearch client
        repo_name: Name of the repository
        
    Returns:
        List of snapshot information
    """
    logger.info(f"Listing snapshots in repository '{repo_name}'...")
    
    response = client.snapshot.get(repository=repo_name, snapshot='*')
    snapshots = response.get('snapshots', [])
    
    logger.info(f"Found {len(snapshots)} snapshot(s)")
    
    for snapshot in snapshots:
        logger.info(f"  - {snapshot['snapshot']}")
        logger.info(f"    State: {snapshot['state']}")
        logger.info(f"    Start time: {snapshot.get('start_time', 'N/A')}")
        logger.info(f"    End time: {snapshot.get('end_time', 'N/A')}")
        logger.info(f"    Indices: {snapshot.get('indices', [])}")
    
    return snapshots


def get_snapshot_status(
    client: Elasticsearch,
    repo_name: str,
    snapshot_name: str
) -> Dict[str, Any]:
    """
    Get the status of a specific snapshot.
    
    Args:
        client: Elasticsearch client
        repo_name: Name of the repository
        snapshot_name: Name of the snapshot
        
    Returns:
        Snapshot status
    """
    logger.info(f"Getting status of snapshot '{snapshot_name}'...")
    
    response = client.snapshot.status(repository=repo_name, snapshot=snapshot_name)
    
    return response


def delete_snapshot(
    client: Elasticsearch,
    repo_name: str,
    snapshot_name: str
) -> Dict[str, Any]:
    """
    Delete a snapshot.
    
    Args:
        client: Elasticsearch client
        repo_name: Name of the repository
        snapshot_name: Name of the snapshot to delete
        
    Returns:
        Response from Elasticsearch
    """
    logger.info(f"Deleting snapshot '{snapshot_name}'...")
    
    response = client.snapshot.delete(repository=repo_name, snapshot=snapshot_name)
    
    logger.info(f"Snapshot '{snapshot_name}' deleted successfully")
    return response


def restore_snapshot(
    client: Elasticsearch,
    repo_name: str,
    snapshot_name: str,
    indices: List[str] = None,
    rename_pattern: str = None,
    rename_replacement: str = None,
    wait_for_completion: bool = True
) -> Dict[str, Any]:
    """
    Restore indices from a snapshot.
    
    Args:
        client: Elasticsearch client
        repo_name: Name of the repository
        snapshot_name: Name of the snapshot
        indices: List of indices to restore (all if not provided)
        rename_pattern: Regex pattern for renaming indices
        rename_replacement: Replacement string for renaming
        wait_for_completion: Whether to wait for restore completion
        
    Returns:
        Restore response
    """
    logger.info(f"Restoring snapshot '{snapshot_name}'...")
    
    body = {}
    if indices:
        body["indices"] = ",".join(indices)
    if rename_pattern and rename_replacement:
        body["rename_pattern"] = rename_pattern
        body["rename_replacement"] = rename_replacement
    
    response = client.snapshot.restore(
        repository=repo_name,
        snapshot=snapshot_name,
        body=body,
        wait_for_completion=wait_for_completion
    )
    
    if wait_for_completion:
        logger.info(f"Snapshot '{snapshot_name}' restored successfully")
    else:
        logger.info(f"Snapshot '{snapshot_name}' restore started")
    
    return response


def demo_snapshot_restore(client: Elasticsearch, index_name: str):
    """
    Demonstrate the snapshot/restore workflow.
    
    Args:
        client: Elasticsearch client
        index_name: Name of the index to backup
    """
    repo_name = os.getenv('SNAPSHOT_REPO_NAME', 'arxiv_backup')
    repo_path = os.getenv('SNAPSHOT_REPO_PATH', '/usr/share/elasticsearch/snapshots')
    
    print("\n" + "="*60)
    print("SNAPSHOT/RESTORE DEMO")
    print("="*60)
    
    # Step 1: Register repository
    print("\n[Step 1] Register snapshot repository")
    print("-" * 40)
    try:
        register_snapshot_repository(client, repo_name, repo_path)
    except Exception as e:
        if 'repository_already_exists' in str(e).lower():
            logger.info(f"Repository '{repo_name}' already exists")
        else:
            raise
    
    # Step 2: Create snapshot
    print("\n[Step 2] Create snapshot")
    print("-" * 40)
    snapshot_name = f"demo_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        create_snapshot(client, repo_name, snapshot_name, indices=[index_name])
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
    
    # Step 3: List snapshots
    print("\n[Step 3] List snapshots")
    print("-" * 40)
    try:
        list_snapshots(client, repo_name)
    except Exception as e:
        logger.error(f"Error listing snapshots: {e}")
    
    print("\n" + "="*60)
    print("SNAPSHOT/RESTORE DEMO COMPLETE")
    print("="*60)


def main():
    """Main function to setup and demo snapshots."""
    repo_name = os.getenv('SNAPSHOT_REPO_NAME', 'arxiv_backup')
    repo_path = os.getenv('SNAPSHOT_REPO_PATH', '/usr/share/elasticsearch/snapshots')
    index_name = os.getenv('INDEX_NAME', 'arxiv-papers')
    
    # Connect to Elasticsearch
    client = get_elasticsearch_client()
    
    print("\nSnapshot Management Menu:")
    print("1. Register snapshot repository")
    print("2. Create snapshot")
    print("3. List snapshots")
    print("4. Restore snapshot (demo)")
    print("5. Run full demo")
    print("6. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            register_snapshot_repository(client, repo_name, repo_path)
        elif choice == '2':
            name = input("Enter snapshot name (or press Enter for auto): ").strip()
            create_snapshot(client, repo_name, name if name else None, indices=[index_name])
        elif choice == '3':
            list_snapshots(client, repo_name)
        elif choice == '4':
            snapshots = list_snapshots(client, repo_name)
            if snapshots:
                name = input("Enter snapshot name to restore: ").strip()
                if name:
                    # Restore to a new index with different name
                    restore_snapshot(
                        client, repo_name, name,
                        indices=[index_name],
                        rename_pattern=index_name,
                        rename_replacement=f"{index_name}_restored"
                    )
        elif choice == '5':
            demo_snapshot_restore(client, index_name)
        elif choice == '6':
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    main()
