# Embedding Matching Report

`match_embeddings.py` loads the Task 3 embedding store and compares an input
embedding with every stored chunk using cosine similarity. Because the vectors
are normalized, similarity is a simple dot product. Results are sorted by score
and the requested top `k` chunks are returned with their IDs, paths, line
ranges, and content.

The script accepts either task text with `--query` or a precomputed JSON vector
with `--embedding-file`. Query text uses the same Task 3 TF-IDF hashing method,
so its dimensions and weighting are compatible with the stored vectors. The
default is five matches, configurable with `--top-k`. A linear scan is clear
and sufficient for this small repository; a larger system could use an
approximate nearest-neighbor index.

The lexical embedding may miss semantic matches when different words express
the same idea, and hash collisions are possible. A learned code embedding and
indexed vector database would improve retrieval for larger or more varied
repositories.