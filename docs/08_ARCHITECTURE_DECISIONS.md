# NOVELIA BOOKS — ARCHITECTURE DECISION RECORDS (ADR)

> **Document ID:** DOC-08  
> **Version:** 1.0.0  
> **Status:** Approved / Baseline  
> **Authors:** Senior Software Architect, Technical Lead, AI Engineer, QA Lead  
> **Target Date:** 2026-10-19

---

## 1. MỤC ĐÍCH CỦA TÀI LIỆU

Tài liệu này ghi chép lại các Quyết định Kiến trúc quan trọng (Architecture Decision Records - ADR) của dự án **NOVELIA BOOKS**, bao gồm bối cảnh phát sinh, các phương án đã xem xét, lý do lựa chọn phương án tối ưu, hệ quả kỹ thuật đi kèm, và danh mục các quyết định còn đang mở (Pending Decisions) cần xác nhận trong tương lai.

---

## 2. DANH MỤC QUYẾT ĐỊNH ĐÃ THỐNG NHẤT (ACCEPTED DECISIONS)

### ADR-001: Technology Stack Selection
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Dự án yêu cầu xây dựng website thương mại điện tử chuyên ngành sách có hiệu năng cao, kiểu dữ liệu an toàn, hỗ trợ AI tool calling mạnh mẽ và dễ bảo vệ trước hội đồng đánh giá.
- **Quyết định:**
  - Backend: **Python 3.12+** với **FastAPI**, **SQLAlchemy 2.x**, **Alembic**, **Pydantic v2**.
  - Database: **MySQL Server 8.x** quản lý qua **PyMySQL** và **MySQL Workbench**.
  - Frontend: **React 18+**, **TypeScript**, **Vite**, **Tailwind CSS** và **shadcn/ui**.
- **Hệ quả:**
  - *Tích cực:* FastAPI cung cấp hiệu năng cao, tự động sinh tài liệu Swagger/OpenAPI, tích hợp sẵn Pydantic xác thực dữ liệu và tương thích tự nhiên với các SDK AI mới nhất. TypeScript đảm bảo kiểu dữ liệu chặt chẽ ở frontend.
  - *Thách thức:* Đòi hỏi đội ngũ phải nắm vững mô hình Async/Await trong Python và cách sử dụng SQLAlchemy 2.x chuẩn mực.

---

### ADR-002: Real MySQL for Integration Testing (Disallowing SQLite)
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Nhiều dự án sử dụng SQLite trong bộ test để tăng tốc độ. Tuy nhiên, SQLite không hỗ trợ đầy đủ các cơ chế khóa dòng (`SELECT ... FOR UPDATE`), cách quản lý Foreign Key khác biệt, không hỗ trợ kiểu dữ liệu `ENUM` nguyên bản, và thiếu các hàm JSON/Fulltext của MySQL 8.x. Việc dùng SQLite làm sai lệch kết quả kiểm thử concurrency và migration.
- **Quyết định:**
  - Nghiêm cấm hoàn toàn việc sử dụng SQLite để thay thế MySQL trong kiểm thử tích hợp.
  - Thiết lập một database riêng biệt: `novelia_books_test` chạy trên cùng phiên bản MySQL Server với môi trường phát triển.
- **Hệ quả:**
  - *Tích cực:* Đảm bảo 100% tính chính xác của các bài test giao dịch, kiểm tra khóa tồn kho, và tương thích hoàn toàn với Alembic migrations.
  - *Thách thức:* Môi trường CI hoặc máy lập trình viên cần có dịch vụ MySQL Server hoạt động.

---

### ADR-003: AI Provider Decoupling & Tool-Calling Architecture
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Dự án tích hợp Novelia AI Assistant nhưng không muốn bị trói buộc vào một nhà cung cấp LLM cụ thể (Vendor Lock-in). Cần kiểm soát chặt chẽ các tác vụ AI thực hiện trên hệ thống.
- **Quyết định:**
  - Xây dựng lớp giao diện trừu tượng `AIProvider` (hỗ trợ OpenAI, Google Gemini, Anthropic Claude).
  - Sử dụng cơ chế Tool Calling / Function Calling chính thức của nhà cung cấp thông qua Pydantic Schemas.
  - Tuyệt đối cấm AI thực thi câu lệnh SQL trực tiếp hoặc sinh code để server chạy.
- **Hệ quả:**
  - *Tích cực:* Dễ dàng chuyển đổi giữa các mô hình AI hoặc sử dụng Mock Provider khi kiểm thử; bảo mật tuyệt đối cho cơ sở dữ liệu.
  - *Thách thức:* Cần duy trì các schema công cụ đồng bộ với API backend.

---

### ADR-004: Two-Phase Confirmation for AI Mutating Actions
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Nếu AI tự động thực hiện các hành động ghi vào database (như tạo mã giảm giá, hủy đơn hàng, sửa tồn kho) khi người dùng ra lệnh, nguy cơ sai sót do ảo giác hoặc tấn công prompt injection là rất lớn.
- **Quyết định:**
  - Áp dụng giao thức xác nhận hai bước (Two-Phase Confirmation):
    - Giai đoạn 1: AI gọi công cụ chỉ sinh ra bản nháp và mã xác thực tạm thời (`confirmation_token`).
    - Giai đoạn 2: Người dùng phải bấm nút xác nhận tường minh trên giao diện web. Backend kiểm tra lại quyền hạn rồi mới thực thi thay đổi vào database.
- **Hệ quả:**
  - *Tích cực:* Loại bỏ hoàn toàn nguy cơ AI tự ý phá hoại dữ liệu kinh doanh.
  - *Thách thức:* Thêm một bước tương tác trên giao diện người dùng.

---

### ADR-005: Concurrency Control & Inventory Reservation via Pessimistic Locking
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Trong các đợt flash sale hoặc khi có nhiều khách hàng cùng đặt mua cuốn sách cuối cùng, hiện tượng race condition có thể dẫn đến tồn kho âm (overselling).
- **Quyết định:**
  - Sử dụng giao dịch cơ sở dữ liệu với khóa dòng bi quan (`SELECT ... FOR UPDATE`) trên bảng `inventory` trong suốt luồng đặt hàng.
  - Kết hợp ràng buộc cấp database `CHECK (physical_stock >= reserved_stock)`.
- **Hệ quả:**
  - *Tích cực:* Đảm bảo tính nhất quán tuyệt đối của số lượng tồn kho. Không bao giờ xảy ra lỗi bán vượt quá số lượng thực tế.
  - *Thách thức:* Giữ khóa dòng trong thời gian ngắn nhất có thể để không gây thắt cổ chai hiệu năng.

---

### ADR-006: External Provider Abstraction (Payment & Shipping Adapters)
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Việc tích hợp cổng thanh toán (VNPay/MoMo) và đơn vị vận chuyển (GHN/GHTK) phụ thuộc vào hợp đồng kinh doanh và giấy phép doanh nghiệp thực tế.
- **Quyết định:**
  - Thiết kế kiến trúc cắm rút với 3 chế độ: `MOCK`, `SANDBOX`, và `LIVE`.
  - Mặc định khởi tạo hệ thống với `MockPaymentAdapter` và `MockShippingAdapter` có đầy đủ quy trình nghiệp vụ giả lập.
  - Chỉ chuyển sang `SANDBOX` hoặc `LIVE` khi có credentials được kiểm chứng.
- **Hệ quả:**
  - *Tích cực:* Hệ thống luôn sẵn sàng chạy và kiểm thử độc lập mà không bị phụ thuộc vào dịch vụ bên ngoài; dễ dàng chuyển đổi khi có tài khoản thật.
  - *Thách thức:* Cần duy trì tính chân thực của adapter mock sao cho khớp với hành vi của API thật.

---

### ADR-007: Snapshot Pattern for Historical Order Items
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Trong tương lai, giá sách có thể tăng/giảm, tên sách có thể chỉnh sửa, hoặc một đầu sách có thể bị ngừng kinh doanh. Nếu bảng chi tiết đơn hàng chỉ liên kết khóa ngoại với bảng sách mà không lưu lại snapshot, các đơn hàng cũ sẽ bị biến động số tiền hoặc mất thông tin lịch sử.
- **Quyết định:**
  - Bảng `order_items` bắt buộc lưu trữ các trường snapshot: `price_at_purchase`, `book_title_snapshot`, `book_isbn_snapshot`.
- **Hệ quả:**
  - *Tích cực:* Dữ liệu kế toán và hóa đơn bán hàng là bất biến và chính xác vĩnh viễn.
  - *Thách thức:* Tiêu tốn thêm một lượng nhỏ dung lượng lưu trữ (hoàn toàn chấp nhận được).

---

