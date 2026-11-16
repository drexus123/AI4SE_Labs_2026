"""Build and query a deterministic, dependency-free chunk embedding store."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DIMENSIONS = 384
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def bucket(token: str, dimensions: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dimensions


def chunk_tokens(chunk: dict[str, Any]) -> list[str]:
    path_tokens = tokenize(str(chunk.get("file_path", "")).replace("/", " "))
    return tokenize(str(chunk.get("content", ""))) + path_tokens


def vectorize(tokens: list[str], dimensions: int, document_frequency: list[int], document_count: int) -> list[float]:
    counts = Counter(bucket(token, dimensions) for token in tokens)
    vector = [0.0] * dimensions
    for index, count in counts.items():
        inverse_frequency = math.log((document_count + 1) / (document_frequency[index] + 1)) + 1.0
        vector[index] = (1.0 + math.log(count)) * inverse_frequency
    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]
    return vector


def build_store(chunks: list[dict[str, Any]], dimensions: int) -> dict[str, Any]:
    token_lists = [chunk_tokens(chunk) for chunk in chunks]
    document_frequency = [0] * dimensions
    for tokens in token_lists:
        for index in {bucket(token, dimensions) for token in tokens}:
            document_frequency[index] += 1

    entries = []
    for chunk, tokens in zip(chunks, token_lists):
        entry = {
            "chunk_id": chunk["chunk_id"],
            "file_path": chunk["file_path"],
            "chunk_index": chunk["chunk_index"],
            "content": chunk["content"],
            "start_line": chunk.get("start_line"),
            "end_line": chunk.get("end_line"),
            "embedding": vectorize(tokens, dimensions, document_frequency, len(chunks)),
        }
        entries.append(entry)

    return {
        "format": "hashed-tfidf-cosine-v1",
        "dimensions": dimensions,
        "source_chunk_count": len(chunks),
        "embedding_entries": entries,
        "document_frequency": document_frequency,
    }


def query_vector(query: str, store: dict[str, Any]) -> list[float]:
    return vectorize(
        tokenize(query),
        int(store["dimensions"]),
        [int(value) for value in store["document_frequency"]],
        int(store["source_chunk_count"]),
    )


def retrieve(query: str, store: dict[str, Any], top_k: int) -> list[tuple[float, dict[str, Any]]]:
    query_embedding = query_vector(query, store)
    ranked = []
    for entry in store["embedding_entries"]:
        score = sum(left * right for left, right in zip(query_embedding, entry["embedding"]))
        ranked.append((score, entry))
    return sorted(ranked, key=lambda result: (-result[0], result[1]["chunk_id"]))[:top_k]


def parse_args() -> argparse.Namespace:
    task_dir = Path(__file__).parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, default=task_dir.parent / "Task_2" / "repository_chunks.json")
    parser.add_argument("--output", type=Path, default=task_dir / "chunk_embeddings.json")
    parser.add_argument("--dimensions", type=int, default=DIMENSIONS)
    parser.add_argument("--query", help="Optional query to retrieve the most similar chunks")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if args.dimensions <= 0 or args.top_k <= 0:
        parser.error("dimensions and top-k must be positive")
    return args


def main() -> int:
    args = parse_args()
    try:
        chunks = json.loads(args.chunks.read_text(encoding="utf-8"))
        if not isinstance(chunks, list):
            raise ValueError("chunk input must be a JSON array")
        store = build_store(chunks, args.dimensions)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"Unable to build embedding store: {error}", file=sys.stderr)
        return 1

    print(f"Chunks embedded: {store['source_chunk_count']}")
    print(f"Vector dimensions: {store['dimensions']}")
    print(f"Storage: {args.output.resolve()}")
    if args.query:
        print(f"\nTop {args.top_k} results for: {args.query}")
        for score, entry in retrieve(args.query, store, args.top_k):
            print(f"{score:.4f}  {entry['chunk_id']}  {entry['file_path']}:{entry['start_line']}-{entry['end_line']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())