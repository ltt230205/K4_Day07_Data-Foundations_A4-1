# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm K4 Data Foundations  
**Thành viên:**
- Đỗ Thị Thanh Loan — 2A202601654
- Lê Trí Tùng — 2A202601458
- Nguyễn Quốc Bảo — 2A202601726
- Nguyễn Thùy Trang — 2A202601294
- Vũ Xuân Anh — 2A202602010

**Ngày:** 2026-08-03

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề cố định theo lớp K4:** Chính sách thương mại điện tử / hỗ trợ khách hàng.

**Phạm vi cụ thể nhóm tập trung:** Nhóm tập trung vào các chính sách hỗ trợ khách hàng và người bán trên sàn TMĐT: đổi trả, đăng bán, thanh toán, giao hàng và quyền riêng tư.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách đổi trả | https://www.lazada.vn/terms-of-use/ | 2026-08-03 / terms-index-crawled-2026-07 | 609 | `doc_id`, `title`, `customer_role=buyer`, `category=returns`, `language`, `source_url`, `retrieved_at`, `document_version` |
| 2 | Quy định đăng bán | https://sellercenter.lazada.vn/apps/register/index?gsc=1 | 2026-08-03 / seller-center-crawled-2026-07 | 765 | `doc_id`, `title`, `customer_role=seller`, `category=listing`, `language`, `source_url`, `retrieved_at`, `document_version` |
| 3 | Chính sách bảo mật thanh toán | https://pages.lazada.vn/wow/gcp/lazada/channel/vn/partnership/chinh-sach-bao-mat-thanh-toan | 2026-08-03 / 2022-12-14 | 791 | `doc_id`, `title`, `customer_role=buyer`, `category=payment`, `language`, `source_url`, `retrieved_at`, `document_version` |
| 4 | Hỗ trợ giao hàng và nhận hàng | https://www.lazada.vn/terms-of-use/ | 2026-08-03 / terms-index-crawled-2026-07 | 662 | `doc_id`, `title`, `customer_role=buyer`, `category=shipping`, `language`, `source_url`, `retrieved_at`, `document_version` |
| 5 | Chính sách bảo vệ thông tin cá nhân | https://www.lazada.vn/privacy/ | 2026-08-03 / 2025-04-23 | 1014 | `doc_id`, `title`, `customer_role=both`, `category=privacy`, `language`, `source_url`, `retrieved_at`, `document_version` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Corpus chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` trong metadata.
- [x] Mỗi tài liệu có `customer_role` theo yêu cầu riêng của K4.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `k4-returns-policy` | Định danh tài liệu, hỗ trợ truy vết chunk và xóa theo tài liệu. |
| `title` | string | `Chính sách đổi trả` | Hiển thị nguồn dễ đọc trong kết quả retrieval. |
| `customer_role` | enum/string | `buyer`, `seller`, `both` | Cho phép lọc câu hỏi theo vai trò người mua/người bán. |
| `category` | string | `returns`, `payment`, `privacy` | Giúp lọc hoặc phân nhóm truy vấn theo loại chính sách. |
| `language` | string | `vi` | Hữu ích khi corpus đa ngôn ngữ. |
| `source_url` | string | URL công khai | Truy vết nguồn và kiểm chứng gold answer. |
| `retrieved_at` | date/string | `2026-08-03` | Biết ngày nhóm lấy dữ liệu. |
| `document_version` | string | `2025-04-23` | Biết phiên bản/ngày hiệu lực của chính sách. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu đầu với `chunk_size=300`:

| Tài liệu | Chiến lược | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Chính sách bảo mật thanh toán | FixedSizeChunker | 3 | 283.7 | Trung bình, có thể cắt ngang ý. |
| Chính sách bảo mật thanh toán | SentenceChunker | 2 | 394.0 | Tốt, giữ câu nguyên vẹn nhưng chunk hơi dài. |
| Chính sách bảo mật thanh toán | RecursiveChunker | 4 | 196.2 | Tốt, giữ đoạn ngắn và dễ đọc. |
| Chính sách quyền riêng tư | FixedSizeChunker | 4 | 276.0 | Trung bình, đôi khi cắt giữa đoạn. |
| Chính sách quyền riêng tư | SentenceChunker | 2 | 505.5 | Tốt về câu nhưng chunk dài. |
| Chính sách quyền riêng tư | RecursiveChunker | 6 | 167.3 | Tốt nhất cho tài liệu nhiều đoạn. |
| Chính sách đổi trả | FixedSizeChunker | 3 | 223.0 | Ổn nhưng chưa bám theo mục nghiệp vụ. |
| Chính sách đổi trả | SentenceChunker | 2 | 303.0 | Tốt, các điều kiện đổi trả nằm cùng câu/đoạn. |
| Chính sách đổi trả | RecursiveChunker | 3 | 201.7 | Tốt, chunk ngắn và rõ ý. |

