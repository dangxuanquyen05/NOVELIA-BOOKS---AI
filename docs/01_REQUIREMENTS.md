# NOVELIA BOOKS — REQUIREMENTS SPECIFICATION

> **Document ID:** DOC-01  
> **Version:** 1.0.0  
> **Status:** Approved / Baseline  
> **Authors:** Senior Software Architect, Technical Lead, AI Engineer, QA Lead  
> **Target Date:** 2026-10-19

---

## 1. PHÂN HỆ VÀ YÊU CẦU CHỨC NĂNG (FUNCTIONAL REQUIREMENTS)

### 1.1. Phân hệ 1: Storefront (Giao diện Cửa hàng Trực tuyến)
- **FR-ST-01 (Trang chủ):** Hiển thị banner nổi bật, danh mục sách tiêu biểu, sách mới phát hành, sách bán chạy nhất, sách được đề xuất và khu vực khám phá nhanh qua BookMatch AI.
- **FR-ST-02 (Tìm kiếm & Bộ lọc):** Cho phép tìm kiếm toàn văn theo tiêu đề, tác giả, tên nhà xuất bản, hoặc mã ISBN. Hỗ trợ bộ lọc kết hợp nhiều tiêu chí: thể loại (Categories), khoảng giá (Price range), đánh giá sao (Ratings), định dạng bìa (Bìa mềm/Bìa cứng), và tình trạng còn hàng (In stock).
- **FR-ST-03 (Chi tiết sách):** Hiển thị đầy đủ thông tin sách: hình ảnh chất lượng cao, tên sách, tác giả, nhà xuất bản, năm xuất bản, ngôn ngữ, số trang, kích thước, trọng lượng (phục vụ tính phí vận chuyển), tóm tắt nội dung, mục lục hoặc trích đoạn đọc thử, giá gốc, giá khuyến mãi, số lượng tồn kho khả dụng.
- **FR-ST-04 (Tác giả & Nhà xuất bản):** Trang thông tin tiểu sử tác giả và danh sách các tác phẩm liên quan đang kinh doanh tại cửa hàng.
- **FR-ST-05 (Đánh giá & Nhận xét):** Khách hàng đã mua sách có thể để lại đánh giá (1 đến 5 sao) và nhận xét có kiểm duyệt; hiển thị điểm đánh giá trung bình và phân bố sao.
- **FR-ST-06 (Danh sách yêu thích - Wishlist):** Người dùng đã đăng nhập có thể thêm/xóa sách khỏi wishlist cá nhân, nhận thông báo khi sách trong wishlist giảm giá hoặc có hàng lại.
- **FR-ST-07 (Giỏ hàng):** Hỗ trợ thêm sách vào giỏ, cập nhật số lượng, kiểm tra tồn kho theo thời gian thực trước khi chuyển sang bước thanh toán, tính toán tạm tính (subtotal).
- **FR-ST-08 (Thanh toán - Checkout):** Quy trình thanh toán nhiều bước chuẩn mực: lựa chọn sổ địa chỉ giao hàng, lựa chọn phương thức vận chuyển, nhập mã voucher/giảm giá, lựa chọn phương thức thanh toán (COD, Chuyển khoản/Cổng thanh toán), xem lại tóm tắt đơn hàng có chi tiết phí ship và thuế/giảm giá trước khi nhấn Đặt hàng.
- **FR-ST-09 (Hồ sơ & Lịch sử đơn hàng):** Khách hàng quản lý thông tin cá nhân, danh sách địa chỉ nhận hàng (đặt địa chỉ mặc định), xem lịch sử tất cả đơn hàng đã đặt kèm trạng thái chi tiết, mã vận đơn và chi tiết hóa đơn.
- **FR-ST-10 (Chatbox AI):** Cửa sổ chat AI nổi (floating widget) cho phép tương tác trực tiếp với Novelia AI Assistant ở bất kỳ trang nào trên Storefront.

---

