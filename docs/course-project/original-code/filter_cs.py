import pandas as pd
import os
from tqdm import tqdm

IN_PATH = 'data/arxiv-metadata-oai-snapshot.json'
OUT_PATH = 'data/arxiv-cs.csv'
CHUNK_SIZE = 50_000                     
MAX_CS_ROWS = None #200_000
REQUIRED_COLS = ["id", "title", "abstract", "categories"]

def main():
    if not os.path.exists(IN_PATH):
        raise FileNotFoundError(f"Could not find {IN_PATH}")

    # Checking the format of the JSON file
    first_char = open(IN_PATH, "r").read(1)
    if first_char == "{":
        ndjson = True
        print("Detected NDJSON (one JSON object per line).")
    elif first_char == "[":
        ndjson = False
        print("Detected JSON array – for huge files this is slower.")
    else:
        raise ValueError("Unknown JSON format; first character is neither '{' nor '['.")

    # Remove old output if it exists
    if os.path.exists(OUT_PATH):
        os.remove(OUT_PATH)

    total = 0
    total_cs = 0
    first_chunk_written = False

    print("Streaming and filtering…")

    # Create an iterator over chunks
    if ndjson:
        chunk_iter = pd.read_json(
            IN_PATH,
            lines=True,
            chunksize=CHUNK_SIZE
        )
    else:
        chunk_iter = pd.read_json(
            IN_PATH,
            chunksize=CHUNK_SIZE
        )
    
    for chunk in tqdm(chunk_iter):
        total += len(chunk)

        # Normalize column names
        chunk = chunk.rename(columns=str.lower)

        # Ensure required columns exist
        missing = [c for c in REQUIRED_COLS if c not in chunk.columns]
        if missing:
            raise ValueError(f"Chunk missing required columns: {missing}")

        # Filter CS: categories containing 'cs.'
        cs_chunk = chunk[chunk["categories"].str.contains(r"\bcs\.", na=False)].copy()

        if len(cs_chunk) == 0:
            continue

        # Keep only needed columns
        cs_chunk = cs_chunk[REQUIRED_COLS]

        # Limit the number of CS rows
        if MAX_CS_ROWS is not None:
            remaining = MAX_CS_ROWS - total_cs
            if remaining <= 0:
                break
            if len(cs_chunk) > remaining:
                cs_chunk = cs_chunk.iloc[:remaining]

        # Append to CSV
        mode = "w" if not first_chunk_written else "a"
        header = not first_chunk_written
        cs_chunk.to_csv(OUT_PATH, mode=mode, header=header, index=False)
        first_chunk_written = True

        total_cs += len(cs_chunk)

        if MAX_CS_ROWS is not None and total_cs >= MAX_CS_ROWS:
            print(f"Reached MAX_CS_ROWS={MAX_CS_ROWS}, stopping early.")
            break
    
    print(f"Total rows seen: {total:,}")
    print(f"Total CS rows saved: {total_cs:,}")
    print(f"CS subset written to: {OUT_PATH}")

if __name__ == "__main__":
    main()