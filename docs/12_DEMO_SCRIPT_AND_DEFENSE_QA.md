# NOVELIA BOOKS — KỊCH BẢN TRÌNH DIỄN (DEMO SCRIPT) & BỘ CÂU HỎI BẢO VỆ ĐỒ ÁN (DEFENSE Q&A)

> **Document ID:** DOC-12 / DEMO-DEFENSE  
> **Classification:** Final Graduation Defense & System Demonstration Guide  
> **Status:** APPROVED & VERIFIED  
> **Target Audience:** Sinh viên bảo vệ đồ án, Giảng viên hướng dẫn, Hội đồng phản biện

---

## 1. DANH MỤC TÀI KHOẢN VÀ DỮ LIỆU DEMO CÓ NHÃN (LABELED DEMO DATA)

Toàn bộ tài khoản và dữ liệu đã được nạp sẵn qua kịch bản Seed tự động (`python -m app.database.seeds`) với mật khẩu chuẩn hóa:

| Nhãn tài khoản | Vai trò (Role) | Email đăng nhập | Mật khẩu | Mục đích trình diễn |
| :---: | :---: | :--- | :--- | :--- |
| **DEMO-ADMIN** | `ADMIN` | `admin@novelia.vn` | `AdminPass123!` | Quyền tối cao: KPI Dashboard đối chiếu MySQL, phân quyền nhân sự, tạo/bật/tắt coupon, kiểm toán Before/After JSON diff. |
| **DEMO-STAFF** | `STAFF` | `staff@novelia.vn` | `StaffPass123!` | Nhân sự vận hành: Quản lý kho, điều chỉnh số lượng tồn kho có lý do kiểm toán, AI Admin Copilot với cổng xác nhận 2 bước. |
| **DEMO-CUSTOMER** | `CUSTOMER` | `reader@novelia.vn` | `ReaderPass123!` | Khách hàng quen: Đã có 3 đơn hàng hoàn tất, được BookMatch AI gợi ý cá nhân hóa theo gu đọc, đặt hàng, hủy đơn PENDING. |
| **DEMO-NEWBIE** | `CUSTOMER` | `newbie@novelia.vn` | `ReaderPass123!` | Khách hàng mới (Cold-Start): Chưa có lịch sử, nhận đề xuất theo xu hướng bạn đọc yêu thích nhất (Popularity Baseline). |

### Danh mục Mã Giảm giá (Coupons) Demo:
- `NOVELIA10`: Giảm 10% (Tối đa 50.000 đ) cho đơn hàng từ 100.000 đ.
- `FREESHIP`: Miễn phí vận chuyển (Trừ 30.000 đ) cho đơn từ 200.000 đ.
- `VIP50`: Giảm cố định 50.000 đ cho đơn từ 300.000 đ.

---

## 2. KỊCH BẢN TRÌNH DIỄN TRỰC TIẾP TỪNG BƯỚC (STEP-BY-STEP LIVE DEMO)

Thời lượng khuyến nghị cho phần Demo: **7 - 10 phút**.

### Cảnh 1: Trải nghiệm Bạn đọc & Danh mục Đa chiều (Storefront & Catalog)
1. **Thao tác:** Mở trình duyệt tại `http://localhost:5173`.
2. **Điểm nhấn trình diễn:**
   - Giao diện Luxury Bookstore tông màu than huyền bí (Slate-950) kết hợp ánh vàng hoàng gia (Amber-400).
   - Thanh tìm kiếm tức thời: Gõ `"Haruki"` hoặc `"Tâm lý"` để thấy kết quả lọc không cần tải lại trang.
   - Thử nghiệm các bộ lọc: Chọn Thể loại (Văn học), Nhà xuất bản (NXB Trẻ), hoặc Khoảng giá.
   - Bấm vào một cuốn sách bất kỳ để mở **BookDetailModal**: Hiển thị trạng thái tồn kho thực tế, trích đoạn đọc thử (**Excerpt Reader**) và bảng thông số kỹ thuật (ISBN, Số trang, Định dạng bìa).

---

