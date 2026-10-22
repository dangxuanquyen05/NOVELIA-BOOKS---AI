# NOVELIA BOOKS — SYSTEM & DOMAIN GLOSSARY

> **Document ID:** DOC-09  
> **Version:** 1.0.0  
> **Status:** Approved / Baseline  
> **Authors:** Senior Software Architect, Technical Lead, AI Engineer, QA Lead  
> **Target Date:** 2026-10-19

---

## 1. THUẬT NGỮ NGHIỆP VỤ (BUSINESS & DOMAIN TERMS)

| Thuật ngữ | Tiếng Anh / Viết tắt | Định nghĩa nghiệp vụ trong hệ thống NOVELIA BOOKS |
| :--- | :--- | :--- |
| **Danh mục sách** | Catalog | Toàn bộ cơ sở dữ liệu các đầu sách, tác giả, nhà xuất bản, và thể loại đang được lưu trữ và kinh doanh tại cửa hàng. |
| **Mã định danh sản phẩm** | SKU (Stock Keeping Unit) | Mã định danh nội bộ duy nhất được cấp cho từng phiên bản sách phục vụ quản lý kho (ví dụ: `NB-BK-00042`). |
| **Mã số tiêu chuẩn quốc tế** | ISBN (International Standard Book Number) | Mã số nhận dạng sách quốc tế duy nhất (ISBN-10 hoặc ISBN-13), dùng để phân biệt chính xác ấn bản sách. |
| **Giá niêm yết / Giá gốc** | Original Price / List Price | Giá bìa của cuốn sách do nhà xuất bản quy định trước khi áp dụng bất kỳ chương trình chiết khấu nào. |
| **Giá bán thực tế** | Selling Price | Giá hiện tại đang bán trên website sau khi đã trừ các chương trình giảm giá định kỳ của cửa hàng. |
| **Snapshot giá đơn hàng** | Snapshot Price | Bản ghi đóng băng đơn giá và thông tin sách tại đúng thời điểm khách hàng đặt mua; không bao giờ bị biến động khi sách đổi giá sau đó. |
| **Tồn kho vật lý** | Physical Stock | Số lượng sách thực tế đang nằm trên kệ trong kho hàng của NOVELIA BOOKS. |
| **Tồn kho giữ chỗ** | Reserved Stock | Số lượng sách đang được giữ lại cho các đơn hàng vừa được tạo (chờ thanh toán hoặc đang trong quá trình đóng gói). |
| **Tồn kho khả dụng** | Available Stock | Số lượng sách thực sự có thể bán cho khách hàng mới (`Available = Physical - Reserved`). Nếu giá trị này bằng 0, sách hiển thị trạng thái "Hết hàng". |
| **Điều chỉnh tồn kho** | Inventory Adjustment | Hành động nghiệp vụ của nhân viên kho làm thay đổi số lượng tồn kho (do nhập hàng, xuất hàng, phát hiện hư hỏng, hoặc kiểm kê sai lệch), bắt buộc ghi vết vào nhật ký kho. |
| **Máy trạng thái đơn hàng** | Order State Machine | Mô hình quản lý vòng đời đơn hàng qua các trạng thái nghiêm ngặt: `PENDING` -> `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED` / `CANCELLED`. |
| **Thanh toán khi nhận hàng** | COD (Cash on Delivery) | Phương thức thanh toán mà người mua chỉ trả tiền mặt cho nhân viên giao hàng sau khi nhận và kiểm tra kiện hàng. |
| **Mã vận đơn** | Tracking Code | Chuỗi ký tự duy nhất do đơn vị vận chuyển (GHN/GHTK) cấp để định danh và theo dõi hành trình của kiện hàng. |
| **Sự kiện vận chuyển** | Shipment Event | Một mốc thời gian ghi nhận thay đổi vị trí hoặc trạng thái của kiện hàng (ví dụ: "Đã lấy hàng", "Đang trung chuyển tại kho Tân Bình", "Đang giao"). |
| **Giá trị đơn hàng trung bình**| AOV (Average Order Value) | Chỉ số kinh doanh đo lường số tiền trung bình một khách hàng chi trả cho mỗi đơn hàng (`Tổng doanh thu / Tổng số đơn hàng`). |
| **Vấn đề người dùng mới** | Cold-Start Problem | Hiện tượng hệ thống gợi ý (BookMatch AI) chưa có đủ dữ liệu lịch sử về một khách hàng mới để đưa ra đề xuất cá nhân hóa, đòi hỏi phải kích hoạt cơ chế fallback (sách bán chạy / sách nổi bật). |

---

