"""Retrieve the most relevant repository chunks for an input embedding."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

TASK_3_DIR = Path(__file__).parent.parent / "Task_3"
sys.path.insert(0, str(TASK_3_DIR))

from embed_chunks import query_vector  # noqa: E402


def normalized(values: list[float], dimensions: int) -> list[float]:
    if len(values) != dimensions:
        raise ValueError(f"expected {dimensions} values, received {len(values)}")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("embedding contains a non-finite value")
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        raise ValueError("embedding cannot be the zero vector")
    return [value / norm for value in values]


def load_input_embedding(path: Path, dimensions: int) -> list[float]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("embedding")
    if not isinstance(value, list):
        raise ValueError("embedding file must contain a JSON array or an object with an embedding field")
    try:
        values = [float(item) for item in value]
    except (TypeError, ValueError) as error:
        raise ValueError("embedding values must be numeric") from error
    return normalized(values, dimensions)


def match_embedding(embedding: list[float], store: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
    dimensions = int(store["dimensions"])
    embedding = normalized(embedding, dimensions)
    results = []
    for entry in store["embedding_entries"]:
        score = sum(left * right for left, right in zip(embedding, entry["embedding"]))
        results.append(
            {
                "score": score,
                "chunk_id": entry["chunk_id"],
                "file_path": entry["file_path"],
                "chunk_index": entry["chunk_index"],
                "start_line": entry["start_line"],
                "end_line": entry["end_line"],
                "content": entry["content"],
            }
        )
    results.sort(key=lambda result: (-result["score"], result["chunk_id"]))
    return results[: min(top_k, len(results))]


def parse_args() -> argparse.Namespace:
    task_dir = Path(__file__).parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=task_dir.parent / "Task_3" / "chunk_embeddings.json")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--query", help="Task text to embed using the Task 3 embedding method")
    inputs.add_argument("--embedding-file", type=Path, help="JSON array or object containing a query embedding")
    parser.add_argument("--top-k", type=int, default=5, help="Number of relevant chunks to return")
    args = parser.parse_args()
    if args.top_k <= 0:
        parser.error("top-k must be positive")
    return args


def main() -> int:
    args = parse_args()
    try:
        store = json.loads(args.store.read_text(encoding="utf-8"))
        dimensions = int(store["dimensions"])
        if args.query is not None:
            embedding = query_vector(args.query, store)
        else:
            embedding = load_input_embedding(args.embedding_file, dimensions)
        results = match_embedding(embedding, store, args.top_k)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"Unable to retrieve chunks: {error}", file=sys.stderr)
        return 1

    print(f"Matches returned: {len(results)}")
    for rank, result in enumerate(results, start=1):
        location = f"{result['file_path']}:{result['start_line']}-{result['end_line']}"
        print(f"{rank}. {result['score']:.4f}  {result['chunk_id']}  {location}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())