### 1.2. Phân hệ 2: Authentication & Authorization (Xác thực & Phân quyền)
- **FR-AUTH-01 (Đăng ký tài khoản):** Đăng ký bằng Email và Mật khẩu; kiểm tra định dạng email chuẩn, độ mạnh mật khẩu (tối thiểu 8 ký tự, có chữ hoa, số và ký tự đặc biệt). Mã hóa mật khẩu an toàn bằng thuật toán băm chuẩn (Argon2id hoặc bcrypt có salt).
- **FR-AUTH-02 (Đăng nhập & Phiên làm việc):** Đăng nhập xác thực thông tin tài khoản, cấp phát Access Token (JWT thời hạn ngắn, ví dụ 15-30 phút) và Refresh Token được bảo vệ trong HTTP-only Secure Cookie hoặc cơ chế lưu trữ bảo mật chống tấn công XSS.
- **FR-AUTH-03 (Phân quyền RBAC):** Hệ thống phân quyền chặt chẽ dựa trên 3 vai trò:
  - `CUSTOMER`: Khách hàng mua sắm, quản lý giỏ hàng, đơn hàng cá nhân, đánh giá sách.
  - `STAFF`: Nhân viên vận hành, quản lý đơn hàng, kho hàng, danh mục sản phẩm, xem báo cáo vận hành.
  - `ADMIN`: Quản trị viên cao nhất, toàn quyền cấu hình hệ thống, quản lý tài khoản nhân viên, xem báo cáo doanh thu tài chính, quản lý nhật ký hệ thống và AI.
- **FR-AUTH-04 (Kiểm tra quyền phía Backend):** Bắt buộc 100% các API riêng tư (Private Endpoints) phải kiểm tra quyền hạn thông qua dependency injection. Tuyệt đối không dựa vào việc ẩn/hiển thị nút bấm trên giao diện để bảo vệ tài nguyên.
- **FR-AUTH-05 (Đăng xuất & Thu hồi Token):** Thu hồi Refresh Token khi đăng xuất để vô hiệu hóa phiên làm việc ngay lập tức.

---

### 1.3. Phân hệ 3: Catalog & Inventory (Danh mục & Quản lý Kho)
- **FR-CAT-01 (Quản lý thực thể Danh mục):** CRUD cho Sách (Books), Tác giả (Authors), Thể loại (Categories), Nhà xuất bản (Publishers). Hỗ trợ quan hệ nhiều-nhiều (một cuốn sách có thể có nhiều tác giả và thuộc nhiều thể loại).
- **FR-CAT-02 (Định danh & Siêu dữ liệu):** Mỗi sách có mã SKU nội bộ duy nhất, mã vạch chuẩn quốc tế ISBN-10 / ISBN-13, tình trạng kinh doanh (`DRAFT`, `ACTIVE`, `OUT_OF_STOCK`, `DISCONTINUED`).
- **FR-CAT-03 (Quản lý giá):** Lưu trữ giá bìa (niêm yết) và giá bán thực tế bằng kiểu dữ liệu số nguyên hoặc số thực thập phân có độ chính xác cao (`DECIMAL`).
- **FR-INV-01 (Theo dõi tồn kho theo thời gian thực):** Hệ thống theo dõi chính xác:
  - Tồn kho vật lý (Physical Stock): Số lượng thực tế trong kho.
  - Tồn kho giữ chỗ (Reserved Stock): Số lượng đang nằm trong các đơn hàng chờ thanh toán hoặc đang xử lý.
  - Tồn kho khả dụng (Available Stock) = Tồn kho vật lý - Tồn kho giữ chỗ.
- **FR-INV-02 (Lịch sử giao dịch kho - Inventory Audit Log):** Bắt buộc ghi nhận mọi biến động kho thành các bản ghi giao dịch (`inventory_transactions`) bao gồm: loại giao dịch (`INBOUND_IMPORT`, `OUTBOUND_ORDER`, `RETURN_RESTOCK`, `MANUAL_ADJUSTMENT`), số lượng thay đổi, tồn trước và sau giao dịch, nhân viên thực hiện, mã chứng từ liên quan và lý do điều chỉnh.
- **FR-INV-03 (Cảnh báo tồn kho thấp):** Tự động cảnh báo trên trang quản trị khi số lượng khả dụng của một đầu sách giảm xuống dưới ngưỡng an toàn (Safety Stock Threshold).

---

