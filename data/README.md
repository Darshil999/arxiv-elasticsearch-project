# data/

| Path | In Git? | Contents |
|---|---|---|
| `sample/papers.jsonl` | yes | ~1,400 recent CS papers (8 categories), for trying the app immediately |
| `papers.jsonl` | no | Your full demo dataset, created by `scripts/fetch_arxiv.py` or `scripts/prepare_data.py` |
| `arxiv-metadata-oai-snapshot.json` | no | Optional Kaggle snapshot (~4.5 GB) used by `scripts/prepare_data.py` |

`scripts/seed_database.py` indexes `papers.jsonl` if it exists, otherwise `sample/papers.jsonl`.

Each line is one paper:

```json
{"arxiv_id": "2401.01234", "title": "...", "abstract": "...", "authors": ["..."],
 "categories": ["cs.LG", "stat.ML"], "primary_category": "cs.LG",
 "published": "2024-01-02", "updated": "2024-02-10",
 "url": "https://arxiv.org/abs/2401.01234", "pdf_url": "https://arxiv.org/pdf/2401.01234"}
```
