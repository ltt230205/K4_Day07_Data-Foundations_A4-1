# VUXUANANH-2A202602010

Thư mục cá nhân của Vũ Xuân Anh cho Lab 7: Embedding & Vector Store.

Phần code được chấm chính vẫn nằm ở package `src` cấp trên vì bộ test import trực tiếp `src`. Thư mục này lưu ghi chú cá nhân và tóm tắt các phần đã hoàn thành.

## Đã hoàn thành

- `SentenceChunker` : tách câu bằng regex và gom theo số câu tối đa.
- `RecursiveChunker` : chia đệ quy theo separator ưu tiên.
- `compute_similarity` : tính cosine similarity và xử lý zero vector.
- `ChunkingStrategyComparator` : so sánh fixed-size, sentence-based và recursive chunking.
- `EmbeddingStore` : thêm tài liệu, tìm kiếm, lọc metadata, đếm số chunk, xóa theo `doc_id`.
- `KnowledgeBaseAgent` : truy xuất top-k chunk và tạo prompt RAG.

## Kiểm thử

```
py -m pytest tests/ -v
42 passed in 0.05s
```
