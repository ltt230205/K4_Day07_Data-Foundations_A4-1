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

> **Chưa phải kết quả chính thức:** nhóm chưa chốt bộ tài liệu thật và 5 câu hỏi đánh giá chung (`REPORT_NHOM.md` còn để trống, `data/k4_ecommerce/` hiện chỉ là dữ liệu mẫu/placeholder do lab cung cấp, nội dung còn ghi rõ "Nhóm phải bổ sung nguồn chính sách công khai... trước khi viết gold answer"). Bảng dưới là **demo tạm** chạy `EmbeddingStore` + `KnowledgeBaseAgent` cá nhân trên đúng 2 file mẫu này (`returns-policy.md`, `seller-listing.md`, `FixedSizeChunker(chunk_size=300, overlap=30)` → 5 chunk), dùng mock embedder, chỉ để chứng minh pipeline cá nhân chạy được đầu-cuối. **Sẽ chạy lại bảng này với 5 câu hỏi + tài liệu thật của nhóm** và (nếu có thể) embedder ngữ nghĩa thật ngay khi `REPORT_NHOM.md` được hoàn thiện.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua cần làm gì để được đổi trả hàng lỗi? | (seller-listing) "...bao gồm giá, mô tả và tình trạng hàng. Sản phẩm bị hạn chế..." | 0.142 | Không | Agent chỉ echo prompt (llm_fn demo là stub, chưa gọi LLM thật) |
| 2 | Điều kiện để trở thành người bán trên sàn là gì? | (returns-policy) "...bổ sung nguồn chính sách công khai, điều kiện và ngoại lệ..." | 0.162 | Không | (như trên) |
| 3 | Thời hạn phản hồi yêu cầu đổi trả của người bán là bao lâu? | (seller-listing) "...bao gồm giá, mô tả và tình trạng hàng..." | 0.126 | Không | (như trên) |
| 4 | Quy định đăng bán sản phẩm có yêu cầu gì về mô tả? | (returns-policy) "...bổ sung nguồn chính sách công khai..." | 0.148 | Không (chunk đúng chủ đề — seller-listing — chỉ xếp hạng 2) | (như trên) |
| 5 | Người mua có thể khiếu nại ở đâu nếu người bán không phản hồi? | (returns-policy) "Người mua cần gửi yêu cầu đổi trả trong thời hạn nêu trên trang sản phẩm..." | 0.160 | Một phần (đúng chủ đề đổi trả, nhưng không có câu trả lời cụ thể "khiếu nại ở đâu" trong dữ liệu mẫu) | (như trên) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 0-1 / 5 (demo tạm)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Chưa có dữ liệu vì nhóm chưa tổ chức buổi so sánh (chưa chốt tài liệu + câu hỏi đánh giá chung). Từ demo tạm của riêng tôi, bài học rút ra: kết quả truy xuất kém ở đây không phải do lỗi code (42/42 test pass, cơ chế dot-product + sort + top_k hoạt động đúng) mà do 2 yếu tố ngoài code — (1) mock embedder không phản ánh ngữ nghĩa, (2) dữ liệu mẫu quá ít (2 tài liệu, 5 chunk) và nội dung phần lớn là hướng dẫn/template chứ chưa phải chính sách thật — đúng như mục "Tác động của chiến lược dữ liệu" trong README. Điều này sẽ được cập nhật lại sau khi nhóm hoàn thành thu thập dữ liệu thật.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 (42/42 pass; **cần copy `src/Do_Thi_Thanh_Loan_2A202601654/` đè lên `src/` trước khi nộp chính thức**) |
| Dự đoán độ tương tự (Similarity Predictions) | 3 / 5 (đúng quy trình + phản ngẫm, nhưng chưa chạy được embedder ngữ nghĩa thật do máy bị chặn cài đặt) |
| Kết quả truy xuất của tôi (Competition Results) | 3 / 10 (mới là demo tạm trên dữ liệu mẫu; cần chạy lại với 5 câu hỏi + tài liệu thật của nhóm) |
| **Tổng phần cá nhân (tạm tính)** | **51 / 60** — sẽ lên ~58-60 sau khi cập nhật Mục 4 (embedder thật) và Mục 5 (dữ liệu + câu hỏi thật của nhóm) |
