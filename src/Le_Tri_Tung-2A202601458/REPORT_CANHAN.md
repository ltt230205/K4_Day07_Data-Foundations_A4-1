# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Le Tri Tung  
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

Lưu ý: thư mục có dấu `-` theo đúng tên yêu cầu nên không import trực tiếp bằng dotted package name thông thường của Python. Code vẫn được đặt riêng theo folder cá nhân.

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

Với phần nhóm, 5 câu hỏi đánh giá cần thống nhất chung giữa các thành viên. Khi có bộ tài liệu nhóm, tôi sẽ chạy cùng corpus với chiến lược cá nhân của mình và ghi top-3 chunk cho từng câu hỏi.

| # | Câu hỏi | Top-1 Chunk | Score | Có liên quan không? | Ghi chú |
|---|---------|-------------|-------|---------------------|---------|
| 1 | Khách hàng được đổi trả trong bao lâu? | [Chạy sau khi có corpus nhóm] | | | |
| 2 | Đơn hàng nào được miễn phí giao hàng? | [Chạy sau khi có corpus nhóm] | | | |
| 3 | Người bán cần làm gì trước khi đăng sản phẩm? | [Chạy sau khi có corpus nhóm] | | | |
| 4 | Dữ liệu cá nhân được dùng để làm gì? | [Chạy sau khi có corpus nhóm] | | | |
| 5 | Có hỗ trợ thanh toán qua ví điện tử không? | [Chạy sau khi có corpus nhóm] | | | |

**Bài học rút ra:**  
Với chính sách TMĐT, chunk theo heading, điều khoản hoặc cặp FAQ thường giữ ý nghĩa tốt hơn chunk cố định. Metadata như `customer_role`, `category`, `source_url`, `retrieved_at` giúp lọc đúng phạm vi và truy vết nguồn trả lời.
