# NOVELIA BOOKS — PROJECT CHARTER

> **Document ID:** DOC-00  
> **Version:** 1.0.0  
> **Status:** Approved / Baseline  
> **Authors:** Senior Software Architect, Technical Lead, AI Engineer, QA Lead  
> **Target Date:** 2026-10-19

---

## 1. EXECUTIVE SUMMARY & PRODUCT VISION

**NOVELIA BOOKS** là một nền tảng thương mại điện tử chuyên ngành sách trực tuyến toàn diện, hiện đại và bảo mật, kết hợp hệ thống quản trị vận hành bán lẻ và hệ sinh thái trợ lý trí tuệ nhân tạo (AI Assistant) đa chức năng.

Dự án không dừng lại ở mức giao diện trình diễn (landing page / mockup) mà được thiết kế và xây dựng như một hệ thống phần mềm hoàn chỉnh, sẵn sàng phục vụ quy trình kinh doanh thực tế: từ tìm kiếm thông minh, tư vấn cá nhân hóa (BookMatch AI), quản lý giỏ hàng, đặt hàng, xử lý thanh toán, theo dõi vận chuyển thực tế (GHN/GHTK), cho đến phân hệ quản trị (Admin Dashboard) với báo cáo doanh thu chuẩn xác và quản lý kho theo thời gian thực.

Sản phẩm được định vị để đạt tiêu chuẩn cao nhất về tính toàn vẹn dữ liệu, kiến trúc phân lớp rõ ràng, bảo mật đa tầng và sẵn sàng cho việc kiểm thử tự động, bảo vệ đồ án chuyên môn và triển khai sản xuất.

---

## 2. CORE OBJECTIVES (MỤC TIÊU DỰ ÁN)

Hệ thống NOVELIA BOOKS được xây dựng nhằm đạt được 8 mục tiêu cốt lõi:

1. **Trải nghiệm người dùng cao cấp (Modern Storefront):**  
   Xây dựng giao diện bán sách trực tuyến với tính thẩm mỹ cao, hỗ trợ chuyển đổi mượt mà, phản hồi tức thì, tối ưu trên cả desktop và thiết bị di động.

2. **Khép kín quy trình thương mại điện tử (Full E-Commerce Lifecycle):**  
   Hỗ trợ trọn vẹn vòng đời mua sắm: tìm kiếm sách, lọc theo nhiều tiêu chí, xem thông tin chi tiết (tác giả, nhà xuất bản, trích dẫn, đánh giá), quản lý wishlist, giỏ hàng, đặt hàng, xử lý thanh toán và theo dõi hành trình đơn hàng.

3. **Hệ thống quản trị bán lẻ toàn diện (Store & Inventory Management):**  
   Cung cấp phân hệ Admin/Staff mạnh mẽ để quản lý danh mục (sách, tác giả, thể loại, nhà xuất bản), điều phối kho hàng (lịch sử nhập/xuất/điều chỉnh, cảnh báo tồn kho thấp), xử lý đơn hàng, quản lý khách hàng và phân tích báo cáo tài chính.

4. **Tích hợp trợ lý AI thông minh & an toàn (Novelia AI Assistant):**  
   Tích hợp trợ lý AI đàm thoại bằng tiếng Việt, hỗ trợ khách hàng khám phá sách, tra cứu tình trạng kho và đơn hàng theo quyền hạn thông qua cơ chế gọi công cụ (Function Calling / Tool Calling) được kiểm soát chặt chẽ ở backend.

5. **Cá nhân hóa trải nghiệm đọc (BookMatch AI):**  
   Xây dựng thuật toán và luồng đề xuất sách cá nhân hóa dựa trên gu đọc sách, danh mục quan tâm và lịch sử tương tác có sự đồng thuận của người dùng, đi kèm giải thích lý do đề xuất rõ ràng và giải pháp fallback cho người dùng mới (cold-start).

6. **Khả năng tích hợp dịch vụ vận chuyển thực tế (Real Logistics Ready):**  
   Thiết kế kiến trúc mở với lớp adapter kết nối tới các đơn vị vận chuyển thực tế (Giao Hàng Nhanh - GHN, Giao Hàng Tiết Kiệm - GHTK), sẵn sàng hoạt động ngay khi được cấu hình credentials.

7. **Kiến trúc bền vững, dễ bảo trì và kiểm thử (Architectural Excellence):**  
   Tuân thủ nghiêm ngặt mô hình kiến trúc phân lớp (Layered Clean Architecture), tách biệt giữa UI, API, Business Logic, Data Access và External Integrations. Đạt tiêu chuẩn cao nhất để giải trình mã nguồn, trình diễn bảo vệ đồ án và mở rộng tính năng trong tương lai.

