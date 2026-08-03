# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đỗ Thị Thanh Loan (MSSV 2A202601654)
**Nhóm:** A4 - 1
**Ngày:** 2026-08-03


**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có góc giữa chúng gần 0° (giá trị cosine gần 1), nghĩa là hai đoạn văn bản có hướng biểu diễn ngữ nghĩa gần giống nhau trong không gian embedding — tức chúng "nói về cùng một ý", dù cách diễn đạt/từ ngữ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả sản phẩm bị lỗi."
- Câu B: "Làm sao để hoàn trả hàng hóa không đúng mô tả?"
- Tại sao tương đồng: cả hai đều nói về yêu cầu đổi/trả hàng do sản phẩm có vấn đề — cùng ý định (intent) dù không trùng từ ngữ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách bảo mật thông tin khách hàng."
- Câu B: "Hôm nay trời nắng đẹp, thích hợp đi chơi."
- Tại sao khác: hai câu thuộc hai chủ đề hoàn toàn không liên quan (chính sách dữ liệu vs. thời tiết).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chuẩn hoá theo độ dài vector (chia cho tích 2 norm) nên chỉ quan tâm đến **hướng** của vector — tức nội dung ngữ nghĩa — thay vì độ lớn; trong khi đó Euclidean distance bị ảnh hưởng bởi độ dài văn bản/tần suất từ khiến 2 câu cùng ý nhưng độ dài khác nhau có thể bị coi là "xa nhau" một cách sai lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: `số lượng chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23`
> Đáp án: **23 chunks** (đã kiểm chứng lại bằng cách chạy trực tiếp `FixedSizeChunker(chunk_size=500, overlap=50).chunk("x"*10000)` trong `src/Do_Thi_Thanh_Loan_2A202601654/chunking.py` → kết quả đúng 23 chunk).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> `làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25 chunks` (đã kiểm chứng bằng code, đúng 25). Overlap tăng → mỗi bước trượt (step = chunk_size − overlap) ngắn hơn nên cần nhiều chunk hơn để phủ hết tài liệu. Overlap lớn hơn giúp giữ ngữ cảnh liên tục qua ranh giới chunk (một câu/ý bị cắt ngang ở chunk này vẫn xuất hiện trọn vẹn ở chunk liền kề), giảm rủi ro mất thông tin khi truy xuất đúng lúc thông tin nằm ngay tại điểm cắt.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+|(?<=\.)\n` (lookbehind) để tách câu ngay sau dấu `.`/`!`/`?` theo sau bởi khoảng trắng, hoặc dấu `.` theo sau bởi xuống dòng — giữ nguyên dấu câu ở cuối mỗi câu thay vì làm mất nó như khi dùng `split()` thường. Sau khi tách, loại bỏ phần tử rỗng/thừa khoảng trắng (`strip`), rồi gom từng nhóm `max_sentences_per_chunk` câu liên tiếp thành 1 chunk. Edge case: text rỗng trả về `[]`; nếu tổng số câu không chia hết cho `max_sentences_per_chunk`, chunk cuối cùng chỉ chứa phần câu còn dư (ít hơn).

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` là hàm đệ quy theo danh sách separator ưu tiên `["\n\n", "\n", ". ", " ", ""]`. **Base case:** nếu đoạn hiện tại đã ≤ `chunk_size`, trả nguyên nó làm 1 chunk. Nếu hết separator để thử hoặc separator hiện tại là chuỗi rỗng, cắt cứng theo từng đoạn `chunk_size` ký tự. Nếu separator không xuất hiện trong đoạn, bỏ qua và đệ quy tiếp với separator ưu tiên thấp hơn. Nếu có, tách đoạn thành các "part" theo separator rồi gộp dần (greedy) vào 1 buffer miễn còn ≤ `chunk_size`; khi vượt ngưỡng, chốt buffer thành 1 chunk và nếu bản thân `part` đó vẫn quá dài thì gọi đệ quy `_split` trên `part` đó với danh sách separator còn lại để chia tiếp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `__init__` thử `import chromadb`; nếu có thì tạo `client.get_or_create_collection(...)`, nếu không (môi trường lab không cài ChromaDB) thì rơi về danh sách in-memory `self._store`. `add_documents` duyệt từng `Document`, dùng `_make_record` để nhúng nội dung (`self._embedding_fn(doc.content)`) và chuẩn hoá thành 1 record (id, content, metadata có `doc_id`, embedding), gán thêm 1 id nội bộ duy nhất (kèm bộ đếm `_next_index`) để không bị trùng khi cùng `doc_id` được add nhiều lần. `search` nhúng câu query rồi gọi `_search_records` tính **dot product** giữa vector query và từng vector đã lưu (dùng `_dot`, vì các embedding trong lab đã được chuẩn hoá về vector đơn vị nên dot product ≈ cosine similarity), sắp xếp giảm dần theo score và cắt `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` **lọc trước, tìm sau**: so khớp từng cặp key/value trong `metadata_filter` với metadata của record (phải đúng hết bằng `all(...)`), rồi mới gọi `_search_records` trên tập con đã lọc — giảm không gian tìm kiếm khi filter càng chặt. `delete_document` xây lại `self._store` chỉ giữ các record có `metadata['doc_id'] != doc_id` (loại bỏ mọi chunk cùng `doc_id`), trả về `True` nếu độ dài danh sách giảm sau khi lọc.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `__init__` chỉ lưu tham chiếu `store` và `llm_fn`. `answer` gọi `store.search(question, top_k)` lấy các chunk liên quan nhất, nối nội dung các chunk bằng dòng trống thành khối `context`, rồi dựng prompt gồm 3 phần cố định: hướng dẫn "chỉ trả lời dựa trên context, nếu không có thông tin thì nói rõ", khối `Context:` chứa các chunk, và `Question:` là câu hỏi gốc — cuối cùng gọi `llm_fn(prompt)` và trả về nguyên văn kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