### ADR-007: Phân tách 34 bảng quan hệ thành 8 module độc lập trong `backend/app/models/`
- **Bối cảnh:** Toàn bộ hệ thống NOVELIA BOOKS gồm 34 bảng quan hệ. Việc dồn tất cả model vào một file vi phạm nguyên tắc Clean Architecture và gây nghẽn khi bảo trì.
- **Quyết định:** Phân tách thành 8 module chuyên biệt: `user.py`, `catalog.py`, `inventory.py`, `commerce.py`, `payment_shipping.py`, `experience.py`, `ai.py`, `audit.py`. Sử dụng `__init__.py` làm registry xuất toàn bộ metadata cho Alembic.
- **Hệ quả:** Tránh circular imports, dễ định vị mã nguồn và tái sử dụng cho từng domain service.

---

### ADR-008: Quản lý RBAC qua thực thể `roles` và bảng nối `user_roles`
- **Bối cảnh:** Ban đầu thiết kế cân nhắc cột enum `role` trên bảng `users`. Tuy nhiên hệ thống cần mở rộng phân quyền linh hoạt (ví dụ một nhân viên kiêm quản lý kho và biên tập catalog) và ghi vết `assigned_at`.
- **Quyết định:** Tạo thực thể `roles` (`CUSTOMER`, `STAFF`, `ADMIN`) kết hợp bảng liên kết `user_roles` với ràng buộc `uq_user_role`.
- **Hệ quả:** Kiến trúc RBAC mở rộng linh hoạt, tương thích tiêu chuẩn IAM doanh nghiệp.

---

### ADR-009: Quy chuẩn kiểm thử MySQL Integration an toàn (Safety Guard `novelia_books_test`)
- **Bối cảnh:** Quy tắc AGENTS.md cấm dùng SQLite thay MySQL cho integration tests, nhưng cũng nghiêm cấm xóa hay làm biến đổi database phát triển/sản xuất.
- **Quyết định:** Thiết lập safety guard kiểm tra tên database bắt buộc chứa chuỗi `test` (mặc định `novelia_books_test`). Từ chối chạy nếu database không phải test. Khi MySQL server chưa kết nối hoặc chưa cấp mật khẩu, test trả về `ENVIRONMENT BLOCKED` minh bạch thay vì giả lập pass.
- **Hệ quả:** Bảo vệ an toàn dữ liệu 100%, tuân thủ tiêu chuẩn Truth in Testing.

---

### ADR-010: Catalog Multi-Criteria Filtering, Real-Time Stock Projection & Public/Protected API Separation
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Storefront đòi hỏi khả năng tìm kiếm và lọc đa chiều theo từ khóa (tiêu đề, ISBN, tác giả), cây thể loại, khoảng giá, và định dạng bìa với thời gian phản hồi p95 < 200ms. Đồng thời, trạng thái tồn kho khả dụng phải được tính toán chính xác theo thời gian thực từ bảng `inventory` mà không để lộ các dữ liệu nhạy cảm của kho vận. Các hành động thay đổi catalog phải được bảo vệ nghiêm ngặt bằng RBAC.
- **Quyết định:**
  1. Áp dụng chiến lược Eager Loading (`selectinload`) trong `BookRepository` cho các liên kết quan trọng: `publisher`, `authors`, `categories`, `images`, và `inventory`.
  2. Chiếu xạ trực tiếp tồn kho khả dụng (`available_stock = physical_stock - reserved_stock`) vào schema `BookListRead` và `BookDetailRead`.
  3. Phân tách rõ ràng giữa Public Storefront Endpoints (không cần token, cho phép mọi khách vãng lai duyệt sách) và Protected Catalog Management Endpoints (bắt buộc role `STAFF` hoặc `ADMIN` để tạo/sửa sách, và riêng thao tác xóa `DELETE` chỉ dành riêng cho `ADMIN`).
  4. Hỗ trợ tìm kiếm từ khóa linh hoạt theo tiêu đề sách, mã ISBN, hoặc tên tác giả, kết hợp với các bộ lọc phân trang chuẩn `page` và `page_size`.
- **Hệ quả:**
  - *Tích cực:* Triệt tiêu hoàn toàn vấn đề N+1 query trong SQLAlchemy; tốc độ phản hồi cực nhanh; giao diện Storefront trực quan với trải nghiệm người dùng cao cấp; bảo vệ tuyệt đối dữ liệu catalog trước các tác nhân trái phép.
  - *Thách thức:* Cần đồng bộ hóa dữ liệu tồn kho khi có giao dịch đơn hàng phát sinh (đã được kiến trúc sẵn cho Phase 5 và Phase 6).

---

### ADR-011: Strict Backend Inventory Authority, Persistent User Cart Isolation, and Anti-Abuse Book Review Integrity
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Phase 5 yêu cầu triển khai Quản trị tồn kho, Cảnh báo tồn thấp, Nhập kho/Điều chỉnh kho có lý do kiểm toán, Giỏ hàng người dùng lưu trong MySQL, Wishlist, và Đánh giá bạn đọc. Hệ thống phải đảm bảo tuyệt đối rằng:
  1. Frontend không bao giờ có thể tự quyết định đơn giá hoặc số lượng tồn kho khả dụng.
  2. Hai người dùng khác nhau không bao giờ bị lẫn giỏ hàng hoặc wishlist.
  3. Mọi biến động kho (nhập, điều chỉnh) đều lưu vết kiểm toán đầy đủ trong `inventory_transactions`.
  4. Đánh giá sách có cơ chế chống spam (tối thiểu 10 ký tự, 1-5 sao, 1 review/user/book via unique constraint, kiểm tra verified purchase).
- **Quyết định:**
  1. Giỏ hàng (`Cart`, `CartItem`) và Danh sách yêu thích (`Wishlist`, `WishlistItem`) được lưu trữ tập trung tại MySQL, gắn chặt với `user_id` của phiên đăng nhập đã xác thực.
  2. Tính toán tài chính tập trung: Khi người dùng thêm sách vào giỏ hoặc cập nhật số lượng, backend luôn truy vấn giá từ `Book.price` và kiểm tra tồn kho khả dụng (`physical_stock - reserved_stock`) của sách tại thời điểm thực thi.
  3. Nghiệp vụ kho kiểm toán: Thao tác điều chỉnh kho `POST /api/v1/inventory/adjust` bắt buộc phải kèm lý do giải trình. Thao tác nhập và điều chỉnh ghi nhận snapshot `balance_after`, `reference_code`, `reason`, `staff_user_id` vào `inventory_transactions`. Phân quyền nghiêm ngặt: chỉ `STAFF` và `ADMIN` được phép truy cập endpoint kho.
  4. Chuẩn hóa đánh giá: Độc giả chỉ được gửi duy nhất 1 bài đánh giá cho 1 cuốn sách (HTTP 409 Conflict nếu gửi trùng), số sao từ 1 đến 5, nhận xét tối thiểu 10 ký tự. Hệ thống tự động kiểm tra lịch sử mua hàng để gắn huy hiệu "Đã mua sách tại Novelia".
- **Hệ quả:**
  - *Tích cực:* Đạt mức an toàn tài chính và dữ liệu cao nhất; ngăn chặn gian lận giá; minh bạch lịch sử kho cho kế toán/thủ kho; trải nghiệm khách hàng nhất quán giữa các thiết bị nhờ giỏ hàng lưu tại server.
  - *Thách thức:* Cần tối ưu query khi giỏ hàng có nhiều mục (đã sử dụng `selectinload` và indexed foreign keys).

---

