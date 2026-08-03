# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Trí Tùng 
**Mã sinh viên:** 2A202601458  
**Nhóm:** A4-1
**Ngày:** 2026-08-03

---

## 1. Khởi động (Warm-up)

**Độ tương tự cosine cao nghĩa là gì?**  
Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau, tức hai đoạn văn bản có ý nghĩa hoặc chủ đề gần nhau. Điểm càng gần 1 thì nội dung càng tương đồng về mặt ngữ nghĩa.

**Ví dụ có độ tương tự cao:**
- Câu A: Khách hàng có thể đổi trả sản phẩm trong vòng 7 ngày.
- Câu B: Người mua được trả hàng trong 7 ngày nếu sản phẩm có lỗi.
- Lý do: Hai câu đều nói về quyền đổi/trả hàng của khách hàng trong cùng khoảng thời gian.

**Ví dụ có độ tương tự thấp:**
- Câu A: Người bán cần xác minh danh tính trước khi mở gian hàng.
- Câu B: Thời tiết hôm nay có mưa lớn vào buổi chiều.
- Lý do: Hai câu thuộc hai chủ đề khác nhau.

**Tại sao dùng cosine similarity thay vì Euclidean distance?**  
Cosine similarity tập trung vào hướng của vector nên phù hợp để so sánh ý nghĩa văn bản. Euclidean distance dễ bị ảnh hưởng bởi độ lớn vector, trong khi với text embeddings ta quan tâm nhiều hơn đến hướng ngữ nghĩa.

**Bài toán chunking:**  

```text
chunk_size = 500
overlap = 50
số chunk = ceil((10000 - 50) / (500 - 50))
         = ceil(9950 / 450)
         = 23 chunks
```

Nếu `overlap = 100`:

```text
số chunk = ceil((10000 - 100) / (500 - 100))
         = ceil(9900 / 400)
         = 25 chunks
```

Overlap tăng làm số chunk tăng vì bước nhảy nhỏ hơn. Đổi lại, chunk giữ được nhiều ngữ cảnh ở ranh giới hơn.

---

## 2. Hướng tiếp cận của tôi

**`SentenceChunker.chunk`:**  
Tôi dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách câu sau dấu `.`, `!`, `?`, sau đó gom các câu theo `max_sentences_per_chunk`. Các chunk được strip khoảng trắng trước khi trả về.

**`RecursiveChunker.chunk` / `_split`:**  
Tôi chia văn bản theo thứ tự separator ưu tiên: đoạn văn, dòng, câu, từ, rồi ký tự. Nếu đoạn nhỏ hơn `chunk_size` thì giữ nguyên; nếu quá dài thì tiếp tục chia bằng separator kế tiếp.

**`compute_similarity`:**  
Tôi tính cosine similarity bằng công thức `dot(a, b) / (norm(a) * norm(b))`. Nếu một trong hai vector có norm bằng 0 thì trả về `0.0` để tránh lỗi chia cho 0.

**`EmbeddingStore`:**  
Mỗi document được lưu thành record gồm `id`, `content`, `metadata`, và `embedding`. Khi search, tôi embed query, tính dot product với từng document, sắp xếp giảm dần theo score và lấy top-k.

**`search_with_filter` và `delete_document`:**  
`search_with_filter` lọc metadata trước rồi mới search trên tập đã lọc. `delete_document` xóa mọi chunk có `metadata["doc_id"]` trùng với document cần xóa.

**`KnowledgeBaseAgent.answer`:**  
Agent lấy top-k chunk liên quan từ store, ghép thành context, tạo prompt RAG và gọi `llm_fn` để sinh câu trả lời.

---

## 3. Hoàn thiện code

Code cá nhân nằm trong thư mục:

```text
src/Le_Tri_Tung-2A202601458/
```

Các file chính:

```text
chunking.py
store.py
agent.py
models.py
embeddings.py
__init__.py
```

Đã kiểm tra cú pháp:

```text
py -m py_compile src\Le_Tri_Tung-2A202601458\chunking.py src\Le_Tri_Tung-2A202601458\store.py src\Le_Tri_Tung-2A202601458\agent.py src\Le_Tri_Tung-2A202601458\models.py src\Le_Tri_Tung-2A202601458\embeddings.py
```

Đã chạy test bằng package bài cá nhân:

```powershell
$env:LAB_SOLUTION_PACKAGE='src.Le_Tri_Tung-2A202601458'
py -m pytest tests/ -v
```

Kết quả:

