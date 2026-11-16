# Chunk Embedding Report

## Method

`embed_chunks.py` creates deterministic 384-dimensional hashed TF-IDF vectors
from each chunk's words, code identifiers, and file path. Vectors are
L2-normalized, so their dot product gives cosine similarity. This approach is
reproducible, fast, offline, and needs no external dependencies.

## Storage and retrieval

`chunk_embeddings.json` stores each chunk's ID, path, line range, content, and
embedding, plus the settings needed to embed queries consistently. The script
supports `--query` and `--top-k`; it ranks all stored vectors by cosine
similarity. A linear scan is sufficient for this small repository.

## Limitations

Hashed TF-IDF is lexical, so synonyms and similar code with different words may
not match well, and hash collisions are possible. A larger or more advanced
system could use a code-aware or transformer embedding model and an indexed
vector database.