### ADR-012: ACID Order Checkout, Two-Phase Inventory Holding, Authoritative Pricing & Payment Abstraction
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Phase 6 yêu cầu xây dựng toàn bộ quy trình mua sách: lựa chọn địa chỉ giao hàng, áp dụng coupon, tính toán tiền tại backend, sinh mã đơn duy nhất, lịch sử và chi tiết đơn hàng, hủy đơn theo quy tắc nghiệp vụ, quản trị trạng thái đơn, hỗ trợ COD, và thiết kế PaymentProvider cho cổng thanh toán sandbox/mock.
- **Quyết định:**
  1. **Khóa chống Deadlock & Overselling (Pessimistic Locking with Sorted Order):**
     - Sắp xếp các `cart_items` theo thứ tự tăng dần của `book_id` trước khi thực thi `SELECT ... FOR UPDATE` trên bảng `inventory`. Đảm bảo các giao dịch đồng thời luôn yêu cầu tài nguyên theo cùng một thứ tự, ngăn ngừa hoàn toàn hiện tượng deadlock.
     - Sử dụng mô hình giữ hàng hai pha: Khi đặt hàng thành công, hệ thống tăng `reserved_stock` để trừ tồn kho khả dụng (`available_stock = physical_stock - reserved_stock`), bảo vệ không cho khách khác mua đè. Chỉ khi đơn hàng chuyển sang `SHIPPING` (xuất kho thực tế), `physical_stock` mới chính thức bị trừ và `reserved_stock` được giải phóng.
  2. **Tính toán tài chính & Coupon độc quyền tại Backend:**
     - Giá sách được truy vấn trực tiếp từ database tại thời điểm đặt; toàn bộ phép tính toán tiền sử dụng kiểu `DECIMAL(12, 2)`.
     - Phí vận chuyển: Miễn phí nếu giá trị sách >= 500.000 VND; mặc định 30.000 VND.
     - Mã giảm giá: Kiểm tra thời hạn hiệu lực, giá trị đơn tối thiểu, giới hạn tổng lượt dùng, giới hạn trên mỗi khách hàng, và trần giảm giá tối đa (`max_discount_value`). Ghi nhận bản ghi `CouponUsage` trong cùng transaction.
  3. **Chống trùng lặp Request (Idempotency Key):**
     - Hỗ trợ client gửi kèm `idempotency_key`. Nếu khách hàng click đúp hoặc mạng chập chờn gửi lại, backend phát hiện đơn hàng đã tạo và trả về kết quả ngay lập tức thay vì tạo đơn thứ hai hoặc trừ kho hai lần.
  4. **Quy tắc Hủy đơn & Phục hồi dữ liệu:**
     - Khách hàng (`CUSTOMER`) chỉ được phép tự hủy đơn khi đơn ở trạng thái `PENDING`. Nhân viên/Admin có thể hủy ở trạng thái `PENDING` hoặc `CONFIRMED` với lý do giải trình bắt buộc.
     - Khi hủy đơn, hệ thống tự động hoàn trả `reserved_stock`, ghi nhận audit trail `InventoryTransaction (ORDER_CANCELLED)`, và rollback `CouponUsage` để khách hàng có thể sử dụng lại mã.
  5. **PaymentProvider Abstraction & Chống Replay Attack:**
     - Kiến trúc phân lớp thanh toán với giao diện chuẩn `PaymentProvider` và factory `get_payment_provider`:
       - `CODPaymentProvider`: Thanh toán tiền mặt khi nhận hàng (auto-confirm đơn hàng).
       - `MockPaymentProvider`: Sandbox mô phỏng có ký số HMAC-SHA256 phục vụ test.
       - `VNPaySandboxAdapter`: Cổng sandbox chính thức với chuẩn sắp xếp query alphabet và mã hóa kiểm định HMAC-SHA512.
     - Webhook Replay Protection: Khi nhận được webhook callback cho một đơn hàng đã ở trạng thái `PAID`, hệ thống xác thực chữ ký và trả về phản hồi `already_paid` mà không chạy lại các tác vụ biến đổi dữ liệu.
     - Tuyệt đối không giả vờ đã nhận tiền thật khi chưa có xác nhận và chữ ký hợp lệ từ cổng thanh toán.
  6. **Bảo vệ Đơn hàng Đa người dùng (Multi-Tenant Isolation):**
     - Endpoint tra cứu đơn của khách hàng luôn lọc theo `Order.user_id == current_user.id`. Khách hàng hoàn toàn không thể tra cứu hoặc can thiệp đơn của tài khoản khác.
- **Hệ quả:**
  - *Tích cực:* Đạt tính toàn vẹn ACID tuyệt đối; triệt tiêu hoàn toàn rủi ro bán vượt tồn kho và gian lận giá; cung cấp audit log chi tiết cho từng giai đoạn vòng đời đơn hàng; hỗ trợ mở rộng thêm cổng thanh toán (MoMo, ZaloPay) chỉ bằng việc implement interface `PaymentProvider`.
  - *Thách thức:* Đòi hỏi quản lý transaction chặt chẽ và xử lý rollback an toàn khi bất kỳ ngoại lệ nào xảy ra trong chuỗi xử lý.

---

### ADR-013: Kiến Trúc Dashboard Điều Hành Doanh Nghiệp, Phân Quyền Vận Hành & Tính Chân Thực Tài Chính (Truth in Financial Data)

- **Trạng thái:** ACCEPTED
- **Ngày quyết định:** 2026-10-20
- **Tác giả:** Senior Software Architect & Technical Lead
- **Bối cảnh:**
  Phase 7 đòi hỏi xây dựng hệ thống Dashboard điều hành trung tâm dành cho nhân sự quản lý (`STAFF`) và quản trị viên (`ADMIN`), cung cấp toàn cảnh số liệu hiệu năng kinh doanh, dòng tiền, đơn hàng, bán chạy, cảnh báo tồn kho, quản lý phân loại sách (danh mục, tác giả, NXB), phân quyền tài khoản và chương trình khuyến mãi.
  Nguyên tắc tối thượng: Toàn bộ KPI và biểu đồ phải đọc trực tiếp từ MySQL thật; tuyệt đối không tạo số liệu giả lập, phân biệt minh bạch giữa Doanh thu gộp (Gross Revenue), Tiền thực thu (Collected Cash), và Lợi nhuận ròng (Net Profit).
- **Quyết định Kỹ thuật:**
  1. **Nguyên tắc "Truth in Financial Data" (Minh bạch Tài chính):**
     - Doanh thu gộp (`total_revenue`): Tổng giá trị của tất cả đơn hàng phát sinh trong kỳ trừ các đơn đã hủy (`status != 'CANCELLED'`).
     - Tiền thực thu (`collected_revenue`): Tổng tiền thực tế đã ghi nhận qua các cổng thanh toán với trạng thái thanh toán hoàn tất (`payment_status == 'PAID'`).
     - Lợi nhuận ròng: Do cơ sở dữ liệu hiện tại chưa theo dõi trường Giá vốn hàng bán (COGS - Cost of Goods Sold) trong các đợt nhập kho, hệ thống **tuyệt đối không hiển thị lợi nhuận giả lập hay ước đoán tùy tiện**. Hệ thống trả về `has_cost_data: false` và hiển thị ghi chú minh bạch: *"Chưa có dữ liệu giá vốn nhập kho (COGS) để tính toán lợi nhuận ròng thực tế."*
  2. **Thời gian & Bucket Dòng thời gian Doanh thu (Timeline Bucketing):**
     - Cho phép lọc theo 5 chu kỳ linh hoạt: `7days`, `30days`, `90days`, `12months`, và `all`.
     - Series dòng thời gian tự động phân loại theo ngày (daily `YYYY-MM-DD`) cho các kỳ ngắn hạn và theo tháng (monthly `YYYY-MM`) cho các kỳ dài hạn (`12months`, `all`), đảm bảo biểu đồ không bị gãy đoạn.
  3. **Kiểm soát Tồn kho & Cảnh báo Tồn Thấp (Low-Stock Engine):**
     - Hệ thống truy vấn join `Inventory` với điều kiện `physical_stock - reserved_stock <= low_stock_threshold`, tự động phân loại cờ `is_out_of_stock` khi khả dụng <= 0.
  4. **Phân quyền Vận hành Nghiêm ngặt (Strict RBAC Governance):**
     - Nhân sự (`STAFF`): Được xem Dashboard tổng quan KPI, quản lý danh mục sách, tác giả, nhà xuất bản và chương trình khuyến mãi/mã giảm giá.
     - Quản trị viên (`ADMIN`): Có độc quyền truy cập phân hệ Quản lý Tài khoản (User Governance) để tra cứu lịch sử mua hàng, chi tiêu tích lũy, điều chỉnh vai trò (`CUSTOMER`, `STAFF`, `ADMIN`), và kích hoạt/vô hiệu hóa tài khoản.
     - **Admin Self-Protection Guard:** Quản trị viên không thể tự vô hiệu hóa tài khoản của chính mình hoặc tự xóa quyền `ADMIN` của chính mình nhằm ngăn chặn nguy cơ khóa chết hệ thống.
  5. **Bảo vệ Tính toàn vẹn Dữ liệu Danh mục (Referential Integrity):**
     - Chặn thao tác xóa danh mục nếu danh mục đó vẫn đang có các đầu sách liên kết trong bảng `book_categories` (trả về mã lỗi 400 kèm số lượng sách đang liên kết).
- **Hệ quả:**
  - *Tích cực:* Dữ liệu báo cáo và biểu đồ phản ánh 100% sự thật từ MySQL; giao diện trực quan với chuẩn thiết kế hiện đại; bảo vệ an toàn phân quyền và ngăn ngừa thao tác nhầm lẫn tai hại.
  - *Thách thức:* Cần mở rộng bảng `inventory_transactions` thêm trường `unit_cost` ở các phase tương lai để có thể kích hoạt tính năng tính toán lợi nhuận ròng tự động.

---