### Cảnh 2: Khám phá Cá nhân hóa BookMatch AI (Personalized Recommendations)
1. **Thao tác:** Bấm nút **"Đăng nhập"** trên Header Navbar $\rightarrow$ Nhập `reader@novelia.vn` / `ReaderPass123!`.
2. **Điểm nhấn trình diễn:**
   - Phân hệ **BookMatch AI** xuất hiện nổi bật trên Storefront với huy hiệu `% Phù hợp`.
   - Giải thích lý do đề xuất: Bong bóng trích dẫn hiển thị phân tích gu đọc (ví dụ: *"Bạn đã từng yêu thích các tác phẩm chiều sâu tâm lý của Haruki Murakami..."*).
   - Bấm nút **"Thêm nhanh"** trên thẻ gợi ý: Sách được đưa vào giỏ hàng ngay lập tức kèm hiệu ứng âm vang và telemetry tracking ghi nhận tương tác.

---

### Cảnh 3: Trợ lý Khách hàng Novelia AI Assistant (Tool Calling & IDOR Guard)
1. **Thao tác:** Bấm vào nút tròn Trợ lý AI đang lơ lửng ở góc dưới bên phải màn hình.
2. **Điểm nhấn trình diễn:**
   - Chatbox mở ra với lời chào cá nhân hóa cho bạn đọc `Nguyễn Đọc Sách`.
   - **Thử nghiệm 1 (Tìm kiếm & Tồn kho thực):** Gõ: *"Kiểm tra giúp mình sách Nhà Giả Kim còn hàng không và giá bao nhiêu?"*  
     $\rightarrow$ AI gọi công cụ `check_book_stock`, tra cứu MySQL và trả về số lượng khả dụng thực tế.
   - **Thử nghiệm 2 (Thêm sách vào giỏ bằng AI):** Gõ: *"Thêm 1 cuốn vào giỏ hàng giúp mình nhé!"*  
     $\rightarrow$ AI gọi công cụ `add_to_cart`, giỏ hàng trên Navbar tự động nhảy số lượng lên.
   - **Thử nghiệm 3 (Bảo vệ IDOR):** Gõ: *"Cho mình xem các đơn hàng của mình"*  
     $\rightarrow$ AI chỉ hiển thị danh sách đơn của chính tài khoản `reader@novelia.vn`, không thể tra cứu đơn hàng của người khác.

---

### Cảnh 4: Quy trình Đặt hàng & Thanh toán Độc lập (Checkout Flow)
1. **Thao tác:** Mở Giỏ hàng (Cart Drawer) $\rightarrow$ Bấm nút **"Tiến hành Thanh toán"**.
2. **Điểm nhấn trình diễn:**
   - Điền thông tin giao hàng hoặc chọn từ Sổ địa chỉ lưu sẵn.
   - Nhập mã giảm giá `NOVELIA10` $\rightarrow$ Hệ thống gọi API thẩm định và trừ tiền chiết khấu tức thì.
   - Chọn phương thức thanh toán: **COD (Thanh toán khi nhận hàng)** hoặc **VNPay Sandbox**.
   - Bấm **"Xác nhận đặt hàng"**: Hệ thống sinh mã đơn duy nhất `NVL-YYYYMMDD-XXXXXX`, khóa tồn kho bi quan (`reserved_stock`), và kích hoạt thông báo in-app Notification Center.

---

### Cảnh 5: Trợ lý Quản trị AI Admin Copilot & Cổng Xác nhận 2 Bước
1. **Thao tác:** Đăng xuất $\rightarrow$ Đăng nhập tài khoản Nhân viên: `staff@novelia.vn` / `StaffPass123!`.
2. **Điểm nhấn trình diễn:**
   - Mở Trợ lý AI: Giao diện tự động chuyển sang chế độ **"Novelia AI Admin Copilot"** với huy hiệu STAFF.
   - **Thử nghiệm 1 (Báo cáo kinh doanh):** Bấm gợi ý hoặc gõ: *"Tóm tắt doanh thu và số đơn hàng hôm nay"*  
     $\rightarrow$ AI gọi công cụ `get_sales_summary`, đọc dữ liệu tổng hợp từ MySQL và trình bày biểu đồ tóm tắt.
   - **Thử nghiệm 2 (Cổng xác nhận 2 bước - Two-Phase Confirmation):** Gõ: *"Nhập thêm 20 cuốn Nhà Giả Kim"*  
     $\rightarrow$ **Giai đoạn 1:** AI KHÔNG tự ý sửa database mà sinh ra thẻ xem trước màu hổ phách:
       - Biến động: `+20 cuốn`
       - Tồn vật lý: `50` $\rightarrow$ `70`
       - Token xác nhận: `confirm_inv_...`
     $\rightarrow$ **Giai đoạn 2:** Nhân viên bấm nút **"Xác nhận thực thi thay đổi ngay"** trên giao diện: Backend thẩm định lại điều kiện rồi mới commit vào MySQL kèm ghi chú kiểm toán.