> Chạy với `LAB_SOLUTION_PACKAGE=src.Do_Thi_Thanh_Loan_2A202601654 pytest tests/ -v` (trỏ vào bản code cá nhân — xem lưu ý ở đầu file).

```
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> **Giới hạn môi trường:** máy của tôi không cài được `sentence-transformers` (local embedder) do chính sách bảo mật hệ thống chặn DLL biên dịch (`Application Control policy` chặn `regex`/`torch`). Vì vậy bài này chạy tạm bằng **mock embedder** (`_mock_embed`) — README đã cảnh báo mock cho điểm **gần như ngẫu nhiên**, không phản ánh ngữ nghĩa thật. Kết quả dưới đây minh hoạ đúng điều đó (xem phản ngẫm). Khi có máy không bị chặn, nên chạy lại với `EMBEDDING_PROVIDER=local` để có kết luận ngữ nghĩa đáng tin cậy.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn đổi trả sản phẩm bị lỗi. | Làm sao để hoàn trả hàng hóa không đúng mô tả? | cao (paraphrase cùng ý định) | -0.1598 | Sai |
| 2 | Người bán cần xác nhận đơn hàng trong 24 giờ. | Người mua có thể hủy đơn trong vòng 1 ngày. | trung bình (cùng miền, khác hành động) | 0.0138 | Gần đúng |
| 3 | Chính sách bảo mật thông tin khách hàng. | Hôm nay trời nắng đẹp, thích hợp đi chơi. | thấp (khác chủ đề) | 0.0348 | Đúng (tình cờ) |
| 4 | Vector embedding biểu diễn văn bản dưới dạng số. | Cosine similarity đo góc giữa hai vector. | cao (cùng miền kỹ thuật, khái niệm liên quan) | -0.2018 | Sai |
| 5 | I sat by the river bank. | I deposited money at the bank. | thấp (trùng từ "bank" nhưng khác nghĩa — câu bẫy kiểm tra ngữ nghĩa thật) | -0.1330 | Đúng (tình cờ) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 1: một cặp diễn giải lại (paraphrase) rất rõ ràng về ý định "đổi trả hàng lỗi" lại nhận điểm **âm** (-0.16), còn thấp hơn cả cặp 3 hoàn toàn không liên quan chủ đề (0.035). Điều này khẳng định đúng cảnh báo trong README: `_mock_embed` chỉ băm (hash) chuỗi ký tự thành vector giả ngẫu nhiên, không dựa trên mô hình ngôn ngữ nào — nên **không nắm bắt được ngữ nghĩa thật**, chỉ đủ để kiểm thử tính đúng đắn của code (có sort, có top_k, có dot product...), tuyệt đối không dùng để kết luận chiến lược chunking/embedding nào "tốt hơn" về mặt ngữ nghĩa. Hai trường hợp "Đúng" ở cặp 3, 5 là trùng hợp ngẫu nhiên, không phải vì mock hiểu ngữ nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy đúng **5 câu hỏi đánh giá chính thức của nhóm** (xem `REPORT_NHOM.md` — Mục 3, cùng bộ 5 tài liệu Lazada thật trong `data/k4_ecommerce/`) trên code cá nhân (`src/Do_Thi_Thanh_Loan_2A202601654`), dùng đúng chiến lược được nhóm phân công: **`FixedSizeChunker(chunk_size=300, overlap=0)`** (16 chunk). Dùng `keyword_embedding` xác định (deterministic, theo `scripts/group_benchmark.py` của nhóm — không dùng mock hash ngẫu nhiên) để kết quả lặp lại được. Cách chấm: 2đ nếu gold doc ở top-1, 1đ nếu gold doc nằm trong top-3, 0đ nếu không.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Điểm |
|---|-------|--------------------------------|-------|-----------|---|
| 1 | Người mua cần làm gì khi muốn đổi trả sản phẩm bị lỗi? | (k4-returns-policy) "Người mua có thể tạo yêu cầu đổi trả khi sản phẩm nhận được bị lỗi, hư hỏng..." | 7.00 | Có (đúng gold doc, top-1) | 2/2 |
| 2 | Người bán cần cung cấp thông tin gì trước khi bắt đầu bán hàng? (lọc `customer_role=seller`) | (k4-seller-listing) "Người bán cần đăng ký tài khoản, cung cấp thông tin định danh và tài khoản ngân hàng..." | 12.00 | Có (đúng gold doc, top-1) | 2/2 |
| 3 | Vì sao người mua nên thanh toán trong nền tảng? | (k4-payment-security) "Nền tảng hỗ trợ các giao dịch thanh toán trong hệ thống để người mua có thể..." | 16.00 | Có (đúng gold doc, top-1) | 2/2 |
| 4 | Khi đơn giao chậm hoặc thất lạc, người mua nên cung cấp thông tin gì? | (k4-shipping-support) "...nên liên hệ trung tâm hỗ trợ và cung cấp mã đơn hàng. Mã đơn hàng giúp bộ phận hỗ trợ kiểm tra..." | 12.00 | Có (đúng gold doc, top-1) | 2/2 |
| 5 | Dữ liệu cá nhân được dùng cho những mục đích nào? | (k4-privacy-policy) "...thông tin tài khoản, thông tin giao dịch và nội dung trao đổi với bộ phận hỗ trợ. Dữ liệu cá nhân được sử dụng..." | 12.00 | Có (đúng gold doc, top-1) | 2/2 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 — **Tổng điểm truy xuất: 10/10**

> Kết quả này khớp với dòng "Đỗ Thị Thanh Loan — Fixed-size không overlap — 10/10" trong bảng benchmark của `REPORT_NHOM.md` (chạy độc lập trên code cá nhân, cùng công thức chấm, cùng embedding xác định — không dùng lại số của nhóm).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Từ bảng so sánh chiến lược trong `REPORT_NHOM.md`, cả 5 chiến lược (fixed-size không/có overlap, sentence, recursive, heading/paragraph custom của Vũ Xuân Anh) đều đạt 10/10 vì corpus hiện tại ngắn (5 tài liệu, mỗi tài liệu 1 chủ đề rõ) và câu hỏi bám sát gold answer — nên chưa phân biệt được chiến lược nào thực sự "tốt hơn". Bài học quan trọng nhất là ở **Câu 2**: nếu không dùng `search_with_filter(metadata_filter={"customer_role": "seller"})`, các chunk buyer (thanh toán, đổi trả) có thể lẫn vào do trùng từ ("thông tin", "tài khoản") — nghĩa là lọc metadata trước khi tìm quan trọng không kém việc chọn chiến lược chunking, đặc biệt khi corpus mở rộng và các tài liệu có nhiều từ vựng chung.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 (42/42 pass; **cần copy `src/Do_Thi_Thanh_Loan_2A202601654/` đè lên `src/` trước khi nộp chính thức**) |
| Dự đoán độ tương tự (Similarity Predictions) | 3 / 5 (đúng quy trình + phản ngẫm, nhưng chưa chạy được embedder ngữ nghĩa thật do máy bị chặn cài đặt) |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 (chạy đúng 5 câu hỏi + tài liệu thật của nhóm, khớp với benchmark trong `REPORT_NHOM.md`) |
| **Tổng phần cá nhân (tạm tính)** | **58 / 60** — chỉ còn thiếu do Mục 4 chưa chạy được embedder ngữ nghĩa thật (máy bị chặn cài `sentence-transformers`) |
