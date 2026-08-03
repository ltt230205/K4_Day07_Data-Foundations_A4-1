# Báo Cáo Cá Nhân - Lab 7: Embedding & Vector Store

**Họ tên:** Nguyen Quoc Bao  
**Mã sinh viên:** 2A202601726  
**Nhóm:** A4-1
**Ngày:** 03/08/2026

---

## 1. Khởi động - Cá nhân

### Độ tương tự Cosine

**Độ tương tự cosine cao nghĩa là gì?**  
Hai đoạn văn bản có cosine similarity cao thường có hướng vector gần giống nhau trong không gian embedding. Nói đơn giản, chúng đang nói về nội dung hoặc ý định tương tự nhau, dù có thể dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự cao:**

- Câu A: Khách hàng có thể đổi trả sản phẩm trong 7 ngày.
- Câu B: Người mua được trả hàng trong vòng một tuần.
- Lý do: Hai câu cùng nói về quyền đổi/trả hàng và cùng mốc thời gian.

**Ví dụ có độ tương tự thấp:**

- Câu A: Người bán phải cung cấp mô tả sản phẩm chính xác.
- Câu B: Thời tiết hôm nay có mưa lớn.
- Lý do: Hai câu thuộc hai chủ đề hoàn toàn khác nhau.

**Vì sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**  
Cosine similarity tập trung vào hướng của vector, tức là ý nghĩa/ngữ cảnh, thay vì chỉ đo khoảng cách tuyệt đối. Với văn bản, độ dài hoặc cường độ vector có thể thay đổi, nên so sánh theo hướng thường ổn định và phù hợp hơn.

### Bài toán tính toán Chunking

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50:**

Công thức:

```text
ceil((10000 - 50) / (500 - 50))
= ceil(9950 / 450)
= ceil(22.11)
= 23 chunks
```

**Nếu overlap tăng lên 100:**

```text
ceil((10000 - 100) / (500 - 100))
= ceil(9900 / 400)
= ceil(24.75)
= 25 chunks
```

Số chunk tăng vì mỗi bước trượt ngắn hơn. Tăng overlap giúp giữ thêm ngữ cảnh giữa hai chunk liên tiếp, hữu ích khi một ý quan trọng nằm ở ranh giới giữa các chunk.

---

## 2. Hướng tiếp cận của tôi

### Các hàm chunking

**`SentenceChunker.chunk`**  
Tôi dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách câu tại ranh giới sau dấu chấm, chấm hỏi hoặc chấm than. Sau đó nhóm các câu theo `max_sentences_per_chunk`, đồng thời loại bỏ khoảng trắng thừa và xử lý văn bản rỗng bằng cách trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`**  
Thuật toán thử các separator theo thứ tự ưu tiên như đoạn văn, dòng, câu, từ rồi cuối cùng là cắt cứng theo ký tự. Base case là khi đoạn hiện tại đã nhỏ hơn hoặc bằng `chunk_size`; nếu không còn separator phù hợp thì chia theo từng đoạn có độ dài `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`**  
Mỗi `Document` được chuẩn hóa thành record gồm `id`, `content`, `metadata`, `doc_id` và `embedding`. Khi search, truy vấn được embed rồi tính dot product với từng record, sau đó sắp xếp giảm dần theo score và trả về `top_k`.

**`search_with_filter` + `delete_document`**  
`search_with_filter` lọc metadata trước để giảm tập ứng viên, sau đó mới chạy similarity search trên các record còn lại. `delete_document` xóa toàn bộ chunk có `metadata["doc_id"]` hoặc `doc_id` trùng với tài liệu cần xóa và trả về `True` nếu có dữ liệu bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`**  
Agent lấy top-k chunk liên quan từ store, ghép thành phần `Context` trong prompt, rồi truyền prompt đó vào `llm_fn`. Prompt có hướng dẫn chỉ trả lời dựa trên context và nói rõ nếu knowledge base không đủ thông tin.

---

## 3. Hoàn thiện code

Các TODO đã hoàn thành trong folder cá nhân:

- `SentenceChunker`
- `RecursiveChunker`
- `compute_similarity`
- `ChunkingStrategyComparator`
- `EmbeddingStore`
- `KnowledgeBaseAgent`

Folder cá nhân đã tạo:

```text
src/Nguyen_Quoc_Bao-2A202601726/
```

### Kết quả kiểm thử

Theo yêu cầu nộp riêng, tôi không sửa các file template gốc trong `src/`. Code bài cá nhân nằm trong folder `src/Nguyen_Quoc_Bao-2A202601726/`, vì vậy tôi chạy smoke test trực tiếp trong folder cá nhân:

```bash
python -c "from chunking import compute_similarity, SentenceChunker, RecursiveChunker; from models import Document; from embeddings import _mock_embed; from store import EmbeddingStore; from agent import KnowledgeBaseAgent; store=EmbeddingStore(embedding_fn=_mock_embed); store.add_documents([Document('d1','Python language',{'kind':'code'}), Document('d2','Marketing plan',{'kind':'biz'})]); print(len(SentenceChunker(1).chunk('A. B.'))); print(len(RecursiveChunker(chunk_size=5).chunk('hello world'))); print(round(compute_similarity([1,0],[1,0]), 3)); print(store.get_collection_size()); print(len(store.search_with_filter('Python', metadata_filter={'kind':'code'}))); print(KnowledgeBaseAgent(store, lambda prompt: 'ok').answer('What?'))"
```

Kết quả:

```text
2
2
1.0
2
1
ok
```

**Kết luận:** các thành phần chính trong folder cá nhân chạy được: chunking, cosine similarity, store add/search/filter và agent answer.

---

## 4. Dự đoán độ tương tự

Lưu ý: kết quả bên dưới dùng mock embedder mặc định của lab. Mock embedder ổn cho unit test nhưng không phản ánh tốt quan hệ ngữ nghĩa tiếng Việt; để đánh giá retrieval thật nên dùng `EMBEDDING_PROVIDER=local`.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Khách hàng có thể đổi trả sản phẩm trong 7 ngày. | Người mua được trả hàng trong vòng một tuần. | Cao | -0.0245 | Không |
| 2 | Người bán phải cung cấp thông tin sản phẩm chính xác. | Shop cần mô tả sản phẩm trung thực và đầy đủ. | Cao | -0.2176 | Không |
| 3 | Thanh toán bằng thẻ được xử lý qua cổng bảo mật. | Giao hàng nhanh áp dụng cho khu vực nội thành. | Thấp | -0.0638 | Tương đối |
| 4 | Chính sách bảo mật quy định cách lưu dữ liệu khách hàng. | Quyền riêng tư nói về việc thu thập và bảo vệ dữ liệu người dùng. | Cao | -0.1305 | Không |
| 5 | Sản phẩm lỗi được hoàn tiền theo quy định. | Thời tiết hôm nay có mưa lớn. | Thấp | 0.0607 | Không |

**Kết quả bất ngờ nhất:**  
Các cặp có nghĩa gần nhau lại có score thấp hơn một số cặp không liên quan. Điều này cho thấy mock embedder chỉ tạo vector xác định để test kỹ thuật, không nên dùng để kết luận chiến lược chunking hoặc chất lượng truy xuất theo ngữ nghĩa.

---

## 5. Kết quả truy xuất của tôi

Vì nhóm chưa cung cấp 5 câu benchmark chính thức, tôi chạy thử trên corpus khởi động `data/k4_ecommerce` với `SentenceChunker(max_sentences_per_chunk=2)` và mock embedder.

**Số chunk đã nạp:** 5

| # | Câu hỏi | Top-1 Chunk truy xuất được | Score | Liên quan? | Ghi chú |
|---|---|---|---:|---|---|
| 1 | Khách hàng có thể đổi trả sản phẩm trong bao lâu? | Chunk từ `k4-seller-listing` nói về sản phẩm bị hạn chế/cấm đăng bán. | 0.0938 | Không | Mock embedder làm retrieval lệch chủ đề. |
| 2 | Điều kiện để người bán đăng sản phẩm là gì? | Chunk từ `k4-returns-policy` nói về đổi trả hàng. | 0.2404 | Không | Truy vấn seller nhưng top-1 sang returns. |
| 3 | Ai chịu trách nhiệm cung cấp mô tả sản phẩm chính xác? | Chunk từ `k4-seller-listing` chứa phần đăng bán sản phẩm. | 0.0928 | Có | Đúng nhóm tài liệu seller listing. |
| 4 | Chính sách đổi trả áp dụng khi sản phẩm bị lỗi như thế nào? | Chunk từ `k4-returns-policy` nói về yêu cầu đổi trả. | 0.0254 | Có | Đúng nhóm tài liệu returns. |
| 5 | Người bán cần chuẩn bị thông tin gì trước khi niêm yết sản phẩm? | Chunk từ `k4-seller-listing` nói về sản phẩm hạn chế/cấm đăng bán. | -0.0398 | Một phần | Đúng tài liệu nhưng chưa đúng trọng tâm. |

**Bao nhiêu câu hỏi trả về chunk liên quan trong top-1:** 2-3 / 5  
**Nhận xét:** Kết quả đủ để kiểm tra pipeline hoạt động từ ingest đến search, nhưng chưa đủ để đánh giá chất lượng ngữ nghĩa. Khi làm phần nhóm, nên bổ sung corpus 5-10 tài liệu thật và dùng local multilingual embedder để có kết quả đáng tin cậy hơn.

---

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận của tôi | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 4 / 5 |
| Kết quả truy xuất của tôi | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
