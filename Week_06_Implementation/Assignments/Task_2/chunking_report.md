# Repository Chunking Report

## Chunk size

The chunker defaults to 4,000 characters, an approximate 1,000-token window
using a simple four-characters-per-token estimate. This gives a retrieved
result enough room for a useful function, class, or documentation section
without consuming the whole future prompt. Smaller windows improve precision
but can lose local context; larger windows preserve more context while using
more of the model budget and potentially reducing retrieval focus. The value is
configurable with `--chunk-size` for later tokenizer-specific calibration.

## Chunk overlap

The default 600-character overlap is approximately 150 tokens. Repeating the
edge of adjacent chunks keeps definitions, imports, and explanatory sentences
available when a logical unit crosses a window boundary. It is smaller than the
window to limit duplicate context and is configurable with `--overlap`.

## Splitting strategy

The script recursively scans common source-code, configuration, documentation,
and text-data extensions. It skips Git metadata, dependency and virtual
environment directories, generated chunk artifacts, binary-looking files,
oversized files, and unreadable files. Source paths are stored relative to the
input repository and use forward slashes for portability.

At each target window, the splitter prefers a nearby class or function
declaration, then a paragraph boundary, then a line boundary. If no useful
boundary exists, it uses the fixed character limit. This preserves meaningful
code and prose units more often than arbitrary slicing while still guaranteeing
progress for minified or unusual files.

## Storage format

`repository_chunks.json` is a human-readable JSON array that can be loaded by
Python's standard library or a future embedding pipeline. Each object contains
a stable `chunk_id`, original relative `file_path`, zero-based `chunk_index`,
the actual `content`, and one-based `start_line` and `end_line` values. The
script prints processed files, skipped files, total chunks, and average chunk
size after every run.

## Limitations

Character counts only approximate tokens and may be inaccurate for languages
with different tokenization patterns. The declaration matcher is intentionally
lightweight rather than a full parser, and fixed overlap may duplicate too much
or too little for a particular file. A production system could use the target
model tokenizer, syntax-tree-aware splitting, incremental file hashing, richer
binary detection, and hybrid lexical plus semantic retrieval.