8. **Tính toàn vẹn dữ liệu và độ tin cậy tuyệt đối (Data & Financial Consistency):**  
   Tuyệt đối không đánh đổi tính toàn vẹn dữ liệu lấy sự hào nhoáng của giao diện. Toàn bộ logic tính tiền, giảm giá, tồn kho và kiểm tra quyền hạn đều phải do backend làm chủ và bảo vệ bằng giao dịch cơ sở dữ liệu (ACID Transactions).

---

## 3. PROJECT SCOPE (PHẠM VI DỰ ÁN)

### 3.1. Phạm vi thực hiện (In-Scope)
- **Storefront Web App:** Trang chủ, trang danh mục, bộ lọc đa chiều (thể loại, tác giả, khoảng giá, đánh giá), trang chi tiết sách, giỏ hàng, quy trình checkout nhiều bước, quản lý sổ địa chỉ, lịch sử đơn hàng, đánh giá/bình luận đã mua hàng.
- **Authentication & RBAC:** Đăng ký, đăng nhập an toàn với JWT và cookie bảo mật, quản lý phiên làm việc, phân quyền 3 cấp (`CUSTOMER`, `STAFF`, `ADMIN`).
- **Catalog & Inventory Engine:** Quản lý siêu dữ liệu sách (ISBN, SKU, kích thước, số trang, loại bìa), quan hệ nhiều-nhiều với tác giả và danh mục; quản lý tồn kho thời gian thực, lưu vết lịch sử biến động kho và cảnh báo thiếu hàng.
- **Order & Pricing State Machine:** Động cơ tính giá backend, áp dụng mã voucher/khuyến mãi, máy trạng thái đơn hàng (`PENDING` -> `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED` / `CANCELLED`), snapshot giá và thông tin sản phẩm tại thời điểm mua.
- **Payment & Shipping Adapters:** Cung cấp interface chuẩn cho thanh toán (COD, Sandbox VNPay/MoMo) và vận chuyển (Mock Provider, GHN/GHTK Adapter).
- **Admin Management Portal:** Bảng điều khiển KPI trực quan, biểu đồ doanh thu theo thời gian, quản lý danh mục sách, quản lý đơn hàng, kiểm soát kho, quản lý tài khoản người dùng, cấu hình khuyến mãi, nhật ký kiểm toán hệ thống và nhật ký AI.
- **Novelia AI Assistant & BookMatch AI:** Trợ lý ảo AI đàm thoại tự nhiên, tra cứu thông tin sách/kho/đơn hàng qua backend tools, hỗ trợ staff soạn thảo nội dung sách và đề xuất sách cá nhân hóa có lý giải.
- **Automated Testing Suite:** Bộ kiểm thử tự động cho cả backend (Pytest kết nối MySQL thực) và frontend (Vitest + React Testing Library).

### 3.2. Ngoài phạm vi hiện tại (Out-of-Scope)
- Sàn thương mại điện tử đa người bán (Multi-vendor Marketplace).
- Ứng dụng di động native (iOS / Android) — Giao diện web responsive sẽ đóng vai trò phục vụ mobile browser.
- Thanh toán quẹt thẻ tín dụng trực tiếp lưu trữ số thẻ trên server (yêu cầu chứng chỉ PCI-DSS cấp độ cao; dự án sẽ sử dụng redirect gateway hoặc sandbox của bên thứ ba).
- Tự động trừ tiền qua tài khoản ngân hàng không qua cổng trung gian.
- Cho phép AI can thiệp trực tiếp hoặc chạy câu lệnh SQL thô trên cơ sở dữ liệu.

---

## 4. STAKEHOLDERS & USER PERSONAS (ĐỐI TƯỢNG SỬ DỤNG)