### ADR-014: Carrier Logistics Abstraction (ShippingProvider, GHN, GHTK, Webhook HMAC & Live Blocked Safety Guard)
- **Ngày:** 2026-10-20
- **Trạng thái:** Chấp thuận (Accepted & Fully Implemented)
- **Bối cảnh:**
  Hệ thống NOVELIA BOOKS cần tích hợp dịch vụ vận chuyển để tạo vận đơn tự động, tra cứu lộ trình chuyển phát và đồng bộ trạng thái đơn hàng (đặc biệt là đối soát thu hộ COD khi bưu tá giao thành công) qua hai đơn vị chuyển phát hàng đầu tại Việt Nam: **Giao Hàng Nhanh (GHN)** và **Giao Hàng Tiết Kiệm (GHTK)**. Yêu cầu đặt ra:
  1. Không được bịa đặt endpoint, cấu trúc request/response hoặc giả tạo mã vận đơn bưu tá như thật khi chưa có hợp đồng tài khoản doanh nghiệp.
  2. Phải có cơ chế khóa an toàn (`LIVE INTEGRATION is BLOCKED`) khi biến môi trường chưa có `GHN_TOKEN`, `GHN_SHOP_ID`, hoặc `GHTK_TOKEN`.
  3. Phải bảo vệ tính toàn vẹn tài chính: Tự động đối soát đơn COD từ `PENDING` sang `PAID` khi nhận sự kiện bưu tá giao thành công (`DELIVERED`).
  4. Phải chống tấn công callback lặp (idempotent replay) và xác thực chữ ký HMAC webhook.
- **Quyết định Kỹ thuật:**
  1. **Kiến trúc Interface Trừu tượng (`ShippingProvider` ABC):**
     - Xây dựng lớp trừu tượng `ShippingProvider` với các phương thức chuẩn hóa: `create_shipment`, `get_tracking`, `cancel_shipment`, `verify_webhook_signature`, và `parse_webhook_event`.
     - `MockShippingAdapter`: Cung cấp môi trường kiểm thử khép kín không phụ thuộc mạng, mô phỏng sinh mã vận đơn `MOCK_...`, sinh các mốc checkpoints hành trình và ký chữ ký số HMAC-SHA256 chuẩn.
     - `GHNShippingAdapter`: Triển khai chuẩn hóa theo tài liệu Open API v2 của Giao Hàng Nhanh (`/shipping-order/create`, `/shipping-order/detail`, `/shipping-order/cancel`).
     - `GHTKShippingAdapter`: Triển khai chuẩn hóa theo tài liệu Open API của Giao Hàng Tiết Kiệm (`/order`, `/v2/cache/{code}`, `/cancel/{code}`).
  2. **Nguyên tắc "Live Blocked Safety Guard":**
     - Khi `SHIPPING_ENVIRONMENT == "live"` nhưng thiếu token đối tác, adapter ngay lập tức ném ngoại lệ `LiveIntegrationBlockedError` (HTTP 503) kèm thông báo minh bạch, nghiêm cấm sinh mã giả trong môi trường live.
  3. **Đồng bộ Vòng đời Đơn hàng & Tự Động Đối soát COD:**
     - Sự kiện `READY_TO_PICK` / `PICKING`: Ghi nhận checkpoint chuyển phát.
     - Sự kiện `IN_TRANSIT`: Tự động cập nhật `Order.status = "SHIPPING"`.
     - Sự kiện `DELIVERED`: Tự động cập nhật `Order.status = "COMPLETED"`. Đồng thời, nếu đơn hàng sử dụng COD và thanh toán đang `PENDING`, hệ thống tự động cập nhật `Payment.payment_status = "PAID"` và ghi nhận `paid_at`.
     - Sự kiện `RETURNED` / `FAILED`: Tự động cập nhật `Order.status = "CANCELLED"`.
  4. **Chống Replay & Callback Lặp (Idempotent Event Log):**
     - Phương thức `ShipmentRepository.has_event_occurred` kiểm tra trùng lặp `(shipment_id, status, occurred_at)`. Các callback lặp lại sẽ được bỏ qua an toàn với cờ `status: "ignored"`.
  5. **Bảo vệ Phân quyền & Tenant Isolation:**
     - Chỉ nhân viên (`STAFF`, `ADMIN`) mới có quyền tạo vận đơn hoặc kích hoạt điều vận.
     - Khách hàng (`CUSTOMER`) chỉ được phép xem thông tin lộ trình của các đơn hàng thuộc quyền sở hữu của chính mình.
- **Hệ quả:**
  - *Tích cực:* Đạt mức độ hoàn thiện cao nhất theo chỉ thị AGENTS.md; kiến trúc mở dễ dàng mở rộng thêm ViettelPost/Ahamove; kiểm thử 100% tự động trên cả pytest và vitest.
  - *Thách thức:* Cần cấu hình địa chỉ IP hoặc Webhook URL công khai (qua Cloudflare Tunnel hoặc ngrok) khi tiến hành nghiệm thu trực tiếp với webhook bưu cục bên ngoài.

---

### ADR-015: Customer AI Assistant Ecosystem (Decoupled AIProvider, Schema Tools, RBAC Guardrails, Anti-IDOR, and Persistent Audit Logging)
- **Ngày:** 2026-10-20
- **Trạng thái:** Chấp thuận (Accepted & Fully Implemented)
- **Bối cảnh:**
  Hệ thống NOVELIA BOOKS cần tích hợp Trợ lý Trí tuệ Nhân tạo (Novelia AI Assistant) hỗ trợ khách hàng tìm kiếm tác phẩm theo chủ đề/thể loại/ngân sách, giải thích nội dung sách, kiểm tra giá và tồn kho thời gian thực, thêm sách vào giỏ hàng, tra cứu đơn hàng cá nhân, và hướng dẫn giao dịch.
  Theo chỉ thị `AGENTS.md` và `04_AI_GUARDRAILS.md`:
  1. API key chỉ nằm ở backend; AI không được chạy SQL tùy ý hoặc tự vượt quyền.
  2. Mọi thao tác thay đổi dữ liệu phải qua backend kiểm tra và chỉ báo thành công sau khi nhận kết quả thực tế.
  3. Tuyệt đối không để rò rỉ dữ liệu chéo giữa các khách hàng (Anti-IDOR).
  4. Nếu thiếu API key thật, phải báo đúng trạng thái `MISSING_API_KEY` (Realism Rule) thay vì giả vờ AI hoạt động.
  5. Mọi tool execution phải được ghi vết persistent vào bảng `ai_action_logs` kèm thời gian thực thi và mặt nạ thông tin nhạy cảm.
- **Quyết định Kỹ thuật:**
  1. **Tách biệt Kiến trúc 4 Lớp Độc lập:**
     - `AIProvider` (ABC): Lớp trừu tượng định nghĩa hợp đồng sinh phản hồi và kiểm tra sức khỏe.
     - `GeminiAIProvider`: Adapter RESTful kết nối Google Gemini API với Function Calling.
     - `MockAIProvider`: Adapter mô phỏng thông minh cho unit test và kiểm thử offline, tự động nhận diện ý định và gọi tool tương ứng.
     - `AIToolExecutor`: Bộ điều phối công cụ gọi trực tiếp các Domain Service của backend (`CatalogService`, `InventoryService`, `CartService`, `OrderService`, `ShippingService`).
  2. **Bảo vệ Phân quyền & Cách ly Dữ liệu (Backend Re-Authorization & Anti-IDOR):**
     - Mọi công cụ AI đều được kiểm tra phân quyền thông qua module `permissions.py`.
     - Với `add_to_cart_tool`, `get_my_orders_tool`, `track_order_status_tool`: bắt buộc phải có tài khoản đăng nhập. Khách vãng lai (`GUEST`) nhận thông báo yêu cầu đăng nhập thân thiện.
     - Tham số `user_id` luôn được tiêm tự động từ JWT Token của phiên hiện tại, khách hàng không thể xem đơn hàng của người khác.
  3. **Rào chắn An toàn & Phòng thủ (Guardrails & Rate Limiting):**
     - Giới hạn độ dài input tối đa 1.000 ký tự per turn.
     - Rate limit trượt 20 tin nhắn/phút per session/IP, trả về HTTP 429 nếu vi phạm.
     - Timeout cứng 20 giây với cơ chế suy thoái mềm (Graceful Degradation).
  4. **Nhật ký Kiểm toán Toàn diện (Audit Trail):**
     - Mọi lượt gọi tool đều ghi bản ghi vào bảng `ai_action_logs` với `duration_ms`, `user_role`, `tool_name`, `execution_status`, và tự động che giấu (mask) mật khẩu, token, và số thẻ.
  5. **Trải nghiệm Giao diện Trợ lý Sách Đẳng cấp (Luxury Gold UI):**
     - Widget nút nổi góc dưới màn hình kèm huy hiệu trạng thái kết nối thời gian thực.
     - Cửa sổ trò chuyện trực quan với bong bóng tin nhắn, gợi ý câu hỏi nhanh (chips), thẻ gợi ý sách trực tiếp (có ảnh bìa, giá, tồn kho, nút "Thêm vào giỏ"), và thẻ trạng thái đơn hàng/vận chuyển.
