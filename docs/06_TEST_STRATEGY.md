# NOVELIA BOOKS — QUALITY ASSURANCE & TEST STRATEGY

> **Document ID:** DOC-06  
> **Version:** 1.0.0  
> **Status:** Approved / Baseline  
> **Authors:** Senior Software Architect, Technical Lead, AI Engineer, QA Lead  
> **Target Date:** 2026-10-19

---

## 1. TẦM NHÌN CHẤT LƯỢNG & KIM TỰ THÁP KIỂM THỬ (TESTING PYRAMID)

Chất lượng của hệ thống **NOVELIA BOOKS** được bảo đảm bằng phương pháp tiếp cận có cấu trúc, chặt chẽ và có thể kiểm chứng được. Dự án tuân thủ mô hình Kim tự tháp kiểm thử chuẩn mực:

```
               / \
              /   \      E2E & Integration Tests (15%)
             / E2E \     - Kết nối MySQL Server thật (novelia_books_test)
            /-------\    - Luồng Đặt hàng -> Trừ kho -> Thanh toán
           /         \   
          /  API Test \  API & Component Tests (35%)
         /-------------\ - FastAPI TestClient (HTTP Status, Auth, Validation)
        /               \- Vitest + React Testing Library (Form, States, UI)
       /    Unit Tests   \ Unit Tests (50%)
      /-------------------\ - Pure Python Services, Pricing Logic, State Machine
     /                     \- AI Tool RBAC, Pydantic Schema Validation
```

### Nguyên tắc vàng của QA Lead:
1. **Sự thật trong kiểm thử (Truth in Testing):** Tuyệt đối không bao giờ báo cáo `PASS` nếu chưa thực sự chạy câu lệnh kiểm thử và kiểm tra kết quả trả về.
2. **Minh bạch lỗi (Transparent Bug Reporting):** Mọi lỗi (bug) phát hiện được chưa thể giải quyết ngay phải được ghi chép tường minh kèm các bước tái hiện (Reproduction Steps) và mức độ nghiêm trọng.
3. **Môi trường cách ly (Isolated Test Environment):** Toàn bộ kiểm thử tích hợp backend chạy trên database `novelia_books_test`. Không được phép làm biến đổi dữ liệu trên database phát triển `novelia_books`.

---

## 2. BACKEND TESTING STRATEGY (CHIẾN LƯỢC KIỂM THỬ BACKEND)

Công cụ sử dụng: **Pytest**, **Pytest-Asyncio**, **HTTPX (FastAPI TestClient)**.

### 2.1. Unit Tests (Kiểm thử đơn vị)
- **Mục tiêu:** Kiểm tra các hàm nghiệp vụ thuần túy, không phụ thuộc vào kết nối mạng hay cơ sở dữ liệu.
- **Phạm vi:**
  - Logic tính toán giá, tỷ lệ chiết khấu, giá trị đơn hàng sau khi áp dụng voucher.
  - Kiểm tra tính hợp lệ của việc chuyển đổi trạng thái đơn hàng (Order State Machine).
  - Kiểm tra bộ phân giải tham số và xác thực Pydantic Schemas.
  - Mock tầng Repository để kiểm tra logic xử lý trong Service.

### 2.2. API / Route Tests (Kiểm thử giao diện lập trình)
- **Mục tiêu:** Kiểm tra giao thức HTTP, mã phản hồi (Status Code), xác thực quyền hạn và xử lý ngoại lệ.
- **Kịch bản bắt buộc:**
  - `401 Unauthorized` khi không truyền Bearer Token hoặc token hết hạn.
  - `403 Forbidden` khi tài khoản `CUSTOMER` cố gọi API của `STAFF` hoặc `ADMIN`.
  - `422 Unprocessable Entity` khi dữ liệu đầu vào không thỏa mãn schema Pydantic.
  - `200/201 OK/Created` khi dữ liệu hợp lệ và quyền hạn đầy đủ.

### 2.3. Database Integration Tests (Kiểm thử tích hợp với MySQL thực tế)
- **Quy tắc bắt buộc:** **TUYỆT ĐỐI KHÔNG DÙNG SQLITE** để thay thế MySQL cho kiểm thử tích hợp. SQLite có sự khác biệt lớn về cơ chế locking, hỗ trợ kiểu dữ liệu JSON, ENUM, và cách hoạt động của Foreign Key.
- **Quy trình thực thi:**
  1. Pytest fixture tự động áp dụng Alembic migrations lên database `novelia_books_test`.
  2. Mỗi bài kiểm thử chạy trong một Database Transaction độc lập và tự động `ROLLBACK` sau khi kiểm thử kết thúc để giữ sạch dữ liệu.
  3. Kiểm tra các kịch bản tương tranh (Concurrency): Mô phỏng 2 tiến trình đồng thời đặt mua cuốn sách cuối cùng trong kho; xác nhận chỉ 1 đơn hàng thành công, đơn hàng còn lại nhận thông báo hết hàng, và trường `available_stock` không bao giờ bị âm.

---

## 3. FRONTEND TESTING STRATEGY (CHIẾN LƯỢC KIỂM THỬ FRONTEND)

Công cụ sử dụng: **Vitest**, **React Testing Library**, **jsdom**.

### 3.1. Component & Hook Tests
- Kiểm thử các component quan trọng:
  - `BookCard`: Hiển thị đúng giá gốc, giá khuyến mãi, nhãn hết hàng.
  - `CartDrawer`: Cập nhật số lượng sách, tính tổng tiền tạm tính.
  - `CheckoutForm`: Kiểm tra tính hợp lệ của số điện thoại, địa chỉ nhận hàng.
  - `AIChatWidget`: Trạng thái gửi tin nhắn, hiển thị loading spinner, hiển thị thẻ xác nhận (Confirmation Card).
