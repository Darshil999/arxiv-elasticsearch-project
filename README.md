# arXiv Elasticsearch Project

A distributed systems project demonstrating semantic search for Computer Science papers using Elasticsearch, Kibana, and vector embeddings.

## 🎯 Project Overview

This university course project demonstrates three key distributed system features:

1. **Sharding and Replication** - Data distribution across multiple shards with replicas for fault tolerance
2. **HNSW ANN Vector Indexing** - Semantic search using dense vector embeddings and k-NN search
3. **Snapshot/Restore** - Backup and recovery capabilities

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kibana (Port 5601)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Elasticsearch Cluster (3 Nodes)                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │   es01   │    │   es02   │    │   es03   │               │
│  │ Primary  │    │ Primary  │    │ Primary  │               │
│  │ +Replica │    │ +Replica │    │ +Replica │               │
│  └──────────┘    └──────────┘    └──────────┘               │
│       ↓               ↓               ↓                      │
│  ┌─────────────────────────────────────────┐                │
│  │        Shared Snapshot Storage           │                │
│  └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

## 📁 Project Structure

```
arxiv-elasticsearch-project/
├── docker-compose.yml          # 3-node ES cluster + Kibana
├── .env.example                # Environment configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── config/
│   ├── index_mapping.json      # Elasticsearch index settings
│   ├── elasticsearch.yml       # Custom ES configuration
│   └── kibana_dashboards.ndjson # Kibana export template
├── scripts/
│   ├── download_dataset.py     # Download arXiv dataset
│   ├── generate_embeddings.py  # Generate vector embeddings
│   ├── ingest_data.py          # Bulk index documents
│   ├── setup_snapshots.py      # Snapshot management
│   ├── demo_queries.py         # Demo all features
│   └── run_demo.sh             # Complete demo script
├── data/                       # Dataset storage
├── snapshots/                  # Snapshot storage
└── docs/
    └── architecture.md         # Architecture documentation
```

## 🛠 Prerequisites

- **Docker** and **Docker Compose** (v2.0+)
- **Python 3.8+**
- **8GB RAM minimum** (16GB recommended)
- **10GB free disk space**
- (Optional) Kaggle API credentials for full dataset

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/arxiv-elasticsearch-project.git
cd arxiv-elasticsearch-project

# Copy environment file
cp .env.example .env

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Cluster

```bash
# Start Elasticsearch cluster and Kibana
docker-compose up -d

# Wait for cluster to be ready (about 1-2 minutes)
# Check health:
curl http://localhost:9200/_cluster/health?pretty
```

### 3. Prepare and Ingest Data

```bash
# Download/create dataset
python scripts/download_dataset.py

# Generate embeddings
python scripts/generate_embeddings.py

# Ingest into Elasticsearch
python scripts/ingest_data.py
```

### 4. Run the Demo

```bash
# Run interactive demo
python scripts/demo_queries.py

# Or run the complete bash demo
chmod +x scripts/run_demo.sh
./scripts/run_demo.sh
```

### 5. Access Kibana

Open http://localhost:5601 in your browser.

## 📖 Detailed Setup Instructions

### Environment Variables

Edit `.env` to customize:

```bash
# Elasticsearch hosts
ELASTICSEARCH_HOSTS=http://localhost:9200

# Index name
INDEX_NAME=arxiv-papers

# Embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Processing
BATCH_SIZE=500
MAX_DOCUMENTS=50000
```

### Kaggle Dataset (Optional)

For the full arXiv dataset:

1. Create a Kaggle account at https://www.kaggle.com
2. Go to Account Settings → API → Create New Token
3. Save `kaggle.json` to `~/.kaggle/kaggle.json`
4. Run `python scripts/download_dataset.py`

Without Kaggle credentials, a sample dataset will be generated for testing.

## 🎓 Demonstrating Distributed Features

### Feature 1: Sharding and Replication

**What it demonstrates:** Data is automatically distributed across multiple shards, with replicas ensuring fault tolerance.

**Demo Steps:**

```bash
# 1. Check cluster health
curl http://localhost:9200/_cluster/health?pretty

# 2. View all nodes
curl http://localhost:9200/_cat/nodes?v

# 3. Check shard allocation
curl http://localhost:9200/_cat/shards/arxiv-papers?v

# 4. View index settings
curl http://localhost:9200/arxiv-papers/_settings?pretty
```

**Expected Output:**
- 3 nodes in the cluster
- 3 primary shards distributed across nodes
- 6 replica shards (2 per primary) for fault tolerance
- Green cluster status indicating all shards are allocated