| Persona | Vai trò | Trách nhiệm & Quyền hạn | Mục tiêu chính |
| :--- | :--- | :--- | :--- |
| **Khách hàng vãng lai (Guest)** | Người xem | Xem danh mục, đọc thử trích dẫn, tìm kiếm sách, trò chuyện tư vấn với AI ở mức công khai, thêm sách vào giỏ tạm thời. | Khám phá sách nhanh chóng, tìm được sách phù hợp. |
| **Khách hàng thành viên (Customer)** | Người mua | Quản lý thông tin cá nhân, sổ địa chỉ, quản lý giỏ hàng, đặt hàng, thanh toán, xem lịch sử và tiến độ giao hàng, đánh giá sách đã mua, nhận đề xuất từ BookMatch AI. | Mua sách tiện lợi, nhận gợi ý chính xác, theo dõi đơn hàng minh bạch. |
| **Nhân viên cửa hàng (Staff)** | Vận hành | Xem và xử lý đơn hàng, cập nhật trạng thái đóng gói/giao hàng, kiểm kê kho, tạo phiếu nhập/xuất kho, sử dụng AI hỗ trợ viết mô tả sách và tạo bản nháp khuyến mãi. | Xử lý đơn hàng nhanh gọn, quản lý kho chính xác, không nhầm lẫn số lượng. |
| **Quản trị viên (Admin)** | Chủ hệ thống | Toàn quyền quản trị hệ thống: phân quyền nhân viên, quản lý người dùng, xem báo cáo doanh thu tài chính, cấu hình tích hợp, giám sát nhật ký kiểm toán và chi phí AI. | Kiểm soát toàn diện hoạt động kinh doanh, bảo đảm hệ thống vận hành ổn định và bảo mật. |
| **Hội đồng đánh giá / Giảng viên (Evaluator)** | Giám khảo | Kiểm tra kiến trúc hệ thống, đánh giá tính chuẩn mực của mã nguồn, kiểm tra báo cáo kiểm thử, xác thực việc tích hợp AI an toàn và quy trình nghiệp vụ thực tế. | Đánh giá năng lực kỹ thuật, tính hoàn thiện và độ tin cậy của đồ án phần mềm. |

---

## 5. SUCCESS & ACCEPTANCE CRITERIA (TIÊU CHÍ THÀNH CÔNG)

Dự án chỉ được nghiệm thu và công nhận hoàn thành khi thỏa mãn đầy đủ 12 tiêu chí sau:

1. **Khởi chạy độc lập trên môi trường phát triển:** Frontend (Vite) và Backend (FastAPI) khởi chạy trơn tru trên Windows mà không gặp lỗi xung đột môi trường.
2. **Cơ sở dữ liệu thực:** Toàn bộ hệ thống kết nối và vận hành trên MySQL Server thực tế (`novelia_books`), không sử dụng dữ liệu tĩnh giả lập (mock data cứng) trên giao diện.
3. **Migration & Seed nhất quán:** Toàn bộ cấu trúc cơ sở dữ liệu được tạo lập thông qua Alembic migration có phiên bản; dữ liệu mẫu (seed data) phong phú, có nguồn gốc và phản ánh đúng nghiệp vụ sách.
4. **Phân quyền và bảo mật toàn diện:** Cơ chế JWT/Session hoạt động ổn định; mọi endpoint riêng tư ở backend đều kiểm tra quyền hạn chặt chẽ; không có lỗ hổng IDOR (Insecure Direct Object References).
5. **Độ tin cậy giao dịch bán hàng:** Quy trình giỏ hàng -> áp voucher -> tạo đơn hàng -> trừ kho diễn ra nguyên khối trong database transaction; ngăn chặn hoàn toàn tình trạng tồn kho âm hoặc đặt vượt tồn khi có nhiều yêu cầu đồng thời.
6. **Snapshot đơn hàng chuẩn xác:** Mọi thay đổi về giá bán hay thông tin sách sau khi đơn hàng được tạo đều không làm ảnh hưởng đến dữ liệu lịch sử của đơn hàng đã đặt.
7. **Admin Dashboard thời gian thực:** Báo cáo doanh thu, số lượng đơn hàng, sách bán chạy và cảnh báo tồn kho phản ánh đúng 100% số liệu từ database qua API backend.
8. **AI Assistant an toàn & hữu ích:** Trợ lý AI giao tiếp tiếng Việt chuẩn xác, gọi công cụ qua backend API theo đúng quyền của người gọi, có bước xác nhận đối với các thao tác nhạy cảm, không có khả năng thực thi SQL tùy ý.
9. **Cơ chế chịu lỗi AI (Fault Tolerance):** Khi nhà cung cấp AI gặp sự cố mất kết nối hoặc hết quota, toàn bộ các chức năng mua sắm, thanh toán và quản trị cốt lõi của website vẫn hoạt động bình thường mà không bị gián đoạn.
10. **Minh bạch trạng thái tích hợp ngoài:** Hệ thống phân biệt tường minh giữa trạng thái `MOCK`, `SANDBOX` và `LIVE` cho các dịch vụ thanh toán và vận chuyển; không công bố tích hợp thành công nếu chưa vượt qua kiểm thử thực tế.
11. **Kiểm thử tự động có kết quả thực tế:** Bộ kiểm thử Pytest (Backend) và Vitest (Frontend) chạy thành công với báo cáo kiểm thử thực tế, kiểm tra đầy đủ các kịch bản thành công và lỗi ngoại lệ.
12. **Bộ tài liệu kỹ thuật hoàn chỉnh:** Có đầy đủ tài liệu kiến trúc, kế hoạch cơ sở dữ liệu (ERD), rào chắn an toàn AI, chiến lược bảo mật, chiến lược kiểm thử, lộ trình phát triển và nhật ký quyết định kiến trúc (ADR).