### 1.4. Phân hệ 4: Order & Payment (Đơn hàng & Thanh toán)
- **FR-ORD-01 (Tạo đơn hàng nguyên khối - Atomic Order Placement):** Khi khách hàng nhấn Đặt hàng, backend thực thi một Database Transaction nguyên khối bao gồm:
  1. Kiểm tra tồn kho khả dụng cho toàn bộ các mục trong giỏ hàng.
  2. Khóa dòng dữ liệu tồn kho (`SELECT ... FOR UPDATE` hoặc Optimistic Versioning) để chống tranh chấp dữ liệu (Race Condition).
  3. Xác thực lại giá bán hiện tại và điều kiện áp dụng mã voucher.
  4. Tạo bản ghi đơn hàng (`orders`) và các dòng đơn hàng (`order_items`).
  5. Tạo bản ghi snapshot lưu lại thông tin cố định tại thời điểm mua: Tên sách, ISBN, Đơn giá mua thực tế, Tỷ lệ giảm giá.
  6. Tăng lượng giữ chỗ hoặc trừ tồn kho tương ứng.
  7. Làm trống giỏ hàng của người dùng.
- **FR-ORD-02 (Máy trạng thái đơn hàng - Order State Machine):**
  - Trạng thái hợp lệ: `PENDING` (Chờ xử lý/thanh toán) -> `CONFIRMED` (Đã xác nhận) -> `PROCESSING` (Đang đóng gói) -> `SHIPPED` (Đang giao hàng) -> `DELIVERED` (Đã giao thành công).
  - Trạng thái kết thúc ngoại lệ: `CANCELLED` (Đã hủy), `RETURNED` (Đã trả hàng/Hoàn tiền).
  - Mọi bước chuyển trạng thái phải được kiểm tra tính hợp lệ và ghi vào bảng lịch sử trạng thái (`order_status_history`).
- **FR-ORD-03 (Động cơ khuyến mãi - Voucher Engine):** Hỗ trợ mã giảm giá theo tỷ lệ phần trăm (có mức giảm tối đa) hoặc theo số tiền cố định; kiểm tra điều kiện giá trị đơn hàng tối thiểu, giới hạn lượt dùng toàn hệ thống và giới hạn mỗi khách hàng.
- **FR-PAY-01 (Phương thức COD - Cash on Delivery):** Thanh toán khi nhận hàng, tự động kích hoạt trạng thái đơn hàng sang `CONFIRMED` khi nhân viên xác thực.
- **FR-PAY-02 (Cổng thanh toán điện tử - Payment Adapters):** Thiết kế lớp trừu tượng `PaymentProvider` hỗ trợ các cổng như VNPay, MoMo, ZaloPay qua chế độ Sandbox:
  - Tạo URL thanh toán an toàn kèm chữ ký số (Checksum / HMAC-SHA512).
  - Tiếp nhận và xử lý Webhook / IPN (Instant Payment Notification) từ cổng thanh toán có xác thực chữ ký số trước khi cập nhật trạng thái thanh toán.
  - Phân định rõ ràng giữa môi trường giả lập (Mock), môi trường kiểm thử (Sandbox) và môi trường thực tế (Live).

---

### 1.5. Phân hệ 5: Shipping (Vận chuyển & Giao nhận)
- **FR-SHIP-01 (Kiến trúc ShippingProvider):** Cung cấp giao diện trừu tượng hóa dịch vụ vận chuyển để tích hợp các đơn vị logistics tại Việt Nam (Giao Hàng Nhanh - GHN, Giao Hàng Tiết Kiệm - GHTK).
- **FR-SHIP-02 (Tính phí vận chuyển):** Tính phí tự động dựa trên địa chỉ giao hàng (Tỉnh/Thành phố, Quận/Huyện, Phường/Xã) và tổng trọng lượng/thể tích của giỏ hàng.
- **FR-SHIP-03 (Tạo vận đơn):** Khi đơn hàng chuyển sang trạng thái sẵn sàng xuất kho, hệ thống gửi yêu cầu tạo vận đơn đến nhà cung cấp dịch vụ vận chuyển, nhận về mã vận đơn (Tracking Code) và lưu vào hệ thống.
- **FR-SHIP-04 (Theo dõi hành trình):** Lưu vết các sự kiện vận chuyển (`shipment_events`) từ các cập nhật trạng thái hoặc webhook của đơn vị vận chuyển, cho phép khách hàng tra cứu tiến độ kiện hàng trực tiếp trên website.
- **FR-SHIP-05 (Chế độ tích hợp minh bạch):** Khi chưa có thông tin xác thực (Credentials) thật của GHN/GHTK, hệ thống sử dụng `MockShippingProvider` với quy trình giả lập logic đầy đủ; tuyệt đối không công bố kết nối thành công nếu chưa vượt qua kiểm thử API thực tế.