### Feature 2: HNSW Vector Search

**What it demonstrates:** Semantic similarity search using HNSW (Hierarchical Navigable Small World) algorithm for approximate k-NN.

**Demo Steps:**

```bash
# 1. Check vector field mapping
curl http://localhost:9200/arxiv-papers/_mapping?pretty | grep -A10 "abstract_vector"

# 2. Run semantic search (via Python)
python scripts/demo_queries.py
# Select option 2: HNSW Vector Search Demo
```

**Expected Output:**
- Papers are found based on semantic similarity, not just keyword matching
- Similar papers to a query are ranked by vector distance
- HNSW parameters (m=16, ef_construction=100) control search accuracy/speed

### Feature 3: Snapshot/Restore

**What it demonstrates:** Point-in-time backup and recovery of indices.

**Demo Steps:**

```bash
# 1. Register snapshot repository
curl -X PUT "http://localhost:9200/_snapshot/arxiv_backup" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/usr/share/elasticsearch/snapshots"
    }
  }'

# 2. Create a snapshot
curl -X PUT "http://localhost:9200/_snapshot/arxiv_backup/snapshot_1?wait_for_completion=true" \
  -H 'Content-Type: application/json' \
  -d '{"indices": "arxiv-papers"}'

# 3. List snapshots
curl http://localhost:9200/_snapshot/arxiv_backup/_all?pretty

# 4. Run snapshot demo (via Python)
python scripts/demo_queries.py
# Select option 3: Snapshot/Restore Demo
```

**Expected Output:**
- Snapshot repository is registered
- Snapshots are created with full index data
- Snapshots can be listed and restored

## 📊 Kibana Dashboard Setup

### Import Dashboards

1. Open Kibana at http://localhost:5601
2. Go to **Management** → **Stack Management** → **Saved Objects**
3. Click **Import** and select `config/kibana_dashboards.ndjson`
4. Click **Import** to load the dashboards

### Manual Dashboard Creation

1. **Create Index Pattern:**
   - Go to **Management** → **Data Views**
   - Create pattern: `arxiv-papers*`
   - Time field: `update_date`

2. **Discover View:**
   - Go to **Discover**
   - Select the `arxiv-papers*` index pattern
   - Search papers using KQL: `categories: "cs.AI" AND title: "neural"`

3. **Dev Tools:**
   - Go to **Dev Tools**
   - Run queries directly:
   ```json
   GET arxiv-papers/_search
   {
     "query": {
       "match": {
         "abstract": "machine learning"
       }
     }
   }
   ```

## 🔧 Troubleshooting

### Common Issues

**Cluster Status Yellow/Red:**
```bash
# Check unassigned shards
curl http://localhost:9200/_cat/shards?v | grep UNASSIGNED

# Check cluster allocation
curl http://localhost:9200/_cluster/allocation/explain?pretty
```

**Memory Issues:**
```bash
# Increase Docker memory limit
# Edit docker-compose.yml, change ES_JAVA_OPTS

# For local development, reduce heap:
ES_JAVA_OPTS=-Xms512m -Xmx512m
```

**Elasticsearch Not Starting:**
```bash
# Check logs
docker-compose logs es01

# Check vm.max_map_count (Linux)
sudo sysctl -w vm.max_map_count=262144
```

**Vector Search Not Working:**
```bash
# Verify embeddings were generated
ls -la data/cs_papers_with_embeddings.json

# Check vector field exists
curl http://localhost:9200/arxiv-papers/_mapping | python -m json.tool | grep abstract_vector
```

### Reset Everything

```bash
# Stop and remove containers
docker-compose down -v

# Remove data files
rm -rf data/*.json

# Start fresh
docker-compose up -d
```

## 📚 Dataset Information

- **Source:** arXiv.org via Kaggle
- **Content:** Computer Science papers (cs.* categories)
- **Fields:** Title, Abstract, Categories, Authors, Date
- **Sample Size:** Configurable (default: 50,000 papers)
- **Embedding Model:** all-MiniLM-L6-v2 (384 dimensions)

## 👥 Team Information

**Course:** Distributed Systems
**Project:** Semantic Search with Elasticsearch

| Role | Name |
|------|------|
| Developer | [Your Name] |
| Developer | [Team Member] |

## 📄 License

This project is for educational purposes as part of a university course.

## 🔗 References

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Sentence Transformers](https://www.sbert.net/)
- [arXiv Dataset on Kaggle](https://www.kaggle.com/datasets/Cornell-University/arxiv)
