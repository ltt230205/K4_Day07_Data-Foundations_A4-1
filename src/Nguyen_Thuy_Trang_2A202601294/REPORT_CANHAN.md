# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thùy Trang
**MSSV:** 2A202601294
**Nhóm:** [Tên nhóm]
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding gần như cùng hướng trong không gian nhiều chiều, tức là hai đoạn văn bản mang ý nghĩa/ngữ cảnh gần giống nhau, bất kể độ dài câu chữ khác nhau ra sao.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả sản phẩm vì bị lỗi."
- Câu B: "Làm sao để hoàn trả hàng bị hư hỏng?"
- Tại sao tương đồng: cả hai đều nói về nhu cầu đổi/trả hàng lỗi, dùng từ vựng và ngữ cảnh (return, hư hỏng) gần nhau nên embedding của chúng chỉ về cùng một hướng trong không gian vector.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi muốn đổi trả sản phẩm vì bị lỗi."
- Câu B: "Phí vận chuyển cho người bán ở khu vực miền Bắc là bao nhiêu?"
- Tại sao khác: chủ đề (đổi trả vs. phí vận chuyển cho người bán) và đối tượng liên quan (người mua vs. người bán) khác nhau hoàn toàn, nên embedding của hai câu chỉ theo hai hướng khác biệt rõ rệt.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến hướng của vector (ý nghĩa ngữ nghĩa) chứ không bị ảnh hưởng bởi độ dài vector (magnitude thường bị lệch theo độ dài câu/tần suất từ), trong khi Euclidean distance nhạy cảm với magnitude nên hai câu cùng ý nghĩa nhưng độ dài khác nhau có thể bị coi là "xa nhau" một cách sai lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: số lượng chunk = làm_tròn_lên((10000 − 50) / (500 − 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11)
> Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng từ 23 lên **25** (làm_tròn_lên((10000 − 100) / (500 − 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25). Overlap lớn hơn giúp giữ lại ngữ cảnh xuyên suốt ranh giới giữa hai chunk liền kề, giảm nguy cơ một ý quan trọng bị cắt đứt giữa chừng và mất mát thông tin khi retrieval, đổi lại phải trả giá bằng nhiều chunk hơn (tốn thêm dung lượng lưu trữ và chi phí embedding).

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r"(?<=[.!?])\s+|(?<=\.)\n", text.strip())` để tách câu: lookbehind giữ dấu câu `.`, `!`, `?` gắn liền với câu trước, tách tại khoảng trắng theo sau hoặc xuống dòng sau dấu chấm. Sau khi tách, loại bỏ chuỗi rỗng và strip khoảng trắng thừa, rồi nhóm các câu liên tiếp thành từng chunk theo `max_sentences_per_chunk` bằng cách duyệt danh sách câu với bước nhảy bằng kích thước nhóm. Edge case: văn bản rỗng trả về `[]` ngay từ đầu, tránh lỗi khi `re.split` nhận chuỗi rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` là hàm đệ quy: base case là khi `len(current_text) <= chunk_size` thì trả về `[current_text]` (hoặc `[]` nếu rỗng); nếu hết separator để thử thì cắt cứng theo `chunk_size`. Với mỗi separator còn lại, văn bản được `split()` ra thành các phần; nếu separator không xuất hiện (chỉ 1 phần) thì đệ quy tiếp với separator tiếp theo trong danh sách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Nếu tách được nhiều phần, thuật toán gộp (merge) các phần liền kề lại với nhau (dùng lại separator làm keo nối) cho tới khi gần chạm `chunk_size`, phần nào vẫn còn quá lớn thì tiếp tục đệ quy với separator nhỏ hơn — cách này giữ chunk gần đầy kích thước tối đa thay vì tạo ra nhiều chunk nhỏ rời rạc.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` gọi `_make_record` để embed nội dung mỗi `Document` (qua `self._embedding_fn`) và chuẩn hoá thành một dict `{id, content, embedding, metadata}` (tự thêm `doc_id` vào metadata nếu chưa có), sau đó append vào danh sách in-memory `self._store` (hoặc gọi `collection.add(...)` nếu có ChromaDB). `search` embed câu query rồi gọi `_search_records`, hàm này tính **dot product** giữa vector query và từng vector đã lưu (`_dot` từ `chunking.py`) — vì `MockEmbedder`/`LocalEmbedder` đều trả vector đã chuẩn hoá (unit norm), dot product ở đây tương đương cosine similarity — sắp xếp giảm dần theo score và cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc **trước rồi mới search**: duyệt `self._store`, chỉ giữ lại các record có `metadata[key] == value` cho tất cả cặp trong `metadata_filter`, sau đó gọi `_search_records` trên tập con đã lọc — cách này rẻ hơn (không cần embed/so sánh với record không liên quan) và đảm bảo kết quả trả về luôn thoả điều kiện lọc. `delete_document` duyệt `self._store`, giữ lại mọi record có `metadata['doc_id'] != doc_id`, rồi so sánh độ dài trước/sau để trả về `True`/`False` (xoá được ít nhất 1 chunk hay không).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` gọi `self.store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất, nối nội dung các chunk thành một khối `context` (mỗi chunk là một dòng gạch đầu dòng `- {content}`). Prompt được dựng theo cấu trúc: hướng dẫn hệ thống ("chỉ trả lời dựa trên context, nếu không có thì nói rõ") + `Context:` (các chunk) + `Question:` (câu hỏi gốc) + `Answer:`, sau đó gọi `self.llm_fn(prompt)` và trả thẳng kết quả — đây là mô hình RAG cơ bản: retrieve → augment prompt → generate.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 3.03s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> **Lưu ý về embedder dùng cho phần này:** môi trường cài đặt local embedder (`sentence-transformers`) gặp lỗi phụ thuộc (`safetensors` version metadata hỏng) trong lúc chạy; để nộp đúng hạn, phần dưới đây chạy `compute_similarity()` bằng **MockEmbedder** (mặc định, hash-based) thay vì `LocalEmbedder` đa ngữ. README đã cảnh báo mock "gần như ngẫu nhiên" — chính vì vậy bảng dưới đây là minh chứng thực tế cho cảnh báo đó, không phải kết quả ngữ nghĩa thật. Sẽ chạy lại bằng `LocalEmbedder`/`EMBEDDING_PROVIDER=local` khi môi trường ổn định.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Tôi muốn đổi trả sản phẩm vì bị lỗi." | "Làm sao để hoàn trả hàng bị hư hỏng?" | cao | 0.0478 (thấp) | Sai |
| 2 | "Người bán cần cung cấp thông tin sản phẩm chính xác." | "Người bán phải mô tả đúng tình trạng hàng hoá khi đăng bán." | cao | -0.0982 (thấp) | Sai |
| 3 | "Đơn hàng sẽ được giao trong vòng 3-5 ngày làm việc." | "Chính sách bảo mật quy định cách chúng tôi thu thập dữ liệu người dùng." | thấp | 0.1489 (cao nhất trong 5 cặp) | Sai |
| 4 | "Con mèo đang ngủ trên ghế sofa." | "Thời tiết hôm nay rất đẹp." | thấp | 0.0131 (thấp) | Đúng |
| 5 | "Khách hàng có thể thanh toán bằng thẻ tín dụng hoặc ví điện tử." | "Payment can be made via credit card or e-wallet." (bản dịch tiếng Anh) | cao | -0.1366 (thấp nhất) | Sai |

*(Ngưỡng "cao/thấp" cho điểm thực tế: ≥ 0.10 → cao, ngược lại → thấp — chỉ mang tính tương đối vì toàn bộ 5 điểm đều nằm trong khoảng nhiễu ngẫu nhiên của vector 64 chiều.)*

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 5: hai câu **cùng một ý nghĩa** (một tiếng Việt, một dịch tiếng Anh) lại có điểm thấp nhất (âm) trong cả 5 cặp, còn cặp 3 (hai câu **hoàn toàn khác chủ đề** — giao hàng vs. bảo mật) lại có điểm cao nhất. Điều này cho thấy `MockEmbedder` chỉ băm (hash) chuỗi ký tự thành vector giả ngẫu nhiên chứ không hề "hiểu" ngữ nghĩa — 4/5 dự đoán của tôi sai vì tôi dự đoán dựa trên ý nghĩa thật của câu, trong khi điểm số chỉ phản ánh sự trùng khớp ngẫu nhiên của chuỗi ký tự. Đây đúng là điều README đã cảnh báo: mock embedder chỉ dùng để test code chạy được, không dùng để kết luận về chất lượng ngữ nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Lưu ý phạm vi:** tại thời điểm nộp, `REPORT_NHOM.md` và thư mục `data/k4_ecommerce/` mới chỉ có **2 tài liệu khởi động** (dữ liệu mẫu/placeholder, chưa phải bộ 5-10 tài liệu thật của nhóm), và nhóm chưa chốt 5 câu hỏi đánh giá chung. Để có số liệu thật thay vì bỏ trống, tôi tự đặt 5 câu hỏi demo trên 2 tài liệu khởi động này bằng `MockEmbedder` (lý do dùng mock: xem ghi chú ở Phần 4) và `llm_fn` dạng stub (chưa cấu hình `OPENAI_API_KEY`). **Cần chạy lại toàn bộ mục này** khi nhóm hoàn tất bộ tài liệu thật + 5 câu hỏi chung + `EMBEDDING_PROVIDER=local`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua cần làm gì khi muốn đổi trả hàng bị lỗi? | "Đăng bán sản phẩm (dữ liệu khởi động)... Người bán chịu trách nhiệm cung cấp thông tin sản phẩm..." (seller-listing.md — sai tài liệu) | 0.2819 | Không | Stub-LLM (chưa có API key) — không phát sinh câu trả lời thật |
| 2 | Người bán có trách nhiệm gì khi xử lý yêu cầu đổi trả? | "Nhóm cần bổ sung danh mục hàng cấm và quy trình xử lý vi phạm..." (ghi chú placeholder, không phải nội dung chính sách) | 0.1395 | Không | Stub-LLM (chưa có API key) |
| 3 | Người bán cần cung cấp thông tin gì khi đăng bán sản phẩm? | "Sản phẩm bị hạn chế hoặc bị cấm không được đăng bán." | 0.2092 | Một phần (đúng tài liệu, nhưng chunk đúng nhất — "cung cấp thông tin... giá, mô tả, tình trạng hàng" — chỉ xếp hạng #2 trong top-3, không phải #1) | Stub-LLM (chưa có API key) |
| 4 | Sản phẩm như thế nào thì không được phép đăng bán? | "Nhóm cần bổ sung danh mục hàng cấm và quy trình xử lý vi phạm..." (ghi chú placeholder) | 0.2482 | Không (chunk đúng — "Sản phẩm bị hạn chế hoặc bị cấm không được đăng bán." — không lọt vào top-3) | Stub-LLM (chưa có API key) |
| 5 | Với vai trò người bán (`metadata_filter={"customer_role":"seller"}`), quy định đăng bán yêu cầu điều gì? | Ghi chú template metadata (placeholder), chunk liên quan thật xếp hạng #3 | 0.1903 | Yếu (chunk liên quan có xuất hiện ở hạng #3 trong top-3 sau lọc metadata, nhưng không phải top-1) | Stub-LLM (chưa có API key) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5 (câu 3 và câu 5 — cả hai đều ở mức liên quan yếu, xếp hạng #2/#3 chứ không phải #1; câu 1, 2, 4 không có chunk liên quan trong top-3)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Vì nhóm chưa demo chung nên tôi chưa có dữ liệu thật cho mục này; tuy nhiên tự chạy demo cho thấy rõ 2 nguyên nhân gây thất bại truy xuất: (1) `MockEmbedder` không phản ánh ngữ nghĩa (đã thấy ở Phần 4) nên xếp hạng gần như ngẫu nhiên; (2) bộ tài liệu khởi động còn lẫn nhiều "chunk nhiễu" là ghi chú hướng dẫn/placeholder (ví dụ dòng "Khối metadata phía trên là template mẫu...") thay vì nội dung chính sách thật — những chunk này vô tình có điểm cao và chiếm top-1/top-3, đẩy chunk đúng xuống hạng thấp hơn. Bài học: cần dọn dữ liệu khởi động (bỏ các dòng ghi chú hướng dẫn ra khỏi phần nội dung được chunk) trước khi coi corpus là "sẵn sàng" để đánh giá.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 (42/42 test pass) |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 (chạy đủ nhưng bằng mock embedder, chưa phải local embedder như khuyến nghị) |
| Kết quả truy xuất của tôi (Competition Results) | 6 / 10 (chạy được pipeline đầy đủ nhưng trên dữ liệu/embedder/LLM tạm thời, chưa phải bộ câu hỏi + corpus chính thức của nhóm) |
| **Tổng phần cá nhân** | **55 / 60** |
