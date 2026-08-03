# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Xuân Anh
**Mã sinh viên:** 2A202602010
**Nhóm:** A4-1
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai đoạn văn bản có độ tương tự cosine cao, điều đó có nghĩa là các vector biểu diễn (embedding) của chúng gần như cùng hướng trong không gian đa chiều — tức là hai đoạn văn bản đó có nội dung ngữ nghĩa tương đồng, nói về cùng một chủ đề hoặc ý nghĩa gần giống nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Con mèo đang ngồi trên bàn."
- Câu B: "Một chú mèo nằm trên chiếc bàn."
- Tại sao tương đồng: Cả hai câu đều nói về cùng một chủ đề (con mèo ở trên bàn), chỉ khác về cách diễn đạt. Các từ khóa chính (mèo, bàn) giống nhau nên embedding sẽ có hướng tương tự.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Con mèo đang ngồi trên bàn."
- Câu B: "Thị trường chứng khoán tăng mạnh hôm nay."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau (động vật vs tài chính). Các từ vựng và ngữ nghĩa không liên quan nên embedding sẽ có hướng rất khác nhau trong không gian vector.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo **hướng** của vector mà không bị ảnh hưởng bởi **độ dài** (magnitude), trong khi Euclidean distance bị ảnh hưởng bởi cả hai. Trong text embeddings, hai văn bản có cùng ý nghĩa nhưng khác độ dài có thể có magnitude rất khác nhau — cosine similarity vẫn nhận ra chúng tương đồng, còn Euclidean distance sẽ cho khoảng cách lớn (sai lệch).

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Phép tính:*
> Công thức: `ceil((doc_length - overlap) / (chunk_size - overlap))`
> = ceil((10000 - 50) / (500 - 50))
> = ceil(9950 / 450)
> = ceil(22.11)
> = **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với overlap=100: ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = **25 chunks** — tăng thêm 2 chunks so với overlap=50. Overlap lớn hơn giúp các chunk chia sẻ nhiều nội dung hơn ở biên, giảm nguy cơ cắt đứt câu hoặc ý nghĩa giữa hai chunk liền kề, từ đó cải thiện chất lượng truy xuất (retrieval) khi tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex lookbehind `(?<=[.!?])(?:\s+|\n)` để tách câu — pattern này split sau dấu kết câu (`.`, `!`, `?`) khi theo sau bởi khoảng trắng hoặc xuống dòng, đồng thời giữ lại dấu câu trong câu gốc. Sau khi tách, loại bỏ chuỗi rỗng bằng `strip()`, rồi nhóm các câu thành chunk theo `max_sentences_per_chunk` bằng slicing `sentences[i:i+max]` và nối lại bằng `" ".join()`. Edge case xử lý: text rỗng trả về `[]`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy thử split text bằng separator có priority cao nhất trước (`\n\n` → `\n` → `. ` → ` ` → `""`). Sau khi split, gom các phần nhỏ (≤ chunk_size) lại thành chunk lớn hơn; nếu một phần vẫn quá lớn thì đệ quy tiếp với separator tiếp theo. Base case 1: text ≤ chunk_size → trả về luôn. Base case 2: hết separator → cắt cứng theo chunk_size. Nếu separator không tồn tại trong text → bỏ qua, thử separator tiếp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` duyệt từng Document, gọi `_make_record()` để embed nội dung thành vector rồi lưu vào `self._store` (list of dict). Mỗi record chứa `id`, `content`, `embedding`, `metadata`. `search` gọi `_search_records()` trên toàn bộ store — hàm này embed query, tính dot product với từng record, sort giảm dần theo score và trả về top_k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc **trước** bằng metadata (dùng `all()` để check mọi key-value trong filter phải khớp), rồi gọi `_search_records()` trên tập đã lọc. `delete_document` dùng list comprehension giữ lại record có `id != doc_id`, so sánh length trước/sau để xác định có xóa được không, trả True/False tương ứng.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Thực hiện pattern RAG 3 bước: (1) Retrieve — gọi `self.store.search(question, top_k)` lấy top-k chunks liên quan nhất; (2) Augment — ghép các chunks thành context dạng `[1] chunk_1\n\n[2] chunk_2...`, nhúng vào prompt cùng câu hỏi; (3) Generate — gọi `self.llm_fn(prompt)` với prompt có cấu trúc "Context + Question + Answer:" để LLM tạo câu trả lời dựa trên ngữ cảnh.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

```
================ test session starts =================
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
================= 42 passed in 0.13s =================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Con meo dang ngoi tren ban" | "Chu meo nam tren chiec ban" | cao | -0.1129 | Sai |
| 2 | "Python la ngon ngu lap trinh" | "Java la ngon ngu lap trinh" | cao | 0.1495 | Sai |
| 3 | "Troi hom nay dep qua" | "Thi truong chung khoan giam" | thấp | 0.1471 | Đúng |
| 4 | "Toi thich an pho" | "Pho la mon an Viet Nam" | cao | 0.0931 | Sai |
| 5 | "Xe hoi chay bang xang" | "Hoa hong co mau do" | thấp | 0.0217 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là cặp 1: hai câu nói cùng chủ đề (mèo trên bàn) nhưng cosine similarity lại **âm** (-0.1129). Điều này cho thấy mock embedder tạo vector dựa trên hash chứ **không mã hóa ngữ nghĩa** — mỗi chuỗi ký tự khác nhau sẽ cho vector gần như ngẫu nhiên. Để có kết quả phản ánh thực sự ý nghĩa ngữ nghĩa, cần dùng embedder thật (local hoặc OpenAI) thay vì mock.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | (thống nhất với nhóm) | | | | |
| 2 | (thống nhất với nhóm) | | | | |
| 3 | (thống nhất với nhóm) | | | | |
| 4 | (thống nhất với nhóm) | | | | |
| 5 | (thống nhất với nhóm) | | | | |

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
