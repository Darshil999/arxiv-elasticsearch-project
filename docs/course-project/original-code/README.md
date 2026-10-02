# Original course implementation (archived)

This folder preserves the first version of the project, built for **COMP 6231 – Distributed System Design**
(Concordia University, Fall 2025). It is kept for reference only and is **not used by the application**.

| File | What it did | Replaced by |
|---|---|---|
| `docker-compose.elasticsearch.yml` | 3-node Elasticsearch 8.15 cluster (3 shards, 1 replica) + Kibana, with snapshot/restore | `docker-compose.yml` (single Qdrant node) / Qdrant Cloud |
| `filter_cs.py` | Streamed the Kaggle arXiv snapshot and kept all `cs.*` papers (846,757 papers) | `scripts/prepare_data.py` |
| `prepare_data.py` | Embedded title + abstract with all-MiniLM-L6-v2 and wrote Elasticsearch bulk NDJSON | `scripts/seed_database.py` |
| `semantic_search.py` | `script_score` cosine-similarity query against the `arxiv_cs_vector` index | `backend/app/services/search.py` |

The report (`../report.pdf`), slides (`../presentation.pdf`) and notebook (`../readme.ipynb`) describe the
distributed-cluster experiments. See the root `README.md` for why the deployed version moved to Qdrant.