### Chiến lược của từng thành viên

**Thành viên 1 — Đỗ Thị Thanh Loan**
- **Loại chiến lược:** FixedSizeChunker, `chunk_size=300`, `overlap=0`.
- **Mô tả & lý do chọn:** Đây là baseline đơn giản nhất để so sánh. Chiến lược này dễ triển khai và ổn với tài liệu ngắn, nhưng có rủi ro cắt ngang một điều khoản hoặc câu dài.

**Thành viên 2 — Lê Trí Tùng**
- **Loại chiến lược:** RecursiveChunker, `chunk_size=300`.
- **Mô tả & lý do chọn:** Chiến lược đệ quy ưu tiên tách theo đoạn, dòng, câu rồi mới đến từ. Với chính sách TMĐT, cách này giữ được các đoạn điều kiện/ngoại lệ gọn hơn fixed-size.

**Thành viên 3 — Nguyễn Quốc Bảo**
- **Loại chiến lược:** SentenceChunker, `max_sentences_per_chunk=2`.
- **Mô tả & lý do chọn:** Chiến lược này giữ nguyên ranh giới câu nên phù hợp với FAQ và chính sách có câu trả lời ngắn. Điểm yếu là nếu một điều khoản cần nhiều câu liên tiếp thì có thể bị tách thiếu ngữ cảnh.

**Thành viên 4 — Nguyễn Thùy Trang**
- **Loại chiến lược:** FixedSizeChunker có overlap, `chunk_size=500`, `overlap=80`.
- **Mô tả & lý do chọn:** Overlap giúp giữ lại phần chuyển tiếp giữa hai chunk. Cách này phù hợp khi tài liệu có đoạn dài như quyền riêng tư hoặc bảo mật thanh toán.

