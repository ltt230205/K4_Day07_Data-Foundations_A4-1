# Do_Thi_Thanh_Loan_2A202601654

Thư mục cá nhân của Đỗ Thị Thanh Loan (MSSV 2A202601654) cho Lab 7: Embedding & Vector Store.

Phần code cá nhân nằm trong thư mục này, không sửa các file template gốc ở `src/`:

- `chunking.py`: `SentenceChunker`, `RecursiveChunker`, `compute_similarity`, `ChunkingStrategyComparator`.
- `store.py`: `EmbeddingStore` với add, search, filter theo metadata, xóa theo `doc_id` và đếm collection size.
- `agent.py`: `KnowledgeBaseAgent` theo mẫu RAG retrieve -> prompt -> LLM.
- `models.py`, `embeddings.py`: các dependency cần thiết để thư mục này chạy độc lập.
- `REPORT_CANHAN.md`: báo cáo cá nhân (60 điểm).

## Kiểm thử

```bash
LAB_SOLUTION_PACKAGE=src.Do_Thi_Thanh_Loan_2A202601654 pytest tests/ -v
```

```text
42 passed in 0.05s
```