## 2. THUẬT NGỮ KỸ THUẬT (TECHNICAL & ARCHITECTURAL TERMS)

| Thuật ngữ | Tiếng Anh / Viết tắt | Định nghĩa kỹ thuật trong hệ thống NOVELIA BOOKS |
| :--- | :--- | :--- |
| **Kiểm soát truy cập dựa trên vai trò** | RBAC (Role-Based Access Control) | Cơ chế phân quyền hệ thống dựa trên vai trò của người dùng (`CUSTOMER`, `STAFF`, `ADMIN`), kiểm tra bắt buộc tại backend thông qua dependency injection. |
| **JSON Web Token** | JWT | Tiêu chuẩn mở (RFC 7519) định nghĩa phương thức an toàn để truyền thông tin xác thực giữa máy khách và máy chủ dưới dạng đối tượng JSON có chữ ký số. |
| **Xoay vòng Refresh Token** | Refresh Token Rotation (RTR) | Kỹ thuật bảo mật mà mỗi lần Refresh Token được sử dụng để lấy Access Token mới, nó sẽ lập tức bị hủy và thay thế bằng một token mới nhằm chống tấn công phát lại (Replay Attack). |
| **Migration cơ sở dữ liệu** | Database Migration (Alembic) | Việc quản lý và theo dõi các thay đổi về cấu trúc bảng (schema) theo các phiên bản mã nguồn có thể nâng cấp (`upgrade`) hoặc hạ cấp (`downgrade`) một cách an toàn. |
| **Lược đồ dữ liệu Pydantic** | Pydantic Schema | Lớp định nghĩa cấu trúc dữ liệu trong Python có khả năng tự động xác thực kiểu dữ liệu (Type Validation), làm sạch và chuẩn hóa dữ liệu trước khi xử lý. |
| **Gọi công cụ AI** | Tool Calling / Function Calling | Tính năng của mô hình LLM cho phép nó phát hiện khi nào cần gọi một hàm nội bộ của backend, trích xuất tham số có cấu trúc và nhận kết quả trả về từ backend để trả lời người dùng. |
| **Tấn công tiêm chỉ thị AI** | Prompt Injection | Hình thức tấn công mà kẻ xấu đưa các chỉ thị văn bản độc hại vào câu hỏi nhằm đánh lừa AI bỏ qua các quy tắc hệ thống, tiết lộ bí mật hoặc thực hiện hành động trái quyền. |
| **Cơ chế suy thoái mềm** | Graceful Degradation | Khả năng duy trì hoạt động của các chức năng chính (mua sách, thanh toán, quản lý kho) khi một thành phần phụ trợ (như AI Provider) gặp sự cố ngừng hoạt động. |
| **Giao thức xác nhận hai bước** | Two-Phase Confirmation | Cơ chế an toàn yêu cầu người dùng phải xác nhận tường minh một hành động thay đổi dữ liệu do AI đề xuất thông qua giao diện trước khi backend thực thi. |
| **Tính bất biến & Toàn vẹn giao dịch** | ACID (Atomicity, Consistency, Isolation, Durability) | Bộ 4 tính chất bảo đảm rằng các giao dịch trên MySQL Server được xử lý một cách đáng tin cậy: Đơn hàng thành công thì mọi bảng liên quan đều cập nhật, nếu có lỗi thì hoàn tác nguyên trạng. |
| **Khóa bi quan** | Pessimistic Locking (`FOR UPDATE`) | Kỹ thuật khóa dòng dữ liệu trong cơ sở dữ liệu để ngăn các giao dịch khác đọc hoặc sửa đổi dòng đó cho đến khi giao dịch hiện tại hoàn tất, dùng để chống tồn kho âm. |
| **Lỗ hổng tham chiếu trực tiếp** | IDOR (Insecure Direct Object References) | Lỗ hổng bảo mật xảy ra khi ứng dụng cho phép người dùng truy cập tài nguyên của người khác chỉ bằng cách thay đổi mã định danh trong tham số URL mà không kiểm tra quyền sở hữu. |
| **Tính lũy kế / Bất biến** | Idempotency | Thuộc tính của một thao tác mà dù có thực hiện một lần hay nhiều lần liên tiếp với cùng dữ liệu đầu vào thì kết quả trên hệ thống vẫn không thay đổi (quan trọng khi nhận Webhook thanh toán). |
| **Chế độ Giả lập / Thử nghiệm / Thực tế** | Mock / Sandbox / Live | Ba môi trường hoạt động của các adapter tích hợp: `Mock` (tự sinh dữ liệu nội bộ phục vụ unit test), `Sandbox` (kết nối cổng test của bên thứ ba), `Live` (môi trường sản xuất thực tế). |
