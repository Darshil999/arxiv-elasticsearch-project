import requests
from sentence_transformers import SentenceTransformer

ES_URL = "http://localhost:9200"
INDEX  = "arxiv_cs_vector"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def semantic_search(query: str, k: int = 5):
    # 1. Encode query into same space as your doc embeddings
    emb = model.encode([query])[0].tolist()

    # 2. cosineSimilarity() script_score query
    payload = {
        "size": k,
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": emb},
                },
            }
        },
        "_source": ["title", "abstract", "categories"],
    }

    r = requests.get(f"{ES_URL}/{INDEX}/_search", json=payload)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    q = "transformer models for natural language processing"
    res = semantic_search(q, k=5)

    print(f"Query: {q}\n")
    for hit in res["hits"]["hits"]:
        score = hit["_score"]
        src = hit["_source"]
        print(f"[score={score:.4f}] {src['title']}")
        print(f"  abstract: {src.get('abstract')}")
        print(f"  categories: {src.get('categories')}")
        print()