"""Chunk a repository's text files into a JSON corpus for later retrieval."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


CHUNK_SIZE = 4_000
OVERLAP = 600
MAX_FILE_SIZE = 1_000_000
SKIP_DIRECTORIES = {".git", "__pycache__", "node_modules", "venv", ".venv", "env"}
GENERATED_NAMES = {"repository_chunks.json", "chunk_repository.py", "chunking_report.md"}
TEXT_EXTENSIONS = {
    ".c", ".cc", ".cfg", ".conf", ".cpp", ".cs", ".css", ".csv", ".go", ".h",
    ".hpp", ".html", ".ini", ".java", ".js", ".jsx", ".json", ".md", ".php",
    ".ps1", ".py", ".rb", ".rs", ".rst", ".scss", ".sh", ".sql", ".toml",
    ".ts", ".tsx", ".txt", ".xml", ".yaml", ".yml",
}
SPECIAL_NAMES = {"Dockerfile", "Makefile", ".gitignore", ".gitattributes"}
DECLARATION = re.compile(
    r"(?m)^[ \t]*(?:async[ \t]+)?(?:def|class)\b"
    r"|^[ \t]*(?:export[ \t]+)?(?:default[ \t]+)?(?:async[ \t]+)?function\b"
    r"|^[ \t]*(?:(?:public|private|protected|static|abstract)[ \t]+)*(?:class|interface|enum)\b"
)


def supported(path: Path) -> bool:
    return path.name in SPECIAL_NAMES or path.suffix.lower() in TEXT_EXTENSIONS


def boundary(pattern: re.Pattern[str], text: str, start: int, limit: int) -> list[int]:
    return [match.start() for match in pattern.finditer(text, start, limit) if match.start() > start]


def split_text(text: str, size: int, overlap: int) -> list[tuple[str, int, int]]:
    chunks: list[tuple[str, int, int]] = []
    start = 0
    while start < len(text):
        target = min(start + size, len(text))
        end = target
        if target < len(text):
            search_start = start + max(size // 2, 1)
            candidates = boundary(DECLARATION, text, search_start, target + 1)
            if not candidates:
                candidates = boundary(re.compile(r"\n[ \t]*\n+"), text, search_start, target + 1)
            if not candidates:
                candidates = boundary(re.compile(r"\n"), text, search_start, target + 1)
            if candidates:
                end = max(candidates)

        raw = text[start:end]
        content = raw.strip()
        if content:
            content_start = start + len(raw) - len(raw.lstrip())
            content_end = content_start + len(content)
            chunks.append(
                (
                    content,
                    text.count("\n", 0, content_start) + 1,
                    text.count("\n", 0, content_end - 1) + 1,
                )
            )
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def default_root() -> Path:
    cloned_repository = Path(__file__).parent.parent / "Task_1" / "AI4SE_Playground"
    return cloned_repository if cloned_repository.is_dir() else Path(__file__).parent


def create_chunks(root: Path, output: Path, size: int, overlap: int, max_file_size: int) -> tuple[list[dict[str, object]], int, int, list[str]]:
    chunks: list[dict[str, object]] = []
    processed = 0
    skipped = 0
    errors: list[str] = []
    output = output.resolve()

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRECTORIES for part in relative.parts[:-1]):
            skipped += 1
            continue
        if path.name in GENERATED_NAMES or path.resolve() == output or not supported(path):
            skipped += 1
            continue
        try:
            if path.stat().st_size > max_file_size:
                raise ValueError(f"file exceeds {max_file_size} bytes")
            raw = path.read_bytes()
            if b"\x00" in raw:
                raise ValueError("binary content detected")
            text = raw.decode("utf-8")
            pieces = split_text(text, size, overlap)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            skipped += 1
            errors.append(f"{relative.as_posix()}: {error}")
            continue
        if not pieces:
            skipped += 1
            continue

        relative_path = relative.as_posix()
        prefix = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:10]
        for index, (content, start_line, end_line) in enumerate(pieces):
            chunks.append(
                {
                    "chunk_id": f"{prefix}-{index:04d}",
                    "file_path": relative_path,
                    "chunk_index": index,
                    "content": content,
                    "start_line": start_line,
                    "end_line": end_line,
                }
            )
        processed += 1
    return chunks, processed, skipped, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_root(), help="Repository to scan")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "repository_chunks.json")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="Window size in characters")
    parser.add_argument("--overlap", type=int, default=OVERLAP, help="Overlap in characters")
    parser.add_argument("--max-file-size", type=int, default=MAX_FILE_SIZE, help="Maximum input size in bytes")
    args = parser.parse_args()
    if args.chunk_size <= 0 or not 0 <= args.overlap < args.chunk_size or args.max_file_size <= 0:
        parser.error("require chunk-size > 0, 0 <= overlap < chunk-size, and max-file-size > 0")
    return args


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"Repository does not exist: {root}", file=sys.stderr)
        return 1
    chunks, processed, skipped, errors = create_chunks(
        root, args.output, args.chunk_size, args.overlap, args.max_file_size
    )
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(chunks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    average = sum(len(str(item["content"])) for item in chunks) / len(chunks) if chunks else 0
    print(f"Files processed: {processed}")
    print(f"Files skipped: {skipped}")
    print(f"Chunks generated: {len(chunks)}")
    print(f"Average chunk size: {average:.1f} characters")
    print(f"Output: {output}")
    for error in errors:
        print(f"Warning: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())