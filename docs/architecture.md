# Architecture Documentation

## System Architecture

This document describes the architecture of the arXiv Elasticsearch Project, a distributed system for semantic search over Computer Science papers.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Interface                                  │
│                           (Kibana Dashboard)                                 │
│                              Port: 5601                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Python Client Scripts                                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌───────────────────┐   │
│  │  download   │  │  generate    │  │  ingest    │  │   demo_queries    │   │
│  │  _dataset   │  │  _embeddings │  │  _data     │  │   setup_snapshots │   │
│  └─────────────┘  └──────────────┘  └────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Elasticsearch Cluster (3 Nodes)                           │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │     Node 1      │  │     Node 2      │  │     Node 3      │              │
│  │    (es01)       │  │    (es02)       │  │    (es03)       │              │
│  │                 │  │                 │  │                 │              │
│  │  Master: Yes    │  │  Master: Yes    │  │  Master: Yes    │              │
│  │  Data: Yes      │  │  Data: Yes      │  │  Data: Yes      │              │
│  │  Port: 9200     │  │  Port: 9201     │  │  Port: 9202     │              │
│  │                 │  │                 │  │                 │              │
│  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │              │
│  │  │ Shard P0  │  │  │  │ Shard P1  │  │  │  │ Shard P2  │  │              │
│  │  │ Shard R1  │  │  │  │ Shard R2  │  │  │  │ Shard R0  │  │              │
│  │  │ Shard R2  │  │  │  │ Shard R0  │  │  │  │ Shard R1  │  │              │
│  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                    │                        │
│           └────────────────────┼────────────────────┘                        │
│                                │                                             │
│                    ┌───────────┴───────────┐                                 │
│                    │   Shared Network      │                                 │
│                    │   (elastic)           │                                 │
│                    └───────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Storage Layer                                     │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   es01_data     │  │   es02_data     │  │   es03_data     │              │
│  │   (Volume)      │  │   (Volume)      │  │   (Volume)      │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                              │
│                    ┌───────────────────────┐                                 │
│                    │   Snapshot Storage    │                                 │
│                    │   (./snapshots)       │                                 │
│                    └───────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Elasticsearch Cluster

The cluster consists of three nodes, all running Elasticsearch 8.11.0:

| Node | Container | Role | HTTP Port | Transport Port |
|------|-----------|------|-----------|----------------|
| es01 | es01 | Master, Data | 9200 | 9300 |
| es02 | es02 | Master, Data | 9201 | 9301 |
| es03 | es03 | Master, Data | 9202 | 9302 |

**Configuration:**
- Memory: 1GB heap per node
- Memory lock enabled for performance
- Security disabled for demo purposes
- Snapshot repository configured at `/usr/share/elasticsearch/snapshots`

### 2. Index Configuration

The `arxiv-papers` index is configured with:

| Setting | Value | Purpose |
|---------|-------|---------|
| Primary Shards | 3 | Data distribution |
| Replica Shards | 2 | Fault tolerance |
| HNSW m | 16 | Graph connectivity |
| HNSW ef_construction | 100 | Index quality |

**Document Schema:**

```json
{
  "paper_id": "keyword",
  "title": "text (analyzed)",
  "abstract": "text (analyzed)",
  "categories": "keyword[]",
  "authors": "text",
  "update_date": "date",
  "abstract_vector": "dense_vector (384 dims)"
}
```

### 3. Vector Search Implementation

The system uses HNSW (Hierarchical Navigable Small World) algorithm for approximate nearest neighbor search:

```
                    Query Processing Flow
                    
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Query      │───▶│   Encoder    │───▶│  384-dim     │
│   Text       │    │   (MiniLM)   │    │   Vector     │
└──────────────┘    └──────────────┘    └──────────────┘
                                               │
                                               ▼
                    ┌──────────────────────────────────────┐
                    │          HNSW Index Search            │
                    │                                       │
                    │    Layer 2:  ○───○───○                │
                    │                  │                    │
                    │    Layer 1:  ○───○───○───○            │
                    │                  │   │                │
                    │    Layer 0:  ○─○─○─○─○─○─○            │
                    │                                       │
                    └──────────────────────────────────────┘
                                               │
                                               ▼
                    ┌──────────────────────────────────────┐
                    │         k Nearest Neighbors           │
                    │  (Semantically Similar Papers)        │
                    └──────────────────────────────────────┘
```