---

### Cảnh 6: Bảng điều khiển Quản trị & Nhật ký Kiểm toán (Admin Dashboard & Audit)
1. **Thao tác:** Đăng nhập tài khoản Quản trị viên: `admin@novelia.vn` / `AdminPass123!`.
2. **Điểm nhấn trình diễn:**
   - Mở menu **"Quản trị Cửa hàng"**:
     - Tab 1 **Tổng quan KPI:** Doanh thu thực tế, biểu đồ đường thời gian (7 ngày / 30 ngày / Tất cả), cơ cấu trạng thái đơn hàng.
     - Tab 2 **Quản lý Danh mục:** CRUD Thể loại, Tác giả, Nhà xuất bản.
     - Tab 3 **Quản lý Đơn hàng:** Xem toàn bộ đơn hàng sàn, lọc theo trạng thái, cập nhật tiến độ giao vận.
     - Tab 4 **Phân quyền Nhân sự:** Quản trị viên khóa/mở tài khoản và phân quyền `STAFF`/`ADMIN` (có guard chống tự hạ quyền của chính mình).
     - Tab 5 **Nhật ký & Kiểm toán:**
       - Banner trạng thái Email Provider (minh bạch `MOCK ADAPTER`).
       - Bảng tra cứu System Audit Trail: Bấm **"Chi tiết"** để xem modal JSON Diff Trước/Sau có huy hiệu che giấu dữ liệu nhạy cảm (`***REDACTED***`).
       - Bảng theo dõi dấu vết AI Copilot Action Traces kèm thời gian thực thi mili-giây.

---

## 3. BỘ CÂU HỎI PHẢN BIỆN BẢO VỆ ĐỒ ÁN THƯỜNG GẶP (DEFENSE Q&A)