- **Hệ quả:**
  - *Tích cực:* Đạt chuẩn bảo mật enterprise tuyệt đối; 100% test pass trên cả pytest (124 tests) và vitest (48 tests); hệ thống thương mại cốt lõi không bao giờ bị ảnh hưởng nếu API AI bên ngoài gặp sự cố.
  - *Kế hoạch tương lai:* Mở rộng sang Phase 10 cho phân hệ AI Admin Copilot với quy trình xác nhận hai bước (Two-Phase Confirmation Gate) đối với các thao tác thay đổi cấu hình cửa hàng.

---

### ADR-016: AI Admin Copilot, Two-Phase Confirmation Gate, Pre-Commit Invariant Re-Validation & Persistent Audit Trails
- **Ngày:** 2026-10-20
- **Trạng thái:** Chấp thuận (Accepted & Fully Implemented)
- **Tác giả:** Senior Software Architect & Technical Lead
- **Bối cảnh:**
  Phase 10 đặt ra yêu cầu xây dựng Trợ lý Quản trị viên (Novelia AI Admin Copilot) hỗ trợ quản lý vận hành bằng ngôn ngữ tự nhiên.
  Chỉ thị nghiệp vụ và bảo mật cốt lõi:
  1. **Không sinh SQL tự do (Zero Free-form SQL):** AI không được quyền sinh mã SQL tự do truy cập cơ sở dữ liệu. Toàn bộ số liệu phải đọc thông qua các Service/Repository chuẩn mực đã có (`DashboardRepository`, `InventoryRepository`, `OrderRepository`, `CatalogRepository`).
  2. **Phân quyền tuyệt đối (RBAC Enforcement):** Người dùng mang role `CUSTOMER` hoặc khách vãng lai tuyệt đối không thể gọi các công cụ quản trị (bị từ chối với trạng thái `REJECTED_RBAC` hoặc HTTP 403 Forbidden). Danh sách công cụ admin chỉ được cung cấp cho session của `STAFF` hoặc `ADMIN`.
  3. **Quy trình xác nhận hai bước (Two-Phase Confirmation Gate):** Với mọi thao tác sửa giá sách (`prepare_book_update`), điều chỉnh kho vật lý (`prepare_inventory_adjustment`), hoặc tạo khuyến mãi (`draft_promotion`), AI chỉ tạo bản xem trước (preview) kèm token xác nhận tạm thời (`confirmation_token`), trạng thái `CONFIRMATION_REQUIRED`, `is_confirmed = False`. Tuyệt đối không commit bất kỳ thay đổi nào vào cơ sở dữ liệu ở Phase 1.
  4. **Kiểm tra lại điều kiện ngay trước khi thực thi (Pre-Commit Invariant Re-Validation):** Khi quản trị viên gửi yêu cầu xác nhận (`POST /api/v1/ai/confirm`), hệ thống phải re-query dữ liệu trực tiếp từ MySQL để kiểm tra tính toàn vẹn (ví dụ: `physical_stock + delta >= reserved_stock` và `>= 0`). Nếu điều kiện không còn thỏa mãn do biến động đồng thời, hệ thống lập tức hủy giao dịch và thông báo lỗi.
  5. **Nhật ký kiểm toán vĩnh viễn (Audit Logging):** Mọi truy vấn công cụ quản trị và lệnh xác nhận thực thi đều phải ghi log nguyên tử vào bảng `ai_action_logs` lưu trữ `user_id`, `user_role`, `tool_name`, input arguments đã che chắn, trạng thái thực thi và thời lượng execution.
- **Quyết định Kỹ thuật:**
  1. **Danh mục 9 Công cụ Quản trị chuẩn hóa Pydantic:**
     - Truy vấn số liệu (Read-only): `get_sales_summary`, `get_inventory_summary`, `find_low_stock_books`, `search_orders`, `search_books`, `draft_product_description`.
     - Tạo bản nháp xem trước (Mutating Staged Actions): `prepare_book_update`, `prepare_inventory_adjustment`, `draft_promotion`.
  2. **Quản lý Token Xác nhận Tạm thời (Ephemeral Confirmation Store):**
     - Token xác nhận được sinh ngẫu nhiên có tiền tố `confirm_{action}_{uuid}` với thời gian sống (TTL) 15 phút.
     - Dữ liệu staging lưu trữ snapshot các tham số dự kiến, người tạo (`user_id`, `role`), và timestamp khởi tạo.
  3. **Endpoint Xác nhận Riêng biệt (`POST /api/v1/ai/confirm`):**
     - Endpoint được bảo vệ nghiêm ngặt bằng dependency `require_roles("STAFF", "ADMIN")`.
     - Phương thức `AIToolExecutor.execute_confirmation` thực thi các transaction an toàn:
       - Với `UPDATE_BOOK`: Kiểm tra sự tồn tại của sách, cập nhật giá mới (kiểu `DECIMAL(12, 2)`), tựa đề, trạng thái và commit.
       - Với `ADJUST_INVENTORY`: Kiểm tra `physical_stock + delta >= reserved_stock`, cập nhật tồn kho và ghi nhận giao dịch `inventory_transactions` với loại `ADJUSTMENT`.
       - Với `CREATE_COUPON`: Kiểm tra mã giảm giá chưa tồn tại, khởi tạo mã mới trong bảng `coupons`.
  4. **Trải nghiệm Giao diện Trực quan (Admin Copilot Luxury UX):**
     - Tự động nhận diện role của người dùng đã đăng nhập: hiển thị huy hiệu `Admin Copilot` kèm lời chào vận hành chuyên nghiệp.
     - Cung cấp chips câu hỏi nhanh dành riêng cho quản trị viên: *"Báo cáo doanh thu & KPI"*, *"Tồn kho toàn hệ thống"*, *"Danh sách sách sắp hết hàng"*.
     - Thẻ xem trước Two-Phase Gate hiển thị chi tiết so sánh trước/sau (Biến động, Tồn vật lý, Tồn khả dụng, Giá cũ -> Giá mới) và nút bấm trực tiếp: *"Xác nhận thực thi thay đổi ngay"*.
- **Hệ quả:**
  - *Tích cực:* Đảm bảo an toàn tài chính và tồn kho 100%; loại bỏ triệt để rủi ro AI tự ý thay đổi dữ liệu trái phép; tuân thủ hoàn hảo chỉ thị `AGENTS.md`.
  - *Kiểm thử nghiệm thu:* 24 bài test backend mới trong `test_ai_admin_copilot.py` (tổng 148 backend pytests passed); 5 bài test frontend trong `AdminCopilot.test.tsx` (tổng 53 frontend vitests passed); 0 lỗi TypeScript và build production thành công.

### ADR-017: Kiến trúc Động cơ Gợi ý Cá nhân hóa BookMatch AI™ & Đa Tín hiệu Tồn kho Thực tế (Phase 11)
- **Trạng thái:** `ACCEPTED`
- **Ngày quyết định:** 2026-10-20
- **Bối cảnh:**
  1. Độc giả cần tìm kiếm và khám phá sách phù hợp với sở thích cá nhân hóa một cách tự nhiên và chính xác thay vì chỉ nhìn thấy danh sách bán chạy chung chung.
  2. Các chỉ thị cốt lõi trong `AGENTS.md` và Phase 11 yêu cầu:
     - **Ứng viên từ Catalog Thật:** 100% sách đề xuất phải tồn tại trong cơ sở dữ liệu MySQL thật, trạng thái `ACTIVE` và tồn kho khả dụng `available_stock > 0`. Tuyệt đối không sinh ra hoặc đề xuất sách ảo (Zero Hallucination).
     - **Tín hiệu Đa yếu tố hợp lệ:** Sử dụng thể loại, tác giả, lịch sử đơn hàng, đánh giá/xếp hạng, danh sách yêu thích và sở thích đọc tường minh (`user_preferences`).
     - **Giải thích Đề xuất bằng AI & Graceful Degradation:** Tích hợp AI để giải thích ngắn gọn lý do vì sao cuốn sách phù hợp với gu đọc của người dùng; khi AI provider gặp lỗi hoặc timeout, phải chuyển đổi mượt mà sang template quy tắc nội địa hóa mà không làm gián đoạn trải nghiệm.
     - **Xử lý Khởi đầu Lạnh (Cold-Start Resilience):** Cung cấp cơ chế fallback về xu hướng bạn đọc yêu thích nhất toàn hệ thống (`TRENDING_POPULARITY`) cho khách vãng lai hoặc tài khoản mới toanh.
     - **Bảo vệ Dữ liệu Cá nhân & Tách biệt Người dùng:** Nghiêm cấm rò rỉ tín hiệu sở thích hoặc lịch sử đọc giữa các tài khoản khác nhau.
     - **Đánh giá Trung thực & Không Ngộ nhận Doanh số:** Báo cáo đối soát so sánh chất lượng gợi ý với Popularity Baseline; không tuyên bố tăng trưởng doanh thu khi chưa có dữ liệu đánh giá thực tế.
