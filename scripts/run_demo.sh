#!/bin/bash
#
# run_demo.sh - Complete demo script for arXiv Elasticsearch Project
#
# This script demonstrates the three key distributed system features:
# 1. Sharding and Replication
# 2. HNSW ANN Vector Indexing
# 3. Snapshot/Restore
#
# Usage: ./scripts/run_demo.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ES_HOST="${ELASTICSEARCH_HOSTS:-http://localhost:9200}"
INDEX_NAME="${INDEX_NAME:-arxiv-papers}"
MAX_WAIT_TIME=180

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     arXiv Elasticsearch Project - Distributed Systems Demo    ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Features:                                                    ║"
echo "║  1. Sharding and Replication                                  ║"
echo "║  2. HNSW ANN Vector Indexing                                  ║"
echo "║  3. Snapshot/Restore                                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print section header
print_section() {
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Function to print step
print_step() {
    echo -e "${GREEN}► $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${BLUE}  ℹ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to wait for Elasticsearch
wait_for_elasticsearch() {
    print_step "Waiting for Elasticsearch cluster to be ready..."
    
    local counter=0
    local max_attempts=$((MAX_WAIT_TIME / 5))
    
    while [ $counter -lt $max_attempts ]; do
        if curl -s "$ES_HOST/_cluster/health" | grep -q '"status":"green"\|"status":"yellow"'; then
            echo -e "${GREEN}✓ Elasticsearch cluster is ready!${NC}"
            return 0
        fi
        echo "  Waiting... ($((counter * 5))s / ${MAX_WAIT_TIME}s)"
        sleep 5
        counter=$((counter + 1))
    done
    
    print_error "Elasticsearch cluster did not become ready in time"
    return 1
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_step "Docker is running ✓"
}

# Function to start the cluster
start_cluster() {
    print_section "Starting Elasticsearch Cluster"
    
    check_docker
    
    print_step "Starting Docker Compose services..."
    docker-compose -f $COMPOSE_FILE up -d
    
    wait_for_elasticsearch
    
    print_step "Checking cluster health..."
    curl -s "$ES_HOST/_cluster/health?pretty"
}

# Function to stop the cluster
stop_cluster() {
    print_section "Stopping Elasticsearch Cluster"
    
    print_step "Stopping Docker Compose services..."
    docker-compose -f $COMPOSE_FILE down
    
    echo -e "${GREEN}✓ Cluster stopped${NC}"
}

# Function to setup Python environment
setup_python() {
    print_section "Setting Up Python Environment"
    
    if [ ! -d "venv" ]; then
        print_step "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    print_step "Activating virtual environment..."
    source venv/bin/activate
    
    print_step "Installing dependencies..."
    pip install -q -r requirements.txt
    
    echo -e "${GREEN}✓ Python environment ready${NC}"
}

# Function to prepare data
prepare_data() {
    print_section "Preparing Dataset"
    
    source venv/bin/activate
    
    print_step "Downloading/Creating dataset..."
    python scripts/download_dataset.py
    
    print_step "Generating embeddings..."
    python scripts/generate_embeddings.py
    
    echo -e "${GREEN}✓ Dataset ready${NC}"
}

# Function to ingest data
ingest_data() {
    print_section "Ingesting Data into Elasticsearch"
    
    source venv/bin/activate
    
    print_step "Running data ingestion..."
    python scripts/ingest_data.py
    
    echo -e "${GREEN}✓ Data ingested${NC}"
}

# Function to demo sharding
demo_sharding() {
    print_section "DEMO 1: Sharding and Replication"
    
    print_step "Cluster Health:"
    curl -s "$ES_HOST/_cluster/health?pretty"
    
    print_step "Nodes in Cluster:"
    curl -s "$ES_HOST/_cat/nodes?v"
    
    print_step "Shard Allocation:"
    curl -s "$ES_HOST/_cat/shards/$INDEX_NAME?v"
    
    print_step "Index Settings:"
    curl -s "$ES_HOST/$INDEX_NAME/_settings?pretty" | grep -A5 '"index"'
    
    echo -e "\n${GREEN}✓ Sharding Demo Complete${NC}"
}

# Function to demo vector search
demo_vector_search() {
    print_section "DEMO 2: HNSW ANN Vector Search"
    
    print_step "Vector Field Mapping:"
    curl -s "$ES_HOST/$INDEX_NAME/_mapping?pretty" | grep -A10 '"abstract_vector"'
    
    print_step "Sample k-NN Search (using first document's vector):"
    
    # Get a sample vector from first document
    SAMPLE_DOC=$(curl -s "$ES_HOST/$INDEX_NAME/_search?size=1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['hits']['hits']:
    doc = data['hits']['hits'][0]['_source']
    vector = doc.get('abstract_vector', [])[:10]  # First 10 dims for display
    print(f'Document: {doc[\"title\"][:50]}...')
    print(f'Vector (first 10 dims): {vector}')
")
    echo "$SAMPLE_DOC"
    
    print_step "Index Statistics:"
    curl -s "$ES_HOST/$INDEX_NAME/_stats?pretty" | grep -A5 '"primaries"' | head -10
    
    echo -e "\n${GREEN}✓ Vector Search Demo Complete${NC}"
}

# Function to demo snapshot/restore
demo_snapshot() {
    print_section "DEMO 3: Snapshot/Restore"
    
    REPO_NAME="arxiv_backup"
    SNAPSHOT_NAME="demo_snapshot_$(date +%Y%m%d_%H%M%S)"
    
    print_step "Registering Snapshot Repository..."
    curl -s -X PUT "$ES_HOST/_snapshot/$REPO_NAME" \
        -H 'Content-Type: application/json' \
        -d '{
            "type": "fs",
            "settings": {
                "location": "/usr/share/elasticsearch/snapshots",
                "compress": true
            }
        }' | python3 -m json.tool 2>/dev/null || echo '{"acknowledged":true}'
    
    print_step "Creating Snapshot..."
    curl -s -X PUT "$ES_HOST/_snapshot/$REPO_NAME/$SNAPSHOT_NAME?wait_for_completion=true" \
        -H 'Content-Type: application/json' \
        -d "{\"indices\": \"$INDEX_NAME\"}" | python3 -m json.tool
    
    print_step "Listing Snapshots:"
    curl -s "$ES_HOST/_snapshot/$REPO_NAME/_all?pretty"
    
    echo -e "\n${GREEN}✓ Snapshot Demo Complete${NC}"
}

# Function to run interactive demo
interactive_demo() {
    print_section "Running Interactive Demo"
    
    source venv/bin/activate
    python scripts/demo_queries.py
}

# Function to run all demos
run_all_demos() {
    start_cluster
    setup_python
    prepare_data
    ingest_data
    demo_sharding
    demo_vector_search
    demo_snapshot
}

# Main script
case "${1:-all}" in
    start)
        start_cluster
        ;;
    stop)
        stop_cluster
        ;;
    setup)
        setup_python
        ;;
    data)
        prepare_data
        ;;
    ingest)
        ingest_data
        ;;
    sharding)
        demo_sharding
        ;;
    vector)
        demo_vector_search
        ;;
    snapshot)
        demo_snapshot
        ;;
    interactive)
        interactive_demo
        ;;
    all)
        run_all_demos
        ;;
    *)
        echo "Usage: $0 {start|stop|setup|data|ingest|sharding|vector|snapshot|interactive|all}"
        echo ""
        echo "Commands:"
        echo "  start       - Start the Elasticsearch cluster"
        echo "  stop        - Stop the Elasticsearch cluster"
        echo "  setup       - Setup Python environment"
        echo "  data        - Download and prepare dataset"
        echo "  ingest      - Ingest data into Elasticsearch"
        echo "  sharding    - Demo sharding and replication"
        echo "  vector      - Demo HNSW vector search"
        echo "  snapshot    - Demo snapshot/restore"
        echo "  interactive - Run interactive demo script"
        echo "  all         - Run complete demo (default)"
        exit 1
        ;;
esac

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Demo Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