---

### 1.6. Phân hệ 6: Admin Dashboard (Quản trị & Báo cáo)
- **FR-ADM-01 (Bảng tổng quan KPI):** Hiển thị doanh thu thuần trong ngày/tuần/tháng/năm, tổng số đơn hàng mới, số lượng khách hàng mới, tỷ lệ hoàn tất đơn hàng, giá trị trung bình mỗi đơn (AOV - Average Order Value).
- **FR-ADM-02 (Biểu đồ doanh thu & tăng trưởng):** Biểu đồ trực quan hóa doanh thu theo thời gian, lọc theo khoảng thời gian tùy chọn; dữ liệu được tính toán chính xác từ backend, không sử dụng số liệu ngẫu nhiên (hardcoded mock) ở frontend.
- **FR-ADM-03 (Báo cáo sách bán chạy):** Bảng xếp hạng các đầu sách có doanh số và doanh thu cao nhất trong kỳ.
- **FR-ADM-04 (Quản lý Đơn hàng & Xử lý nhanh):** Danh sách đơn hàng trực quan với bộ lọc trạng thái, tìm kiếm theo mã đơn, hỗ trợ xem chi tiết đơn, in phiếu xuất kho, chuyển trạng thái đơn hàng.
- **FR-ADM-05 (Quản lý Khách hàng):** Danh sách khách hàng, lịch sử mua hàng, tổng chi tiêu (LTV - Lifetime Value), trạng thái tài khoản (Hoạt động / Bị khóa).
- **FR-ADM-06 (Quản lý Khuyến mãi & Chiến dịch):** Tạo và theo dõi hiệu quả các mã giảm giá, giới hạn ngân sách và thời gian kích hoạt.
- **FR-ADM-07 (Nhật ký kiểm toán & Giám sát AI):** Giao diện theo dõi toàn bộ hoạt động của hệ thống và nhật ký gọi công cụ của trợ lý AI (Ai Audit Log) để đảm bảo tính minh bạch và an toàn vận hành.

---

### 1.7. Phân hệ 7: Novelia AI Assistant (Trợ lý AI Đa chức năng)
- **FR-AI-01 (Tư vấn sách tiếng Việt tự nhiên):** Đàm thoại thông minh bằng tiếng Việt, hiểu ngữ cảnh và yêu cầu tìm sách theo chủ đề, tâm trạng, độ tuổi, mục đích đọc.
- **FR-AI-02 (Tìm kiếm & Lọc dữ liệu qua Tool Calling):** Trợ lý chuyển đổi câu hỏi tự nhiên của người dùng thành tham số gọi công cụ backend (`search_books_tool`, `get_book_details_tool`) để truy xuất dữ liệu từ danh mục sách thực tế, không tự bịa đặt thông tin sách.
- **FR-AI-03 (Kiểm tra kho và giá thực tế):** Cung cấp thông tin giá bán và tình trạng còn hàng chính xác thông qua công cụ nghiệp vụ (`check_stock_tool`).
- **FR-AI-04 (Tra cứu đơn hàng cá nhân):** Khách hàng đã đăng nhập có thể nhờ AI kiểm tra tiến độ giao hàng của các đơn hàng thuộc quyền sở hữu của chính họ (`get_my_order_status_tool`). Tuyệt đối không cho phép tra cứu đơn hàng của người khác.
- **FR-AI-05 (Hỗ trợ nghiệp vụ quản trị theo Role):** Khi người dùng có quyền `STAFF` hoặc `ADMIN`, AI có thể hỗ trợ các tác vụ vận hành:
  - Soạn thảo nội dung bản nháp tóm tắt sách, giới thiệu tác giả mới (`draft_book_metadata_tool`).
  - Soạn thảo bản nháp thông điệp chiến dịch khuyến mãi (`draft_promotion_campaign_tool`).
  - Hỗ trợ phân tích báo cáo doanh thu và cảnh báo tồn kho qua dịch vụ chuyên biệt (`query_business_metrics_tool`).