```text
collected 42 items
...
============================= 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua:** 42 / 42

---

## 4. Dự đoán độ tương tự

| Cặp | Câu A | Câu B | Dự đoán |
|------|-----------|-----------|---------|
| 1 | Khách hàng có thể đổi trả sản phẩm trong 7 ngày. | Người mua được trả hàng trong vòng bảy ngày. | Cao |
| 2 | Thanh toán bằng ví điện tử được hỗ trợ. | Đơn hàng có thể trả tiền qua ví điện tử. | Cao |
| 3 | Chính sách giao hàng miễn phí cho đơn từ 500k. | Thời tiết hôm nay có mưa lớn. | Thấp |
| 4 | Người bán cần xác minh danh tính trước khi mở gian hàng. | Seller phải hoàn tất xác thực tài khoản để bán hàng. | Cao |
| 5 | Dữ liệu cá nhân được bảo vệ theo chính sách riêng tư. | Con mèo đang ngủ trên ghế. | Thấp |

**Nhận xét:**  
Các cặp cùng nói về một chính sách TMĐT thì nên có similarity cao, còn các cặp khác chủ đề thì similarity thấp. Nếu dùng mock embedder, kết quả có thể không phản ánh đúng ngữ nghĩa thật; để đánh giá tốt hơn nên dùng local multilingual embedder.

---

## 5. Kết quả truy xuất của tôi

Tôi chạy 5 câu hỏi benchmark chính thức của nhóm trên corpus `data/k4_ecommerce` bằng chiến lược cá nhân `RecursiveChunker(chunk_size=300)`. Lệnh benchmark nhóm:

```bash
py scripts/group_benchmark.py
```

Embedding dùng cho benchmark là deterministic keyword/category embedding để kết quả có thể lặp lại trong môi trường lớp học; không dùng mock hash embedding vì mock không phản ánh tốt ngữ nghĩa tiếng Việt.

| # | Câu hỏi | Top-1 Chunk truy xuất được | Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|---------|-----------------------------|------:|---------------------|----------------------------------|
| 1 | Người mua cần làm gì khi muốn đổi trả sản phẩm bị lỗi? | `k4-returns-policy::chunk_0` | 6.00 | Có | Người mua gửi yêu cầu đổi trả trong thời hạn quy định và cung cấp bằng chứng như hình ảnh/video/mô tả lỗi. |
| 2 | Người bán cần cung cấp thông tin gì trước khi bắt đầu bán hàng? | `k4-seller-listing::chunk_0` | 8.00 | Có | Người bán cần thông tin định danh, tài khoản ngân hàng; doanh nghiệp cần giấy phép đăng ký kinh doanh, mã số thuế và tài khoản ngân hàng. |
| 3 | Vì sao người mua nên thanh toán trong nền tảng? | `k4-payment-security::chunk_0` | 16.00 | Có | Thanh toán trong nền tảng giúp giữ lịch sử đơn hàng, bằng chứng thanh toán và cơ sở hỗ trợ khi có tranh chấp. |
| 4 | Khi đơn giao chậm hoặc thất lạc, người mua nên cung cấp thông tin gì? | `k4-shipping-support::chunk_0` | 10.00 | Có | Người mua nên liên hệ hỗ trợ và cung cấp mã đơn hàng để kiểm tra lịch sử vận chuyển. |
| 5 | Dữ liệu cá nhân được dùng cho những mục đích nào? | `k4-privacy-policy::chunk_0` | 12.00 | Có | Dữ liệu cá nhân được dùng để xử lý đơn hàng, giao hàng, xác minh thanh toán, hỗ trợ khách hàng, xử lý khiếu nại, phát hiện gian lận và cải thiện dịch vụ. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Top-3 doc_ids theo từng câu hỏi:**

| # | Top-3 doc_ids | Top-3 scores |
|---|---------------|--------------|
| 1 | `k4-returns-policy`, `k4-returns-policy`, `k4-returns-policy` | 6.00, 4.00, 4.00 |
| 2 | `k4-seller-listing`, `k4-seller-listing`, `k4-seller-listing` | 8.00, 8.00, 6.00 |
| 3 | `k4-payment-security`, `k4-payment-security`, `k4-payment-security` | 16.00, 14.00, 12.00 |
| 4 | `k4-shipping-support`, `k4-shipping-support`, `k4-shipping-support` | 10.00, 6.00, 4.00 |
| 5 | `k4-privacy-policy`, `k4-privacy-policy`, `k4-privacy-policy` | 12.00, 2.00, 2.00 |

**Bài học rút ra:**  
Recursive chunking hoạt động tốt với corpus chính sách vì nó ưu tiên tách theo đoạn và câu trước khi phải cắt cứng theo ký tự. Metadata như `customer_role`, `category`, `source_url`, `retrieved_at` giúp lọc đúng phạm vi và truy vết nguồn trả lời, đặc biệt ở câu hỏi dành riêng cho người bán.

---

## Tự đánh giá cá nhân

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi | 10 / 10 |
| Hoàn thiện code (Core Implementation) | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất của tôi | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