**Thành viên 5 — Vũ Xuân Anh**
- **Loại chiến lược:** Custom heading/paragraph chunker.
- **Mô tả & lý do chọn:** Chiến lược custom tách theo heading và đoạn văn, phù hợp với tài liệu chính sách có tiêu đề rõ như `# Chính sách đổi trả`, `# Hỗ trợ giao hàng`. Đây là chiến lược gần với cách người dùng đọc tài liệu chính sách nhất.
- **Code snippet:**
```python
class HeadingParagraphChunker:
    """Tách tài liệu chính sách theo heading và đoạn văn."""

    def chunk(self, text: str) -> list[str]:
        chunks = []
        current = []
        for line in text.splitlines():
            if line.startswith("#") and current:
                chunks.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            chunks.append("\n".join(current).strip())

        refined = []
        for chunk in chunks:
            refined.extend(p.strip() for p in chunk.split("\n\n") if p.strip())
        return refined
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Đỗ Thị Thanh Loan | Fixed-size không overlap | 7 | Đơn giản, dễ tái lập, tốc độ nhanh. | Dễ cắt ngang câu hoặc điều kiện. |
| Lê Trí Tùng | Recursive | 8 | Chunk ngắn, giữ đoạn tốt, cân bằng giữa độ dài và ngữ cảnh. | Nếu separator không rõ, kết quả phụ thuộc nhiều vào cấu trúc văn bản. |
| Nguyễn Quốc Bảo | Sentence, 2 câu/chunk | 8 | Giữ nguyên câu, tốt với câu hỏi trực tiếp. | Có thể thiếu ngữ cảnh nếu gold answer trải qua nhiều câu. |
| Nguyễn Thùy Trang | Fixed-size có overlap | 7 | Ít mất ngữ cảnh ở ranh giới chunk. | Tạo lặp nội dung, tốn thêm token và bộ nhớ. |
| Vũ Xuân Anh | Heading/paragraph custom | 9 | Bám sát cấu trúc chính sách, chunk dễ đọc và dễ kiểm chứng. | Cần tài liệu có heading/đoạn rõ ràng. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**  
Chiến lược heading/paragraph custom phù hợp nhất vì tài liệu chính sách thường được tổ chức theo tiêu đề và đoạn nghiệp vụ. Khi tách theo cấu trúc này, mỗi chunk có khả năng chứa trọn một ý như đổi trả, xác minh người bán, thanh toán hoặc quyền riêng tư, giúp top-3 dễ có chunk đúng hơn.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn

| # | Câu hỏi | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua cần làm gì khi muốn đổi trả sản phẩm bị lỗi? | Người mua cần gửi yêu cầu đổi trả trong thời hạn quy định và cung cấp bằng chứng như hình ảnh, video mở hàng hoặc mô tả lỗi/sai mô tả. | `k4-returns-policy`, đoạn "Chính sách đổi trả". |
| 2 | Người bán cần cung cấp thông tin gì trước khi bắt đầu bán hàng? | Người bán cần cung cấp thông tin định danh và tài khoản ngân hàng; với hộ kinh doanh/doanh nghiệp cần giấy phép đăng ký kinh doanh, mã số thuế và tài khoản ngân hàng. | `k4-seller-listing`, đoạn "Quy định đăng bán sản phẩm". |
| 3 | Vì sao người mua nên thanh toán trong nền tảng? | Thanh toán trong nền tảng giúp giữ lịch sử đơn hàng, bằng chứng thanh toán và cơ sở hỗ trợ khi có tranh chấp. | `k4-payment-security`, đoạn "Chính sách bảo mật thanh toán". |
| 4 | Khi đơn giao chậm hoặc thất lạc, người mua nên cung cấp thông tin gì? | Người mua nên liên hệ trung tâm hỗ trợ và cung cấp mã đơn hàng để kiểm tra lịch sử vận chuyển. | `k4-shipping-support`, đoạn "Hỗ trợ giao hàng và nhận hàng". |
| 5 | Dữ liệu cá nhân được dùng cho những mục đích nào? | Dữ liệu cá nhân được dùng để xử lý đơn hàng, giao sản phẩm, xác minh thanh toán, hỗ trợ khách hàng, phản hồi khiếu nại, phát hiện gian lận và cải thiện dịch vụ. | `k4-privacy-policy`, đoạn "Chính sách bảo vệ thông tin cá nhân". |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Đổi trả sản phẩm bị lỗi | Heading/paragraph hoặc Sentence | Có | Câu hỏi bám sát đoạn đổi trả; chunk theo câu/đoạn giữ bằng chứng và điều kiện tốt. |
| 2 | Thông tin người bán cần cung cấp | Heading/paragraph hoặc Recursive | Có | Cần `metadata_filter={"customer_role": "seller"}` để tránh lẫn sang chính sách người mua. |
| 3 | Lý do thanh toán trong nền tảng | Recursive hoặc Heading/paragraph | Có | Chunk thanh toán có nhiều keyword đặc thù: giao dịch, hoàn tiền, tranh chấp. |
| 4 | Đơn giao chậm/thất lạc | Heading/paragraph | Có | Câu trả lời nằm gọn trong đoạn hỗ trợ giao hàng. |
| 5 | Mục đích xử lý dữ liệu cá nhân | Recursive hoặc Fixed-size overlap | Có | Tài liệu privacy dài hơn nên overlap hoặc recursive giúp giữ đủ danh sách mục đích. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**  
Có. Câu 2 nên dùng `metadata_filter={"customer_role": "seller"}` vì câu hỏi dành riêng cho người bán; nếu không lọc, các chunk buyer như thanh toán hoặc đổi trả có thể xuất hiện do cùng dùng từ "thông tin", "tài khoản", "đơn hàng". Metadata `category` cũng hữu ích khi câu hỏi nói rõ chủ đề như `payment`, `shipping`, `returns`.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích nhóm sẽ trình bày:**
- Cùng một corpus nhưng chunk theo heading/paragraph cho kết quả dễ đọc và dễ kiểm chứng hơn fixed-size.
- Metadata `customer_role` là bắt buộc và đặc biệt hữu ích với câu hỏi người bán.
- Mock embedder không đủ tốt để kết luận chất lượng tiếng Việt; khi chạy chính thức nên dùng `EMBEDDING_PROVIDER=local` hoặc OpenAI embedder.

**Bài học rút ra khi so sánh trong nhóm:**  
Fixed-size chunking là baseline tốt để bắt đầu nhưng không hiểu cấu trúc tài liệu. Sentence và recursive chunking giữ ý nghĩa tốt hơn, còn custom heading/paragraph phù hợp nhất với chính sách TMĐT vì mỗi heading thường tương ứng một nhóm nghiệp vụ.

**Failure case:**  
Câu hỏi về "thông tin người bán" có thể thất bại nếu không dùng metadata filter vì các tài liệu thanh toán/quyền riêng tư cũng chứa nhiều từ như "thông tin", "tài khoản", "xác minh". Cách cải thiện là lọc trước bằng `customer_role=seller` hoặc `category=listing`, đồng thời giữ chunk người bán theo heading riêng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu?**  
Nhóm sẽ mở rộng corpus lên 8-10 tài liệu thật, tách mỗi chính sách theo heading gốc, và thêm metadata chi tiết hơn như `policy_type`, `risk_level`, `effective_date`. Nhóm cũng sẽ chạy lại benchmark bằng local multilingual embedder để kết quả phản ánh ngữ nghĩa tiếng Việt tốt hơn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **36 / 40** |