**Model:** all-MiniLM-L6-v2
- Dimensions: 384
- Sequence Length: 256 tokens
- Similarity: Cosine

### 4. Snapshot/Restore Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Snapshot Repository                        │
│                    (Type: fs)                                │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              /usr/share/elasticsearch/snapshots      │    │
│  │                                                      │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │    │
│  │  │ snapshot_1 │  │ snapshot_2 │  │ snapshot_n │     │    │
│  │  │            │  │            │  │            │     │    │
│  │  │ - indices  │  │ - indices  │  │ - indices  │     │    │
│  │  │ - metadata │  │ - metadata │  │ - metadata │     │    │
│  │  │ - shards   │  │ - shards   │  │ - shards   │     │    │
│  │  └────────────┘  └────────────┘  └────────────┘     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Snapshot Features:**
- Full index backup
- Incremental snapshots
- Compressed storage
- Point-in-time recovery

## Data Flow

### Ingestion Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Kaggle    │───▶│   Filter    │───▶│  Embedding  │───▶│    Bulk     │
│   Dataset   │    │   CS Papers │    │  Generation │    │   Index     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                   │                   │
     ▼                   ▼                   ▼                   ▼
  2.5M papers      ~500K CS papers     384-dim vectors    Elasticsearch
```

### Query Pipeline

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  User Query  │───▶│   Encode     │───▶│   k-NN      │
│  (Text)      │    │   (MiniLM)   │    │   Search    │
└──────────────┘    └──────────────┘    └──────────────┘
                                               │
                                               ▼
                    ┌──────────────────────────────────────┐
                    │         Hybrid Ranking                │
                    │   (BM25 Text + Vector Similarity)     │
                    └──────────────────────────────────────┘
                                               │
                                               ▼
                    ┌──────────────────────────────────────┐
                    │         Search Results                │
                    │   (Sorted by Combined Score)          │
                    └──────────────────────────────────────┘
```

## Network Architecture

All services communicate over a dedicated Docker bridge network:

```
Docker Network: elastic (bridge)
│
├── es01 (172.18.0.2)
├── es02 (172.18.0.3)
├── es03 (172.18.0.4)
└── kibana (172.18.0.5)
```

## Fault Tolerance

The system provides fault tolerance through:

1. **Replica Shards**: Each primary shard has 2 replicas distributed across different nodes
2. **Master Election**: Any of the 3 nodes can become master
3. **Automatic Failover**: If a node fails, replicas are promoted to primary
4. **Snapshot Backup**: Point-in-time recovery capability

### Failure Scenarios

| Scenario | Impact | Recovery |
|----------|--------|----------|
| 1 node failure | No data loss | Automatic replica promotion |
| 2 node failure | No data loss | Manual intervention may be needed |
| All nodes failure | Service unavailable | Restore from snapshot |

## Performance Considerations

### Memory Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Each ES Node | 1GB heap | 2GB heap |
| Total RAM | 8GB | 16GB |
| Embedding Generation | 2GB | 4GB |

### Disk Requirements

| Component | Size |
|-----------|------|
| Dataset (raw) | ~2.5GB |
| Dataset (CS filtered) | ~500MB |
| Dataset (with embeddings) | ~1.5GB |
| Elasticsearch indices | ~2GB |
| Snapshots | ~500MB per snapshot |

## Security Notes

**Note:** This demo configuration has security disabled for simplicity. For production:

1. Enable TLS for transport and HTTP
2. Enable authentication
3. Use API keys for scripts
4. Configure proper network isolation
5. Enable audit logging
