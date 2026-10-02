import os
import json
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

INPUT_CSV   = "data/arxiv-cs.csv"
OUT_TEXT    = "data/arxiv_text_bulk.ndjson"
OUT_VECTOR  = "data/arxiv_vector_bulk.ndjson"
MODEL_NAME  = "sentence-transformers/all-MiniLM-L6-v2"
MAX_DOCS    = None        # set to None to use all rows
BATCH_SIZE  = 512            # embedding batch size


def load_cs_data(path: str, max_docs: int | None = None) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find {path}")

    print(f"Loading CS subset from {path} ...")
    df = pd.read_csv(path)

    # Normalize column names
    df = df.rename(columns=str.lower)

    # Filtering required columns
    required_cols = ["id", "title", "abstract", "categories"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    # Drop rows with missing title/abstract
    before = len(df)
    df = df.dropna(subset=["title", "abstract"])
    after = len(df)
    print(f"Dropped {before - after} rows with missing title/abstract.")

    # Cap the number of documents
    if max_docs is not None and len(df) > max_docs:
        df = df.head(max_docs)
        print(f"Using first {len(df)} documents (MAX_DOCS={max_docs}).")
    else:
        print(f"Using all {len(df)} documents.")

    return df

def prepare_outputs():
    # Remove old files if they exist
    for path in (OUT_TEXT, OUT_VECTOR):
        if os.path.exists(path):
            os.remove(path)
    os.makedirs(os.path.dirname(OUT_TEXT), exist_ok=True)

def main():
    df = load_cs_data(INPUT_CSV, MAX_DOCS)
    prepare_outputs()

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    # Open files once, append per batch
    f_text = open(OUT_TEXT, "w")
    f_vec  = open(OUT_VECTOR, "w")

    try:
        n = len(df)
        print(f"Generating embeddings & NDJSON for {n} documents...")

        # Iterate in batches over the dataframe
        for start in tqdm(range(0, n, BATCH_SIZE), desc="Batches"):
            end = min(start + BATCH_SIZE, n)
            batch = df.iloc[start:end]

            # Build texts for embedding
            texts = (batch["title"] + ". " + batch["abstract"]).tolist()

            # Compute embeddings for this batch
            embeddings = model.encode(
                texts,
                batch_size=64,          # internal model batch size
                show_progress_bar=False
            )

            # Write bulk lines for each doc in batch
            for (idx, row), emb in zip(batch.iterrows(), embeddings):
                doc_id = str(row["id"])

                text_doc = {
                    "title":      row["title"],
                    "abstract":   row["abstract"],
                    "text":       row["title"] + ". " + row["abstract"],
                    "categories": row["categories"],
                }

                vec_doc = {
                    **text_doc,
                    "embedding": emb.tolist()
                }

                # Text-only index action + source
                f_text.write(json.dumps({
                    "index": {"_index": "arxiv_cs_text", "_id": doc_id}
                }) + "\n")
                f_text.write(json.dumps(text_doc) + "\n")

                # Vector index action + source
                f_vec.write(json.dumps({
                    "index": {"_index": "arxiv_cs_vector", "_id": doc_id}
                }) + "\n")
                f_vec.write(json.dumps(vec_doc) + "\n")

        print(f"\nDone. Wrote:")
        print(f"- Text bulk file:   {OUT_TEXT}")
        print(f"- Vector bulk file: {OUT_VECTOR}")

    finally:
        f_text.close()
        f_vec.close()

if __name__ == "__main__":
    main()