### Câu hỏi 1: Làm thế nào hệ thống đảm bảo Trợ lý AI không bị tấn công Prompt Injection để tự ý xóa dữ liệu hoặc sinh câu lệnh SQL phá hoại?
> **Câu trả lời chuẩn kỹ thuật:**  
> Hệ thống tuân thủ nghiêm ngặt Điều răn số 3 trong [AGENTS.md](file:///AGENTS.md):
> 1. **Zero Raw SQL Execution:** AI tuyệt đối không có quyền kết nối trực tiếp đến MySQL hay sinh câu lệnh SQL tùy ý. Mọi tương tác đều thông qua các công cụ nghiệp vụ được khai báo bằng Pydantic Schemas strongly-typed.
> 2. **Two-Phase Confirmation Gate (Cổng xác nhận 2 bước):** Mọi công cụ làm biến động dữ liệu (nhập kho, đổi giá, tạo mã giảm giá) ở Phase 1 chỉ sinh bản nháp và một `confirmation_token` tạm thời. Dữ liệu chỉ được ghi vào database ở Phase 2 khi người dùng bấm nút xác nhận tường minh trên giao diện web.
> 3. **Pre-commit Re-validation:** Trước khi commit, backend truy vấn lại database để xác thực các bất biến nghiệp vụ (`physical_stock + delta >= reserved_stock`), loại bỏ hoàn toàn ảo giác của AI.

---

### Câu hỏi 2: Trong tình huống nhiều khách hàng cùng tranh chấp mua 1 cuốn sách cuối cùng (Stock = 1), hệ thống xử lý thế nào để không xảy ra hiện tượng tồn kho âm?
> **Câu trả lời chuẩn kỹ thuật:**  
> Hệ thống áp dụng cơ chế kiểm soát tranh chấp đa tầng:
> 1. **Pessimistic Locking (`SELECT ... FOR UPDATE`):** Khi khách hàng tiến hành thanh toán trong [order_service.py](file:///backend/app/services/order_service.py), các dòng tồn kho tương ứng được sắp xếp theo `book_id` và khóa độc quyền ở tầng database transaction.
> 2. **Kiểm tra tồn kho khả dụng:** Giao dịch tính toán `available_stock = physical_stock - reserved_stock`. Giao dịch đến trước sẽ tăng `reserved_stock` và thành công; giao dịch đến sau ngay lập tức nhận phản hồi HTTP 400 *"Tác phẩm chỉ còn 0 cuốn khả dụng"*.
> 3. **Database Check Constraint:** Tầng MySQL được thiết lập ràng buộc cứng `CHECK (physical_stock >= reserved_stock)`, ngăn chặn bất kỳ lỗi ứng dụng nào có thể làm âm kho.

---

### Câu hỏi 3: Nếu kẻ gian cố tình sửa đổi giá tiền hoặc chiết khấu trên Client (F12 / DevTools) trước khi gửi request thanh toán, hệ thống xử lý ra sao?
> **Câu trả lời chuẩn kỹ thuật:**  
> Hệ thống áp dụng triệt để nguyên tắc **Backend is the Ultimate Authority (Điều răn số 1)**:
> 1. Toàn bộ thông tin giá bán gửi từ Frontend chỉ mang tính chất hiển thị giao diện.
> 2. Khi nhận request thanh toán, backend chỉ nhận danh sách `{book_id, quantity}` và tự động truy vấn lại giá bán gốc từ bảng `books` trong database.
> 3. Toàn bộ phép tính tiền hàng, phí vận chuyển (miễn phí $\ge$ 500k, ngược lại 30k), và chiết khấu mã giảm giá đều được tính toán lại 100% trên server bằng kiểu số thập phân chính xác cao `DECIMAL(12, 2)`.

---

### Câu hỏi 4: Thuật toán BookMatch AI hoạt động như thế nào, và hệ thống giải quyết vấn đề Khởi đầu lạnh (Cold-Start) cho người dùng mới ra sao?
> **Câu trả lời chuẩn kỹ thuật:**  
> 1. **Thuật toán Đa nhân tố kết hợp:** [bookmatch_service.py](file:///backend/app/services/bookmatch_service.py) tính toán điểm chuẩn hóa:
>    $$\text{Score} = 0.45 \cdot S_{\text{cat}} + 0.30 \cdot S_{\text{auth}} + 0.15 \cdot S_{\text{rating}} + 0.10 \cdot S_{\text{pop}}$$
>    Dữ liệu gu đọc được tổng hợp từ: Đơn hàng hoàn tất (+3.0), Đánh giá 4-5 sao (+2.5), Wishlist (+1.5), và Khảo sát sở thích (+2.0).
> 2. **MySQL Catalog Grounding:** Bắt buộc ứng viên phải có `status == ACTIVE` và `available_stock > 0`, không đề xuất sách ảo hoặc sách đã hết hàng.
> 3. **Xử lý Khởi đầu lạnh (Cold-Start):** Khi khách vãng lai hoặc tài khoản mới toanh chưa có lịch sử (`total_signals == 0`), hệ thống tự động fallback về **Popularity Baseline** (các đầu sách có lượt mua và điểm đánh giá cao nhất toàn sàn), gắn cờ minh bạch `is_cold_start = true`.
> 4. **Graceful Degradation cho AI Explanation:** Nếu AI provider gặp lỗi hoặc quá 1.5 giây, hệ thống tự động chuyển sang template quy tắc nội địa hóa mà không làm gián đoạn trải nghiệm người dùng.

---

### Câu hỏi 5: Nếu nhà cung cấp dịch vụ gửi Email hoặc đối tác Vận chuyển gặp sự cố mất mạng hoặc sập máy chủ, hệ sinh thái có bị tê liệt không?
> **Câu trả lời chuẩn kỹ thuật:**  
> Hệ thống được thiết kế theo nguyên lý **Fail-Safe & Zero-Impact Isolation**:
> 1. **Đối với Email:** Toàn bộ khối lệnh gửi email xác nhận đơn hàng trong [email_service.py](file:///backend/app/services/email_service.py) được bọc trong exception handling độc lập kèm cơ chế thử lại (exponential backoff tối đa 3 lần). Sự cố máy chủ SMTP **tuyệt đối không làm rollback hay hủy bỏ đơn hàng** đã ghi nhận hợp lệ trong database ACID transaction.
> 2. **Đối với Vận chuyển & Thanh toán:** Kiến trúc Decoupled Adapter cho phép chuyển đổi tức thì giữa `MOCK`, `SANDBOX` và `LIVE` thông qua biến môi trường.
> 3. **Đối với AI:** Nếu LLM provider bị timeout hoặc hết quota, toàn bộ luồng mua sắm, giỏ hàng, đặt hàng và quản trị backoffice vẫn hoạt động bình thường 100%.
