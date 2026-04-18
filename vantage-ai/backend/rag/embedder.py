"""
RAG Embedder — chunks and embeds SEC EDGAR filing text.
Run this script before the hackathon to pre-cache demo company filings.

Usage:
    python -m backend.rag.embedder --ticker CRM
    python -m backend.rag.embedder --ticker HUBS
"""
import os
import json
import argparse
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

EMBEDDING_MODEL = "text-embedding-3-small"  # Cheap, fast, high quality
CHUNK_SIZE = 400    # words per chunk
CHUNK_OVERLAP = 50  # word overlap between chunks


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + CHUNK_SIZE])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Embed chunks using OpenAI text-embedding-3-small."""
    print(f"  Embedding {len(chunks)} chunks...")
    # Batch in groups of 100 to respect API limits
    all_embeddings = []
    for i in range(0, len(chunks), 100):
        batch = chunks[i : i + 100]
        response = client.embeddings.create(
            input=batch,
            model=EMBEDDING_MODEL,
        )
        all_embeddings.extend([e.embedding for e in response.data])
    return all_embeddings


def embed_and_store(ticker: str, filing_text: str, metadata: dict = None):
    """
    Chunk, embed, and store filing text for a company.

    Args:
        ticker: Company ticker symbol e.g. "CRM"
        filing_text: Raw text extracted from the SEC filing
        metadata: Optional dict with filing info (date, type, url)
    """
    print(f"Processing {ticker}...")
    chunks = chunk_text(filing_text)
    print(f"  Created {len(chunks)} chunks from {len(filing_text.split())} words")

    embeddings = embed_chunks(chunks)

    store = {
        "ticker": ticker,
        "metadata": metadata or {},
        "chunks": chunks,
        "embeddings": embeddings,
    }

    cache_path = os.path.join(CACHE_DIR, f"{ticker.upper()}.json")
    with open(cache_path, "w") as f:
        json.dump(store, f)

    print(f"  Saved to {cache_path}")
    return cache_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed SEC filings for a company")
    parser.add_argument("--ticker", required=True, help="Company ticker e.g. CRM")
    parser.add_argument("--file", help="Path to raw filing text file (optional)")
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            text = f.read()
        embed_and_store(args.ticker, text)
    else:
        print(f"No --file provided. Add raw filing text for {args.ticker} and re-run.")
        print("Tip: Use scripts/fetch_edgar.py to download filing text first.")