- Kiểm thử custom hooks: `useAuth`, `useCart`.

### 3.2. Kiểm thử 4 trạng thái giao diện (The 4 UI States)
Mọi trang và component tải dữ liệu đều phải được kiểm thử cho đủ 4 trạng thái:
1. **Loading State:** Hiển thị skeleton hoặc spinner khi đang fetch dữ liệu.
2. **Error State:** Hiển thị thông báo lỗi rõ ràng kèm nút thử lại khi API trả về mã lỗi 4xx/5xx.
3. **Empty State:** Hiển thị giao diện thân thiện khi không có dữ liệu (ví dụ: Giỏ hàng trống, Không tìm thấy sách phù hợp).
4. **Success State:** Hiển thị dữ liệu hoàn chỉnh, tương tác mượt mà.

### 3.3. Static Analysis & Build Verification
- Chạy kiểm tra kiểu tĩnh: `npm run type-check` (`tsc --noEmit`).
- Chạy kiểm tra đóng gói: `npm run build` để bảo đảm không có lỗi cú pháp hoặc import file sai sót trước khi triển khai.

---

## 4. AI TESTING STRATEGY (CHIẾN LƯỢC KIỂM THỬ PHÂN HỆ AI)

Do tính chất ngẫu nhiên của mô hình ngôn ngữ lớn (LLM), kiểm thử AI được chia thành hai nhóm riêng biệt:

### 4.1. Deterministic Mock Provider Tests (Kiểm thử giả lập tất định - Chạy trong CI)
- Sử dụng `MockAIProvider` để trả về các tool call payload định trước.
- **Kịch bản kiểm thử:**
  - Kiểm tra việc chọn đúng công cụ dựa trên ngữ cảnh người dùng.
  - Kiểm tra việc bắt lỗi sai tham số gọi công cụ (`tool_arguments`).
  - Kiểm tra việc backend từ chối gọi tool nếu tài khoản không đủ quyền (RBAC Test).
  - Kiểm tra luồng xác nhận hai bước (Confirmation Flow): Đảm bảo các công cụ thay đổi dữ liệu trả về token xác nhận và không tự ý ghi vào database.
  - Kiểm tra việc ghi bản ghi đầy đủ vào `ai_audit_logs`.
  - Kiểm tra hành vi Timeout: Giả lập LLM phản hồi chậm hơn 20 giây; xác nhận hệ thống ngắt kết nối an toàn và trả về fallback message.

### 4.2. Live Provider Integration Tests (Kiểm thử nhà cung cấp thực tế - Chạy thủ công có điều kiện)
- Chỉ chạy khi có biến môi trường `AI_API_KEY` hợp lệ.
- Kiểm tra tính tương thích của System Prompt và chất lượng đàm thoại tiếng Việt với API thực tế của OpenAI / Gemini.
- Báo cáo kết quả kiểm thử bắt buộc phải ghi rõ: *Kết quả từ Mock Provider* hay *Kết quả từ Live API Provider*.

---

## 5. EXTERNAL INTEGRATION TESTING (KIỂM THỬ DỊCH VỤ BÊN NGOÀI)

| Dịch vụ | Chế độ Mock (Mặc định trong Test) | Chế độ Sandbox | Chế độ Live (Sản xuất) |
| :--- | :--- | :--- | :--- |
| **Thanh toán (VNPay / MoMo)** | `MockPaymentAdapter`: Giả lập URL thanh toán, tự sinh callback IPN hợp lệ và chữ ký số chuẩn. | Kết nối đến môi trường Sandbox chính thức của cổng thanh toán bằng tài khoản test. | Chỉ bật khi ký hợp đồng chính thức và có Merchant ID / Private Key production. |
| **Vận chuyển (GHN / GHTK)** | `MockShippingAdapter`: Trả về phí ship giả lập theo cân nặng, sinh mã vận đơn `MOCK-GHN-xxxx` và chuỗi hành trình mẫu. | Kết nối API Sandbox của đơn vị vận chuyển với ShopID thử nghiệm. | Chỉ kích hoạt khi có hợp đồng dịch vụ vận chuyển thực tế. |

---

## 6. QUY CÁCH BÁO CÁO LỖI (DEFECT REPORTING TEMPLATE)

Khi phát hiện lỗi trong quá trình kiểm thử, báo cáo lỗi phải tuân thủ mẫu chuẩn:

```markdown
### [DEFECT-XXX] Tên ngắn gọn mô tả lỗi
- **Phân hệ:** (Storefront / Order / Inventory / AI / Admin)
- **Mức độ nghiêm trọng:** (Critical / Major / Minor / Trivial)
- **Môi trường:** OS: Windows, Python 3.12, Node 20, MySQL 8.0
- **Các bước tái hiện (Steps to Reproduce):**
  1. Bước 1...
  2. Bước 2...
  3. Bước 3...
- **Kết quả thực tế (Actual Result):** (Mô tả chi tiết kèm mã lỗi / log / ảnh chụp màn hình)
- **Kết quả mong đợi (Expected Result):** (Hệ thống phải phản hồi như thế nào)
- **Nguyên nhân cốt lõi dự kiến (Root Cause Analysis):**
- **Đề xuất khắc phục (Proposed Fix):**
```
