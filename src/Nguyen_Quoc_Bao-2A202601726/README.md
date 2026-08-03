# Nguyen Quoc Bao - 2A202601726

Folder ca nhan cho Lab 7: Embedding & Vector Store.

Phan code ca nhan nam trong folder nay, khong sua cac file template goc o `src/`:

- `chunking.py`: SentenceChunker, RecursiveChunker, compute_similarity, ChunkingStrategyComparator.
- `store.py`: EmbeddingStore voi add, search, filter, delete va dem collection size.
- `agent.py`: KnowledgeBaseAgent theo mau RAG retrieve -> prompt -> LLM.
- `models.py`, `embeddings.py`: cac dependency can thiet de folder ca nhan co the chay doc lap.

Luu y: ten folder co dau gach ngang (`-`) nen khong import truc tiep bang cu phap package Python thong thuong. De test nhanh, chay lenh tu ben trong folder nay hoac them folder nay vao `PYTHONPATH`.