- **FR-AI-06 (Quy trình xác nhận hai bước cho thao tác thay đổi dữ liệu):** Mọi hành động của AI có tác động làm biến đổi dữ liệu (tạo bản nháp, cập nhật tồn kho, hủy đơn hàng) đều KHÔNG ĐƯỢC tự động thực thi ngay. AI phải trả về tóm tắt yêu cầu và yêu cầu người dùng xác nhận trên giao diện trước khi backend thực thi.
- **FR-AI-07 (Ghi nhật ký kiểm toán AI):** Mọi lượt gọi công cụ của AI đều được lưu vào `ai_audit_logs`.

---

### 1.8. Phân hệ 8: BookMatch AI (Cá nhân hóa Khám phá Sách)
- **FR-BM-01 (Hồ sơ sở thích đọc sách):** Cho phép khách hàng thiết lập sở thích cá nhân (thể loại yêu thích, tác giả quan tâm, phong cách viết, chủ đề muốn tìm hiểu).
- **FR-BM-02 (Đề xuất cá nhân hóa):** Thuật toán đối khớp sở thích người dùng với danh mục sách hiện có trong hệ thống, đề xuất danh sách sách phù hợp nhất kèm điểm tương đồng và phân tích lý do đề xuất rõ ràng.
- **FR-BM-03 (Cơ chế Fallback cho người dùng mới - Cold-Start):** Đối với khách hàng chưa có lịch sử mua sắm hoặc chưa cung cấp sở thích, hệ thống tự động fallback sang đề xuất sách bán chạy nhất (Best-sellers), sách có điểm đánh giá cao nhất (Top-rated) hoặc sách mới nổi bật theo từng thể loại phổ biến.
- **FR-BM-04 (Bảo vệ quyền riêng tư dữ liệu):** Dữ liệu tương tác và sở thích đọc sách của người dùng chỉ được sử dụng cho mục đích cải thiện trải nghiệm cá nhân, không chia sẻ cho bên thứ ba và có tùy chọn làm mới/xóa dữ liệu sở thích.

---

## 2. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS)

### 2.1. Hiệu năng & Tải (Performance & Scalability)
- **NFR-PERF-01 (Thời gian phản hồi API):** Các API đọc dữ liệu (Storefront, Catalog, Book Details) phải có thời gian phản hồi p95 < 200ms trên môi trường máy chủ tiêu chuẩn.
- **NFR-PERF-02 (Thời gian phản hồi AI):** Luồng xử lý AI qua API bên ngoài phải có cơ chế streaming phản hồi hoặc trả lời trong vòng 3-8 giây; thiết lập timeout tối đa 20 giây để không gây treo giao diện.
- **NFR-PERF-03 (Xử lý đồng thời):** Hệ thống đặt hàng và kiểm tra kho phải chịu được các giao dịch đồng thời mà không bị deadlock hoặc sai lệch số liệu tồn kho.

### 2.2. Bảo mật & An toàn thông tin (Security & Privacy)
- **NFR-SEC-01 (Kiểm soát truy cập):** Áp dụng nguyên tắc đặc quyền tối thiểu (Least Privilege). Mọi endpoint đều phải được bảo vệ bởi xác thực phân quyền nghiêm ngặt.
- **NFR-SEC-02 (Chống tấn công Web):** Bảo vệ toàn diện trước các lỗ hổng OWASP Top 10: SQL Injection (sử dụng SQLAlchemy Parameterized Queries), XSS (Sanitize input/output, React auto-escaping), CSRF (SameSite cookies / CSRF tokens), IDOR (Validate ownership of records).
- **NFR-SEC-03 (Rào chắn AI - Prompt Injection Defense):** Nội dung từ người dùng hoặc văn bản sách không được tin cậy như chỉ thị hệ thống; phân tách rõ ràng giữa System Prompt, Context và User Message.

### 2.3. Tính toàn vẹn & Nhất quán dữ liệu (Data Integrity)
- **NFR-DATA-01 (ACID Transactions):** Tất cả các thao tác thay đổi nhiều bảng liên quan (như đặt hàng + trừ kho + ghi log) phải thực hiện trong một Transaction nguyên khối.
- **NFR-DATA-02 (Không làm tròn sai lệch tài chính):** Sử dụng `DECIMAL(12, 2)` cho toàn bộ dữ liệu tiền tệ. Không dùng kiểu `FLOAT` hoặc `DOUBLE`.
- **NFR-DATA-03 (Audit Trail):** Mọi biến động số lượng tồn kho và trạng thái đơn hàng đều phải có bản ghi lịch sử truy vết không thể xóa.

