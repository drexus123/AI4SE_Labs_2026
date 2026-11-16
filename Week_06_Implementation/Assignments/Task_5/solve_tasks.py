"""Solve missing repository methods with the Task 2-4 RAG pipeline."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


TASK_DIR = Path(__file__).parent
ASSIGNMENTS_DIR = TASK_DIR.parent
REPOSITORY_DIR = ASSIGNMENTS_DIR / "Task_1" / "AI4SE_Playground"
EMBEDDING_STORE = ASSIGNMENTS_DIR / "Task_3" / "chunk_embeddings.json"
MISSING_CODE = ASSIGNMENTS_DIR / "missing_code.json"
ALLOWED_MODELS = {
    "gpt-6-luna",
    "gpt-5.6-luna",
    "gpt-5.4-nano",
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-4.1-nano",
    "gpt-4o-mini",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def bucket(token: str, dimensions: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dimensions


def vectorize(tokens: list[str], store: dict[str, Any]) -> list[float]:
    dimensions = int(store["dimensions"])
    document_frequency = [int(value) for value in store["document_frequency"]]
    document_count = int(store["source_chunk_count"])
    counts = Counter(bucket(token, dimensions) for token in tokens)
    vector = [0.0] * dimensions
    for index, count in counts.items():
        inverse_frequency = math.log((document_count + 1) / (document_frequency[index] + 1)) + 1.0
        vector[index] = (1.0 + math.log(count)) * inverse_frequency
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def query_vector(query: str, store: dict[str, Any]) -> list[float]:
    return vectorize(tokenize(query), store)


def match_embedding(embedding: list[float], store: dict[str, Any], count: int) -> list[dict[str, Any]]:
    results = []
    for entry in store["embedding_entries"]:
        score = sum(left * right for left, right in zip(embedding, entry["embedding"]))
        results.append({**entry, "score": score})
    results.sort(key=lambda result: (-result["score"], result["chunk_id"]))
    return results[:count]


def load_tasks(path: Path) -> list[dict[str, str]]:
    tasks = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(tasks, list):
        raise ValueError("missing-code input must be a JSON array")
    return tasks


def retrieve_chunks(task_text: str, store: dict[str, Any], count: int = 5) -> list[dict[str, Any]]:
    embedding = query_vector(task_text, store)
    return match_embedding(embedding, store, count)


def build_prompt(task: dict[str, str], matches: list[dict[str, Any]]) -> str:
    context = "\n\n".join(
        f"--- {item['file_path']}:{item['start_line']}-{item['end_line']} ---\n{item['content']}"
        for item in matches
    )
    return f"""You are implementing one missing Python method in an existing repository.
Return only the complete replacement method definition as Python code. Do not use
Markdown fences, explanations, imports, or modify any other method.

Target file: {task['file']}
Target class: {task['class']}
Target method: {task['method']}
Method documentation:
{task['docstring']}

Use the retrieved repository context below to preserve existing APIs, types,
exceptions, and coding style. Implement the smallest correct behavior.

RETRIEVED CONTEXT:
{context}
"""


def call_model(prompt: str, model: str, api_key: str, base_url: str) -> str:
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "You write precise repository code."},
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.HTTPError, json.JSONDecodeError) as error:
        raise RuntimeError(f"model request failed: {error}") from error
    try:
        return str(result["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("model response did not contain choices[0].message.content") from error


def clean_code(response: str) -> str:
    code = response.strip()
    fenced = re.fullmatch(r"```(?:python)?\s*(.*?)\s*```", code, re.IGNORECASE | re.DOTALL)
    return (fenced.group(1) if fenced else code).strip()


def find_method(source: str, class_name: str, method_name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                    return child
    raise ValueError(f"could not locate {class_name}.{method_name}")


def replace_method(source: str, task: dict[str, str], generated: str) -> str:
    target = ast.parse(generated)
    definitions = [node for node in target.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(definitions) != 1 or definitions[0].name != task["method"]:
        raise ValueError("model output must contain exactly the requested method definition")

    original = find_method(source, task["class"], task["method"])
    lines = source.splitlines(keepends=True)
    original_line = lines[original.lineno - 1]
    indentation = original_line[: len(original_line) - len(original_line.lstrip())]
    replacement = "\n".join(indentation + line if line.strip() else line for line in generated.splitlines()) + "\n"
    lines[original.lineno - 1 : original.end_lineno] = [replacement]
    updated = "".join(lines)
    ast.parse(updated)
    return updated


def task_text(task: dict[str, str]) -> str:
    return f"Implement {task['class']}.{task['method']} in {task['file']}.\n{task['docstring']}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=MISSING_CODE)
    parser.add_argument("--store", type=Path, default=EMBEDDING_STORE)
    parser.add_argument("--repository", type=Path, default=REPOSITORY_DIR)
    parser.add_argument("--model", default="gpt-4o-mini", choices=sorted(ALLOWED_MODELS))
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    parser.add_argument("--task-index", type=int, help="Run only the zero-based task at this index")
    parser.add_argument("--dry-run", action="store_true", help="Retrieve context and print prompts without calling the model")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        tasks = load_tasks(args.tasks)
        store = json.loads(args.store.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Unable to load pipeline input: {error}", file=sys.stderr)
        return 1
    if args.task_index is not None:
        if not 0 <= args.task_index < len(tasks):
            print("task-index is outside the task list", file=sys.stderr)
            return 1
        tasks = [tasks[args.task_index]]

    api_key = os.getenv("OPENAI_API_KEY")
    if not args.dry_run and not api_key:
        print("OPENAI_API_KEY is required unless --dry-run is used", file=sys.stderr)
        return 1

    completed = 0
    for task in tasks:
        try:
            matches = retrieve_chunks(task_text(task), store)
            prompt = build_prompt(task, matches)
            if args.dry_run:
                print(f"\n[{task['file']}::{task['class']}.{task['method']}] top matches:")
                for match in matches:
                    print(f"{match['score']:.4f} {match['file_path']}:{match['start_line']}")
                continue

            generated = clean_code(call_model(prompt, args.model, api_key, args.base_url))
            target = (args.repository / task["file"]).resolve()
            repository_root = args.repository.resolve()
            if repository_root not in target.parents:
                raise ValueError("target file is outside the repository")
            source = target.read_text(encoding="utf-8")
            target.write_text(replace_method(source, task, generated), encoding="utf-8")
            completed += 1
            print(f"Implemented {task['class']}.{task['method']} in {task['file']}")
        except (OSError, ValueError, RuntimeError) as error:
            print(f"Failed {task['class']}.{task['method']}: {error}", file=sys.stderr)

    print(f"Tasks selected: {len(tasks)}")
    print(f"Tasks written: {completed}")
    return 0 if args.dry_run or completed == len(tasks) else 1


if __name__ == "__main__":
    raise SystemExit(main())