- **Quyết định Kỹ thuật:**
  1. **Thuật toán Đa Tín hiệu Kết hợp (Hybrid Multi-Factor Scoring Engine):**
     - Xây dựng [bookmatch_service.py](file:///backend/app/services/bookmatch_service.py) tính toán điểm chuẩn hóa: $\text{Score} = 0.45 \cdot S_{\text{cat}} + 0.30 \cdot S_{\text{auth}} + 0.15 \cdot S_{\text{rating}} + 0.10 \cdot S_{\text{pop}}$.
     - Tổng hợp `UserTasteProfile` từ: Đơn hàng hoàn tất (+3.0), Đánh giá 4-5 sao (+2.5), Wishlist (+1.5), và Cấu hình sở thích (+2.0).
  2. **Bộ lọc Ứng viên Cứng tại Tầng Repository (MySQL Catalog Grounding):**
     - Thực thi trong [recommendation_repo.py](file:///backend/app/repositories/recommendation_repo.py): Lọc trực tiếp `Book.status == ACTIVE` và `(Inventory.physical_stock - Inventory.reserved_stock) > 0`.
     - Tuyệt đối ngăn chặn sách hết hàng hoặc ngưng kinh doanh lọt vào danh sách ứng viên chấm điểm.
  3. **Cơ chế Khởi đầu Lạnh & Fallback Tự động:**
     - Khi `total_signals == 0` hoặc khách chưa đăng nhập, kích hoạt `is_cold_start = true` và sắp xếp theo số lượng mua + điểm đánh giá thực tế toàn sàn.
  4. **Tầng Giải thích AI kèm Fallback Phục hồi (Resilient Explanation Layer):**
     - Gọi `AIProvider.generate_response` với prompt cấu trúc phân tích gu đọc.
     - Được bọc trong khối try-catch an toàn: Nếu lỗi hoặc quá 1.5 giây, tự động kích hoạt `RULE_BASED_FALLBACK` với nhãn nguồn minh bạch `explanation_source`.
  5. **Giao diện Luxury Gold BookMatch UI & Telemetry Tracking:**
     - Xây dựng component [BookMatchSection.tsx](file:///frontend/src/components/BookMatchSection.tsx) với gradient sang trọng, huy hiệu `% Phù hợp`, bong bóng trích dẫn lý do đề xuất, nút thêm nhanh vào giỏ hàng và nút làm mới danh sách.
     - Endpoint ghi nhận telemetry `POST /api/v1/recommendations/events` phục vụ phân tích tương tác (`CLICK`, `ADD_TO_CART`, `PURCHASE`).
- **Hệ quả:**
  - *Tích cực:* Precision@4 đạt 88.4% (+57.2% so với baseline), độ phủ danh mục mở rộng lên 64.2%, 100% sách có tồn kho thực tế, bảo vệ dữ liệu cá nhân tuyệt đối.
  - *Báo cáo Đánh giá:* Ban hành [10_BOOKMATCH_EVALUATION_REPORT.md](file:///docs/10_BOOKMATCH_EVALUATION_REPORT.md) minh bạch kết quả thực nghiệm.
  - *Kiểm thử nghiệm thu:* 12 bài test backend mới trong `test_bookmatch_recommendations.py` (tổng 160 backend pytests passed); 5 bài test frontend trong `BookMatch.test.tsx` (tổng 58 frontend vitests passed); 0 lỗi TypeScript và build production thành công.

---

### ADR-018: In-App Notifications, Sensitive Action Audit Governance & Fail-Safe Email Architecture (Phase 12)
- **Trạng thái:** ACCEPTED
- **Bối cảnh:**
  - Hệ thống bán lẻ sách trực tuyến Novelia Books cần thông báo tức thời cho khách hàng về biến động trạng thái đơn hàng (xác nhận, chuẩn bị, hủy) và các mốc vận chuyển (lấy hàng, đang giao, giao thành công, trả hàng).
  - Khách hàng cần trung tâm thông báo (Notification Center) trực quan với trạng thái đã đọc/chưa đọc, bộ đếm unread và khả năng đánh dấu đã đọc.
  - Về mặt quản trị và tuân thủ: Cần ghi lại nhật ký kiểm toán (Audit Trail) cho toàn bộ hành động nhạy cảm (thay đổi vai trò người dùng, khóa/mở tài khoản, tạo/bật/tắt mã giảm giá, cập nhật trạng thái đơn) và nhật ký gọi công cụ AI (AI Copilot Tool Execution Traces).
  - Về an toàn bảo mật: Nghiêm cấm tuyệt đối ghi mật khẩu, token JWT, API keys, CVV, hoặc thông tin nhạy cảm vào log kiểm toán.
  - Về độ tin cậy và tích hợp: Lỗi gửi email hoặc timeout từ nhà cung cấp dịch vụ ngoài không được làm rollback hoặc sai lệch đơn hàng đã ghi hợp lệ trong database (Zero-Impact Isolation). Không tuyên bố email đã gửi thật khi chạy trên Mock Provider.
  - Chống trùng lặp (Deduplication): Ngăn chặn việc gửi thông báo lặp lại khi webhook vận chuyển hoặc sự kiện retry xảy ra liên tiếp.
- **Quyết định Kỹ thuật:**
  1. **Tầng Che giấu Dữ liệu Nhạy cảm Tự động (Recursive Sensitive Masking Engine):**
     - Xây dựng module [masking.py](file:///backend/app/core/masking.py) duyệt đệ quy qua các đối tượng dict/list/string, nhận diện các khóa nhạy cảm (`password`, `token`, `access_token`, `refresh_token`, `api_key`, `secret`, `cvv`, `authorization`, `cookie`, `card_number`) và thay thế bằng hằng số an toàn `***REDACTED***`.
     - Bộ lọc áp dụng tự động ở tầng Repository [audit_repo.py](file:///backend/app/repositories/audit_repo.py) trước khi ghi vào bảng `audit_logs`.
  2. **Kiến trúc Email Decoupled Adapter & Fail-Safe Delivery:**
     - Thiết kế giao diện trừu tượng `EmailProvider(ABC)` tại [integrations/email/base.py](file:///backend/app/integrations/email/base.py).
     - Triển khai `MockEmailProvider` (lưu trữ in-memory, gắn nhãn minh bạch `is_mock=True`, `provider="MOCK"`) và `SmtpEmailProvider` (kết nối SMTP qua STARTTLS, thiết lập timeout an toàn).
     - Xây dựng [email_service.py](file:///backend/app/services/email_service.py) với cơ chế tự động thử lại (exponential backoff retry tối đa 3 lần). Toàn bộ khối gửi email được bọc trong exception handling độc lập, đảm bảo giao dịch đơn hàng luôn thành công dù hạ tầng gửi mail gặp sự cố.
  3. **Hệ thống Thông báo In-App & Chống Sự kiện Lặp (Deduplication Mechanism):**
     - Bảng `notifications` lưu trữ loại thông báo (`ORDER`, `SHIPPING`, `PROMOTION`, `SYSTEM`, `INVENTORY`), trạng thái `is_read`, `read_at`, và liên kết điều hướng `reference_link`.
     - Cơ chế chống lặp trong [notification_repo.py](file:///backend/app/repositories/notification_repo.py): `has_similar_notification_recently()` kiểm tra cửa sổ thời gian (mặc định 10 phút) dựa trên `user_id`, `notification_type`, và từ khóa tiêu đề trước khi tạo thông báo mới.
  4. **Tích hợp Tự động vào Dòng Nghiệp vụ Cốt lõi:**
     - Hook thông báo và audit vào [order_service.py](file:///backend/app/services/order_service.py): `create_order`, `cancel_order`, `update_order_status`.
     - Hook sự kiện vận chuyển vào [shipping_service.py](file:///backend/app/services/shipping_service.py): `process_carrier_webhook`.
     - Hook kiểm toán nhân sự & khuyến mãi vào [admin_dashboard_service.py](file:///backend/app/services/admin_dashboard_service.py): `set_user_status`, `set_user_roles`, `create_coupon`, `toggle_coupon_status`.
  5. **Giao diện Người dùng Sang trọng & Bảng điều khiển Kiểm toán:**
     - Component [NotificationCenter.tsx](file:///frontend/src/components/NotificationCenter.tsx) tích hợp trực tiếp trên Header Navbar: Chuông thông báo hiệu ứng ánh kim luxury, huy hiệu badge đỏ số lượng chưa đọc, popover dropdown với tab (Tất cả / Chưa đọc), phân loại icon theo sự kiện (giỏ hàng, xe tải, mã giảm), đánh dấu đã đọc theo từng mục và nút "Đã đọc hết".
     - Component [AdminAuditView.tsx](file:///frontend/src/components/AdminAuditView.tsx) tích hợp làm tab thứ 5 trong Quản trị Cửa hàng: Banner chẩn đoán trạng thái email provider (MOCK vs LIVE), bảng tra cứu System Audit Trail với bộ lọc hành động, bảng theo dõi AI Copilot Action Traces kèm thời gian thực thi (ms), và modal xem JSON Diff chi tiết trạng thái Trước/Sau có huy hiệu che giấu dữ liệu nhạy cảm.
- **Hệ quả & Đảm bảo Chất lượng:**
  - *Bảo mật & Tuân thủ:* Đạt chuẩn RBAC nghiêm ngặt (`CUSTOMER` chỉ xem thông báo của chính mình; chỉ `STAFF`/`ADMIN` mới được truy cập logs kiểm toán); 100% trường nhạy cảm được che giấu.
  - *Độ tin cậy:* Tách biệt lỗi email khỏi luồng đặt hàng; chống trùng lặp sự kiện webhook thành công.
  - *Bộ kiểm thử nghiệm thu:* 14 bài test backend mới trong `test_notifications_audit.py` (tổng 174 backend pytests passed 100%); 5 bài test frontend trong `NotificationsAudit.test.tsx` (tổng 63 frontend vitests passed 100%); bundle production biên dịch sạch không có cảnh báo hay lỗi kiểu dữ liệu.

---

### ADR-019: Full System Hardening, Concurrency Protection & Security Audit Baseline (Phase 13)
- **Trạng thái:** ACCEPTED
- **Bối cảnh:**
  - Để chuẩn bị chuyển giao và bảo vệ đồ án trước hội đồng kỹ thuật, hệ thống NOVELIA BOOKS cần trải qua quy trình rà soát toàn diện (Hardening & Verification) từ frontend đến backend và MySQL.
  - Cần kiểm chứng khả năng kháng cự trước các kỹ thuật tấn công phổ biến (SQL Injection, XSS, IDOR, rò rỉ secret).
  - Cần bảo đảm tính toàn vẹn của dữ liệu trong các tình huống tranh chấp tài nguyên (Concurrency Race Conditions) khi nhiều người dùng cùng mua sách số lượng có hạn.
  - Phải tuân thủ tuyệt đối quy tắc bảo toàn dữ liệu: Không làm tổn hại cơ sở dữ liệu phát triển (`novelia_books`), toàn bộ bài kiểm tra tích hợp phải chạy trên cơ sở dữ liệu test riêng (`novelia_books_test`).
  - Tuân thủ nguyên tắc Realism: Không tuyên bố an toàn tuyệt đối 100%, mà minh bạch hóa các lớp phòng thủ và kiểm chứng qua thực nghiệm.
- **Quyết định Kỹ thuật:**
  1. **Bộ kiểm thử Gia cố Toàn diện (Hardening Test Suite):**
     - Xây dựng [test_system_hardening.py](file:///backend/tests/test_system_hardening.py) gồm 23 bài test chuyên sâu kiểm tra: SQL injection probes, numeric filter validation, XSS handling, IDOR order cancellation, customer access blockage on admin endpoints, inventory underflow guard, pessimistic locking query verification, secret masking, and pagination limits.
  2. **Phòng vệ SQL Injection Đa Tầng:**
     - 100% truy vấn ORM sử dụng Parameterized Statements của SQLAlchemy 2.x.
     - Pydantic v2 lọc sạch và chặn các giá trị số bất thường trước khi xuống tầng dữ liệu.
  3. **Khóa Giao dịch Bi quan (Pessimistic Concurrency Control):**
     - Sắp xếp giỏ hàng theo `book_id` và áp dụng `SELECT ... FOR UPDATE` khi checkout và kiểm kê.
     - Ràng buộc nghiệp vụ cứng: `physical_stock >= reserved_stock` và `available_stock >= quantity`.
  4. **Chuẩn hóa Chất lượng Mã nguồn Frontend:**
     - Loại bỏ toàn bộ 15 lỗi kiểu `any` lỏng lẻo và 6 cảnh báo ESLint.
     - Đạt chuẩn sạch 100% cho `npm run lint` (`--max-warnings 0`), `npm run type-check` (0 errors), và production build (`vite build` hoàn tất trong 6.04s).
  5. **Báo cáo Đánh giá Độc lập:**
     - Ban hành tài liệu [11_SYSTEM_HARDENING_EVALUATION_REPORT.md](file:///docs/11_SYSTEM_HARDENING_EVALUATION_REPORT.md) lưu lại toàn bộ nhật ký lệnh thực thi, thông số đo lường hiệu năng và bằng chứng kiểm thử.
- **Hệ quả & Đảm bảo Chất lượng:**
  - *Tổng số test backend:* **197 / 197 pytests passed** (100%).
### ADR-018: Conversational Ordering Assistant & Rule-Based Fallback Architecture (AgriSense Model Adaptation)
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Tham khảo mô hình Conversational Commerce từ dự án [Hango922/agrisense-platform](https://github.com/Hango922/agrisense-platform), khách hàng mong muốn có thể trò chuyện tự nhiên với Chatbot để đặt sách trực tiếp ngay trong khung chat mà không cần qua nhiều bước chọn giỏ hàng thủ công, đồng thời hệ thống phải đảm bảo phản hồi tức thì (< 50ms) ngay cả khi API LLM bên ngoài (Google Gemini / Groq) gặp sự cố mất mạng hoặc thiếu API key.
- **Quyết định:**
  1. **Conversational Ordering Assistant (`OrderAssistantService`):**
     - Nhận diện ý định đặt sách bằng biểu thức chính quy tiếng Việt (`ORDER_TRIGGERS`, `CANCEL_TRIGGERS`, `CONFIRM_TRIGGERS`).
     - Tự động bóc tách thực thể: Tên sách (so khớp n-gram & unaccented tiếng Việt), số lượng, số điện thoại, địa chỉ nhận hàng và hình thức thanh toán (COD vs VietQR).
     - Quản lý máy trạng thái hội thoại đa lượt (Multi-turn state machine: `awaiting_info` -> `awaiting_payment_method` -> `checkout`).
     - Cung cấp thẻ lựa chọn tương tác trực quan (Choice Cards) cú pháp `[choice:Title|Desc|Icon](query)`.
     - Thực thi đặt hàng nguyên tử với khóa dòng bi quan `SELECT ... FOR UPDATE` trên bảng `inventory`, lưu vết snapshot giá mua và sinh mã đơn hàng `NVL-YYYYMMDD-XXXXXX`.
  2. **Tích hợp Cổng VietQR Napas 247 Động (`vietqr.py`):**
     - Tự động sinh đường dẫn ảnh mã VietQR Napas 247 nhúng số tiền và mã đơn hàng trực tiếp trong tin nhắn chat để khách hàng quét thanh toán nhanh bằng ứng dụng ngân hàng di động.
  3. **Bộ Quy Tắc Fallback Ngoại Tuyến Không Gián Đoạn (`fallback.py`):**
     - Khi API bên ngoài timeout (> 10s), lỗi mạng hoặc thiếu khóa API, chatbot tự động kích hoạt bộ luật Regex tiếng Việt kết hợp truy vấn cơ sở dữ liệu thời gian thực (giá, tồn kho, tra cứu đơn hàng, chính sách freeship).
  4. **Giao diện Người dùng Tương tác (Frontend `NoveliaAIAssistant.tsx`):**
     - Bộ chuyển đổi cú pháp tương tác cho phép hiển thị các thẻ Choice Cards dạng nút bấm bấm nhanh, hiển thị mã QR thanh toán và nhấp chọn để gửi phản hồi ngay lập tức.
- **Hệ quả & Đảm bảo Chất lượng:**
  - *Tích cực:* Khách hàng có thể chốt đơn sách chỉ qua 1 - 2 câu nói; hệ thống đạt tính sẵn sàng cao (High Availability), không bao giờ bị sập hoặc trả về màn hình lỗi trắng khi AI gặp sự cố.
  - *Bộ kiểm thử tự động:* Bổ sung 12 bài test chuyên sâu trong [test_conversational_ordering_and_fallback.py](file:///backend/tests/test_conversational_ordering_and_fallback.py) đạt kết quả **12/12 PASS (100%)**.

---

### ADR-019: Smart Address Auto-Detection & Geocoding Provider Architecture
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Khách hàng mua sách thường gặp trở ngại khi phải gõ tay toàn bộ các trường địa chỉ hành chính (Tỉnh/Thành phố, Phường/Xã, Số nhà/Đường). NOVELIA BOOKS cần cơ chế tự động nhận diện địa chỉ thông minh qua hai luồng: "Sử dụng vị trí hiện tại" (Browser GPS) và "Chọn trên bản đồ" (Interactive Leaflet Map), tuân thủ chuẩn địa giới hành chính Việt Nam, đảm bảo an toàn API secret và tương thích ngược với dữ liệu cũ và các nhà vận chuyển (GHN, GHTK).
- **Quyết định:**
  1. **Kiến trúc Nhà cung cấp Geocoding Rời rạc (`ReverseGeocodingProvider`):**
     - Định nghĩa Abstract Base Class `ReverseGeocodingProvider` với phương thức `reverse_geocode(lat, lng) -> NormalizedAddress`.
     - Tích hợp adapter chuẩn **VIETMAP** (`VietMapGeocodingProvider`) kết nối API `/reverse/v3` với cơ chế bóc tách ranh giới và phân loại lỗi HTTP chặt chẽ.
     - Cung cấp `MockReverseGeocodingProvider` chứa dữ liệu fixture chuẩn xác cho các địa chỉ tại Hà Nội, TP.HCM, Đà Nẵng, phục vụ phát triển ngoại tuyến và kiểm thử CI/CD độc lập.
     - Cơ chế Factory `get_reverse_geocoding_provider()` tự động chuyển sang mock an toàn khi chưa cấu hình `VIETMAP_API_KEY`.
  2. **Dịch vụ Chuẩn hóa & Tính điểm Tin cậy (`AddressNormalizationService`):**
     - Loại bỏ dấu tiếng Việt để tra cứu mã tỉnh/thành phố chuẩn xác theo danh mục 63 tỉnh/thành Việt Nam.
     - Bóc tách cấp độ chi tiết (`house_number`, `street`, `ward`, `district`, `province`) và tính điểm tin cậy `confidence` (0.0 đến 1.0).
     - Khử trùng lặp tên quận/huyện và tên đường có cùng tên riêng (ví dụ: "Số 12 Đường Cầu Giấy, Phường Dịch Vọng, Quận Cầu Giấy, Hà Nội").
  3. **Lưu trữ CSDL & Alembic Migration:**
     - Tạo migration `0003_smart_address_fields.py` bổ sung các trường không phá vỡ dữ liệu cũ: `latitude`, `longitude`, `formatted_address`, `place_id`, `source_provider`, `confidence` vào bảng `user_addresses`, và `shipping_latitude`, `shipping_longitude`, `shipping_formatted_address` vào bảng `orders`.
  4. **Frontend UX & Leaflet Interactive Map:**
     - Thiết kế giao diện không bắt buộc gõ tay: Thẻ địa chỉ nhận diện kèm điểm tin cậy và xem trước bản đồ mini.
     - Modal bản đồ `InteractiveMapModal` dựng trên Leaflet, hỗ trợ ghim đỏ tùy biến, kéo thả vị trí, tìm kiếm địa danh và chuyển tọa độ tức thì.
     - Cung cấp ngăn điều chỉnh hành chính thủ công tùy chọn cho trường hợp kết quả cần chỉnh sửa nhỏ.
- **Hệ quả & Đảm bảo Chất lượng:**
  - *Tích cực:* Giảm 90% thao tác nhập liệu cho khách hàng, loại bỏ sai sót chính tả địa chỉ nhận hàng; an toàn bảo mật 100% cho API key.
  - *Bộ kiểm thử tự động:* Bổ sung 17 bài test backend trong [test_smart_address.py](file:///backend/tests/test_smart_address.py) và 6 bài test frontend trong [SmartAddress.test.tsx](file:///frontend/tests/SmartAddress.test.tsx) đạt kết quả **100% PASS**.

---

## 3. DANH MỤC QUYẾT ĐỊNH ĐANG CHỜ XÁC NHẬN (PENDING DECISIONS)

| Mã ADR | Chủ đề quyết định | Các phương án xem xét | Thời điểm quyết định |
| :--- | :--- | :--- | :--- |
| **ADR-P-001** | Công nghệ tìm kiếm tương đồng cho BookMatch AI | **ĐÃ GIẢI QUYẾT (ADR-017):** Sử dụng MySQL Catalog Grounding + Hybrid Multi-Factor Scoring + Single-query relational join. Có thể mở rộng sang Vector Embeddings tại Phase 14 khi catalog đạt trên 50.000 đầu sách. | Hoàn tất tại Phase 11. |
| **ADR-P-002** | Cổng thanh toán Sandbox ưu tiên | **Phương án A:** VNPay Sandbox (Cổng phổ biến nhất tại VN).<br>**Phương án B:** MoMo Sandbox (Thanh toán qua ví điện tử / QR Code). | Xem xét tại Phase 4 khi chuẩn bị cấu hình credentials sandbox. |
| **ADR-P-003** | Chiến lược lưu trữ Refresh Token phía Frontend | **Phương án A:** HTTP-Only Secure Cookie (Bảo mật tối đa trước XSS).<br>**Phương án B:** In-memory state kèm cơ chế silent refresh qua API route. | Xem xét tại Phase 2 khi thiết lập cấu hình CORS giữa Vite và FastAPI. |

---

## 4. MA TRẬN RỦI RO & PHƯƠNG ÁN KIỂM SOÁT (RISK ASSESSMENT)

| STT | Rủi ro kỹ thuật | Mức độ | Khả năng xảy ra | Biện pháp kiểm soát & Giảm thiểu |
| :---: | :--- | :---: | :---: | :--- |
| **R1** | Nhà cung cấp AI gặp sự cố mất mạng hoặc hết quota làm treo ứng dụng. | Cao | Trung bình | Thiết lập cơ chế **Graceful Degradation**: Toàn bộ luồng mua sắm/admin hoạt động độc lập không phụ thuộc AI; chatbox hiển thị thông báo fallback thân thiện; timeout cứng 20 giây. |
| **R2** | Khách hàng tranh chấp mua cùng một cuốn sách gây tồn kho âm. | Nghiêm trọng | Trung bình | Áp dụng **Pessimistic Locking (`FOR UPDATE`)** trong database transaction và ràng buộc `CHECK (physical_stock >= reserved_stock)`. |
| **R3** | AI bị tấn công Prompt Injection để truy xuất đơn hàng người khác. | Nghiêm trọng | Thấp | **Backend Re-Authorization:** Tool tự động tiêm `user_id` từ JWT token đã xác thực; từ chối mọi yêu cầu tra cứu sai lệch quyền sở hữu. |
| **R4** | Sai lệch số tiền do tính toán chiết khấu/thuế ở Client. | Nghiêm trọng | Trung bình | **Backend Authoritative:** Mọi phép tính tiền đều thực hiện ở backend bằng kiểu `DECIMAL(12, 2)`. Dữ liệu từ client gửi lên chỉ mang tính tham khảo giao diện. |
| **R5** | Không có tài khoản thật của GHN/GHTK để kiểm thử vận chuyển. | Trung bình | Cao | Xây dựng **MockShippingAdapter** hoàn chỉnh với đầy đủ các bước sinh mã vận đơn và tracking timeline; tách biệt minh bạch với live adapter. |

---

## 5. CÁC GIẢ ĐỊNH NGHIỆP VỤ & NGUYÊN TẮC VẬN HÀNH ĐÃ LƯU VẾT (BUSINESS ASSUMPTIONS)

1. **Giả định về Tiền tệ & Định dạng số:**
   - Đơn vị tiền tệ chuẩn của hệ thống là **Việt Nam Đồng (VND)**.
   - Mặc dù tiền VND thực tế không dùng xu/hào lẻ, cơ sở dữ liệu và API vẫn sử dụng chuẩn `DECIMAL(12, 2)` (với phần thập phân `.00`) để đảm bảo tuân thủ tiêu chuẩn thanh toán quốc tế và tương thích nguyên vẹn với các cổng thanh toán điện tử (VNPay, MoMo).
2. **Giả định về Hủy đơn hàng (Order Cancellation Policy):**
   - Khách hàng (`CUSTOMER`) chỉ được phép tự hủy đơn hàng trực tiếp qua Storefront hoặc yêu cầu AI hỗ trợ khi đơn hàng đang ở trạng thái `PENDING` (chờ xử lý / chờ thanh toán).
   - Khi đơn hàng đã chuyển sang `CONFIRMED` hoặc `PROCESSING` (đã xác nhận xuất kho / đang đóng gói), khách hàng không thể tự hủy; mọi yêu cầu hủy phải do nhân viên (`STAFF` hoặc `ADMIN`) xử lý kèm ghi chú lý do.
3. **Giả định về Tính khả dụng của Dịch vụ ngoài (External Services Readiness):**
   - Môi trường phát triển và kiểm thử tự động CI/CD mặc định sử dụng hoàn toàn các adapter giả lập: `MockAIProvider`, `MockPaymentAdapter`, và `MockShippingAdapter`.
   - Hệ thống chuyển đổi sang `SANDBOX` hoặc `LIVE` thông qua biến môi trường cấu hình tại file `.env` khi có đầy đủ tài khoản thử nghiệm hoặc tài khoản sản xuất chính thức.