### 2.4. Độ tin cậy & Chịu lỗi (Reliability & Fault Tolerance)
- **NFR-REL-01 (Graceful Degradation):** Khi dịch vụ AI bên ngoài không khả dụng (lỗi mạng, hết quota, timeout), toàn bộ chức năng mua sắm, thanh toán, quản lý kho và xem báo cáo vẫn hoạt động bình thường 100%. Trợ lý AI hiển thị thông báo lỗi lịch sự, không làm sập ứng dụng.
- **NFR-REL-02 (Idempotency):** Xử lý Webhook thanh toán và tạo đơn hàng phải có cơ chế chống xử lý trùng lặp (Idempotent Handling) dựa trên mã giao dịch duy nhất.

### 2.5. Khả năng bảo trì & Mở rộng (Maintainability)
- **NFR-MAINT-01 (Clean Architecture):** Tách biệt rõ ràng các lớp Router, Service, Repository, Model và Schemas.
- **NFR-MAINT-02 (Cấu hình linh hoạt):** Toàn bộ cấu hình hệ thống (cổng, chuỗi kết nối database, API keys) đều được quản lý tập trung qua biến môi trường (`.env` và `pydantic-settings`).

---

## 3. BẢNG PHÂN QUYỀN MA TRẬN (ROLE-BASED ACCESS CONTROL MATRIX)

| Chức năng / Tài nguyên | Guest (Vãng lai) | Customer (Thành viên) | Staff (Nhân viên) | Admin (Quản trị viên) |
| :--- | :---: | :---: | :---: | :---: |
| Xem trang chủ, danh mục, sách | ✅ Đọc | ✅ Đọc | ✅ Đọc | ✅ Đọc |
| Tìm kiếm, lọc sách | ✅ Đọc | ✅ Đọc | ✅ Đọc | ✅ Đọc |
| Trò chuyện AI (Tư vấn chung) | ✅ Đọc | ✅ Đọc | ✅ Đọc | ✅ Đọc |
| BookMatch AI (Cá nhân hóa) | Fallback Mode | ✅ Đầy đủ | ✅ Đầy đủ | ✅ Đầy đủ |
| Quản lý Wishlist cá nhân | ❌ Không | ✅ CRUD | ✅ CRUD | ✅ CRUD |
| Giỏ hàng & Đặt hàng | ❌ Cần login | ✅ Toàn quyền | ✅ Toàn quyền | ✅ Toàn quyền |
| Xem lịch sử đơn của bản thân | ❌ Không | ✅ Đọc | ✅ Đọc | ✅ Đọc |
| Tra cứu đơn hàng của người khác| ❌ Không | ❌ Bị cấm | ❌ Bị cấm | ✅ Đọc |
| Đánh giá sách đã mua | ❌ Không | ✅ Tạo/Sửa | ✅ Tạo/Sửa | ✅ Kiểm duyệt/Xóa |
| Quản lý danh mục sách/tác giả | ❌ Không | ❌ Không | ✅ Tạo/Sửa | ✅ Toàn quyền |
| Quản lý tồn kho & Phiếu nhập | ❌ Không | ❌ Không | ✅ Thực hiện | ✅ Toàn quyền |
| Cập nhật trạng thái đơn hàng | ❌ Không | ❌ Không | ✅ Xử lý | ✅ Toàn quyền |
| Xem Dashboard & Báo cáo doanh thu| ❌ Không | ❌ Không | ❌ Không | ✅ Toàn quyền |
| Quản lý tài khoản người dùng/Role| ❌ Không | ❌ Không | ❌ Không | ✅ Toàn quyền |
| Xem AI Audit Logs & System Logs | ❌ Không | ❌ Không | ❌ Không | ✅ Toàn quyền |
| AI Tool: Tra cứu đơn cá nhân | ❌ Không | ✅ Gọi được | ✅ Gọi được | ✅ Gọi được |
| AI Tool: Soạn thảo bản nháp/Khuyến mãi | ❌ Không | ❌ Bị từ chối | ✅ Yêu cầu xác nhận | ✅ Yêu cầu xác nhận |
| AI Tool: Báo cáo số liệu kinh doanh | ❌ Không | ❌ Bị từ chối | ❌ Bị từ chối | ✅ Có phân quyền |
