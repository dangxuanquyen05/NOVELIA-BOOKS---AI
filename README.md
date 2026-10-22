# NOVELIA BOOKS — PRODUCTION BOOKSTORE & AI ECOSYSTEM PLATFORM

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.111-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/Frontend-React_18_TypeScript-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![MySQL](https://img.shields.io/badge/Database-MySQL_8.x_InnoDB-4479A1.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Alembic](https://img.shields.io/badge/Migrations-Alembic-orange.svg)](https://alembic.sqlalchemy.org/)
[![Vitest](https://img.shields.io/badge/Frontend_Tests-63%2F63_PASS-brightgreen.svg?logo=vitest&logoColor=white)](https://vitest.dev/)
[![Pytest](https://img.shields.io/badge/Backend_Tests-197%2F197_PASS-brightgreen.svg?logo=pytest&logoColor=white)](https://pytest.org/)
[![License](https://img.shields.io/badge/Status-100%25_Completed_Phase_14-gold.svg)]()

> **Đồ án Tốt nghiệp / Production Project:** Hệ thống Bán lẻ Sách Trực tuyến Cao cấp tích hợp Trợ lý Trí tuệ Nhân tạo Đa tầng (Customer AI Assistant, AI Admin Copilot, BookMatch Personalized Recommendations).  
> **Chỉ thị Kỹ thuật Tối cao:** [AGENTS.md](file:///AGENTS.md)  
> **Hệ điều hành Khuyến nghị:** Windows 10 / 11 (PowerShell)

---

## 1. TỔNG QUAN HỆ THỐNG (SYSTEM OVERVIEW)

**NOVELIA BOOKS** là một nền tảng thương mại điện tử chuyên ngành sách hoàn chỉnh, được thiết kế theo tiêu chuẩn công nghiệp (Enterprise Architecture) với 14 phân hệ chuyên sâu:

- **Storefront & Catalog:** Danh mục sách đa tiêu chí (Thể loại, Tác giả, Nhà xuất bản, Khoảng giá, Định dạng bìa), tìm kiếm Full-Text và xem trước nội dung sách (Excerpt Reader).
- **Inventory & Cart:** Quản trị tồn kho khả dụng thời gian thực (`physical_stock - reserved_stock`), cảnh báo hết hàng, nhập kho định kỳ kèm lý do kiểm toán, giỏ hàng phân lập người dùng và danh sách yêu thích (Wishlist).
- **Checkout & Financial Authority:** Quy trình thanh toán nhiều bước, tính toán tài chính hoàn toàn tại backend bằng kiểu `DECIMAL(12, 2)`, mã đơn duy nhất `NVL-YYYYMMDD-XXXXXX`, và lưu vết bất biến các dòng sản phẩm (`OrderItemSnapshot`).
- **Logistics & Payment:** Trừu tượng hóa đối tác vận chuyển ([ShippingProvider](file:///backend/app/integrations/shipping/base.py) — GHN Open API v2, GHTK, Mock) và đối tác thanh toán ([PaymentProvider](file:///backend/app/integrations/payment/base.py) — COD, VNPay Sandbox HMAC-SHA512, Mock).
- **Customer AI Assistant (Novelia AI):** Chatbox giao diện nổi luxury hỗ trợ tìm sách theo chủ đề, tra cứu tồn kho, hướng dẫn checkout và tra cứu đơn hàng cá nhân (chống IDOR).
- **AI Admin Copilot:** Trợ lý ngôn ngữ tự nhiên cho nhà quản trị cửa hàng với 9 công cụ nghiệp vụ, áp dụng cổng kiểm soát xác nhận hai bước (**Two-Phase Confirmation Gate**) ngăn chặn phá hoại dữ liệu.
- **BookMatch Recommendations:** Thuật toán chấm điểm đa nhân tố kết hợp ($0.45 S_{cat} + 0.30 S_{auth} + 0.15 S_{rating} + 0.10 S_{pop}$), nối kết danh mục MySQL thật (Stock > 0), kèm cơ chế AI giải thích gu đọc và fallback khởi đầu lạnh.
- **Notifications & Audit:** Trung tâm thông báo in-app với huy hiệu chưa đọc, gửi email an toàn không chặn giao dịch (Fail-Safe), tự động che giấu dữ liệu nhạy cảm (`***REDACTED***`), và nhật ký kiểm toán hệ thống.

---

## 2. YÊU CẦU PHẦN MỀM HỆ THỐNG TRÊN WINDOWS

Trước khi khởi động dự án, máy tính cần cài đặt sẵn:
- **Hệ điều hành:** Windows 10/11 (64-bit).
- **Python:** Phiên bản 3.11+ (kiểm tra bằng `python --version`).
- **Node.js:** Phiên bản 20+ hoặc 22+ LTS (kiểm tra bằng `node -v` và `npm -v`).
- **MySQL Server:** Phiên bản 8.0+ đang hoạt động trên cổng mặc định `localhost:3306`.
- **MySQL Workbench:** Để kết nối, tạo database và kiểm tra dữ liệu.

---

## 3. THIẾT LẬP CƠ SỞ DỮ LIỆU MYSQL (WORKBENCH / CLI)

Mở **MySQL Workbench** hoặc **Windows PowerShell**, kết nối MySQL và chạy kịch bản tạo hai database độc lập:

```sql
-- 1. Tạo Database phát triển chính thức
CREATE DATABASE IF NOT EXISTS novelia_books
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 2. Tạo Database kiểm thử biệt lập (Tuyệt đối không dùng SQLite)
CREATE DATABASE IF NOT EXISTS novelia_books_test
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 3. (Tùy chọn) Cấp quyền cho user ứng dụng
CREATE USER IF NOT EXISTS 'novelia_app'@'localhost' IDENTIFIED BY 'NoveliaSecurePass2026!';
GRANT ALL PRIVILEGES ON novelia_books.* TO 'novelia_app'@'localhost';
GRANT ALL PRIVILEGES ON novelia_books_test.* TO 'novelia_app'@'localhost';
FLUSH PRIVILEGES;

-- 4. Xác nhận cơ sở dữ liệu đã sẵn sàng
SHOW DATABASES LIKE 'novelia_%';
```

---

## 4. HƯỚNG DẪN CÀI ĐẶT TỪNG BƯỚC TRÊN WINDOWS (POWERSHELL)

### Bước 4.1: Cấu hình và Khởi động Backend (FastAPI)

Mở cửa sổ **PowerShell thứ nhất**:

```powershell
# 1. Di chuyển vào thư mục backend
cd "c:\Users\dangx\OneDrive\Desktop\NOVELIA BOOKS\NOVELIA BOOKS - AI\backend"

# 2. Khởi tạo môi trường ảo Python (nếu chưa có)
python -m venv .venv

# 3. Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# 4. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# 5. Khởi tạo file biến môi trường .env từ mẫu chuẩn
Copy-Item .env.example .env

# Chỉnh sửa file .env: Cập nhật DB_USER và DB_PASSWORD tương ứng với MySQL Server của bạn:
# DB_USER=root
# DB_PASSWORD=your_mysql_password

# 6. Chạy Migration Alembic để khởi tạo 34 bảng dữ liệu
alembic upgrade head

# 7. Nạp dữ liệu mẫu có nhãn chuẩn (Idempotent Seed Data)
.\.venv\Scripts\python.exe -m app.database.seeds

# 8. Khởi chạy máy chủ Backend Uvicorn
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
> Khi khởi động thành công, Backend sẽ hoạt động tại: `http://127.0.0.1:8000`  
> Tài liệu tương tác Swagger UI: `http://127.0.0.1:8000/docs`

---

### Bước 4.2: Cấu hình và Khởi động Frontend (React 18 + Vite)

Mở cửa sổ **PowerShell thứ hai**:

```powershell
# 1. Di chuyển vào thư mục frontend
cd "c:\Users\dangx\OneDrive\Desktop\NOVELIA BOOKS\NOVELIA BOOKS - AI\frontend"

# 2. Cài đặt các gói phụ thuộc Node.js
npm install

# 3. Khởi tạo file biến môi trường .env (nếu chưa có)
Copy-Item .env.example .env

# 4. Kiểm tra kiểu dữ liệu tĩnh và linting
npm run lint
npm run type-check

# 5. Khởi chạy máy chủ phát triển Frontend
npm run dev
```
> Khi khởi động thành công, giao diện ứng dụng sẽ hoạt động tại: `http://localhost:5173`

---

## 5. TÀI KHOẢN THỬ NGHIỆM ĐÃ NẠP SẴN (DEMO CREDENTIALS)

Hệ thống đã chuẩn bị sẵn 3 cấp độ tài khoản mẫu với đầy đủ lịch sử giao dịch và phân quyền RBAC:

| Vai trò (Role) | Email đăng nhập | Mật khẩu | Phạm vi quyền hạn & Luồng Demo |
| :---: | :--- | :--- | :--- |
| **`ADMIN`** | `admin@novelia.vn` | `AdminPass123!` | Quyền tối cao: Xem KPI doanh thu, quản lý danh mục (Category, Author, Publisher), phân quyền tài khoản, bật/tắt khuyến mãi, kiểm toán và giám sát AI Copilot. |
| **`STAFF`** | `staff@novelia.vn` | `StaffPass123!` | Nhân viên cửa hàng: Quản lý kho sách, xuất nhập kho có lý do kiểm toán, chuyển trạng thái đơn hàng, tương tác AI Admin Copilot với cổng xác nhận 2 bước. |
| **`CUSTOMER`** | `reader@novelia.vn` | `ReaderPass123!` | Bạn đọc thân thiết: Tìm sách, nhận đề xuất BookMatch AI cá nhân hóa theo gu đọc, đặt hàng, hủy đơn PENDING, nhận thông báo in-app. |

---

## 6. HƯỚNG DẪN CHẠY BỘ KIỂM THỬ TOÀN HỆ THỐNG

### 6.1. Kiểm thử Backend (Pytest Suite — 197 Tests)
```powershell
cd "c:\Users\dangx\OneDrive\Desktop\NOVELIA BOOKS\NOVELIA BOOKS - AI\backend"
.\.venv\Scripts\python.exe -m pytest -v
```
*Kết quả:* **197 / 197 passed** trong ~7 giây. Bao gồm:
- 16 test Catalog & Multi-Criteria Filtering
- 13 test Inventory, Cart & Reviews
- 10 test Orders & Checkout ACID
- 13 test Shipping & Carrier Webhooks
- 15 test Customer AI Assistant
- 24 test AI Admin Copilot
- 12 test BookMatch Recommendations
- 14 test Notifications & Audit Governance
- 6 test Real MySQL Integration (`novelia_books_test`)
- 23 test System Hardening & Security (SQLi, XSS, Concurrency, IDOR)

### 6.2. Kiểm thử Frontend (Vitest Suite — 63 Tests)
```powershell
cd "c:\Users\dangx\OneDrive\Desktop\NOVELIA BOOKS\NOVELIA BOOKS - AI\frontend"
npm test -- --run
```
*Kết quả:* **63 / 63 passed** trong ~11 giây trên 11 test suites.

### 6.3. Kiểm thử Đóng gói Sản xuất (Production Build)
```powershell
npm run build
```
*Kết quả:* Biên dịch hoàn tất trong ~6 giây. Bundle tối ưu (CSS: 83 kB, JS: 417 kB) đạt 0 lỗi TypeScript và 0 cảnh báo ESLint.

---

## 7. CẤU TRÚC THƯ MỤC TÀI LIỆU KỸ THUẬT (`docs/`)

| Tên tài liệu | Nội dung chi tiết |
| :--- | :--- |
| [AGENTS.md](file:///AGENTS.md) | Chỉ thị kỹ thuật tối cao: RBAC, ACID, Two-Phase Confirmation, Realism Rule. |
| [00_PROJECT_CHARTER.md](file:///docs/00_PROJECT_CHARTER.md) | Tuyên ngôn dự án, mục tiêu kinh doanh và phạm vi phân hệ. |
| [01_REQUIREMENTS.md](file:///docs/01_REQUIREMENTS.md) | Yêu cầu chức năng (FR) và phi chức năng (NFR) chuẩn đồ án. |
| [02_ARCHITECTURE.md](file:///docs/02_ARCHITECTURE.md) | Kiến trúc phân tầng (Router $\rightarrow$ Service $\rightarrow$ Repository $\rightarrow$ Model). |
| [03_DATABASE_PLAN.md](file:///docs/03_DATABASE_PLAN.md) | Chiến lược phân vùng, lập chỉ mục và kết nối cơ sở dữ liệu. |
| [04_AI_GUARDRAILS.md](file:///docs/04_AI_GUARDRAILS.md) | Hàng rào bảo vệ AI: Tool calling Pydantic, rate limit, timeout, chống injection. |
| [05_SECURITY.md](file:///docs/05_SECURITY.md) | Tiêu chuẩn mã hóa, quản lý JWT token, chống IDOR, và che giấu dữ liệu nhạy cảm. |
| [06_TEST_STRATEGY.md](file:///docs/06_TEST_STRATEGY.md) | Chiến lược kiểm thử tự động kim tự tháp (Unit, Integration, Component, E2E). |
| [07_PHASE_ROADMAP.md](file:///docs/07_PHASE_ROADMAP.md) | Lộ trình triển khai 14 giai đoạn từ nền tảng đến nghiệm thu. |
| [08_ARCHITECTURE_DECISIONS.md](file:///docs/08_ARCHITECTURE_DECISIONS.md) | Toàn bộ 19 Architecture Decision Records (ADR-001 đến ADR-019). |
| [09_GLOSSARY.md](file:///docs/09_GLOSSARY.md) | Từ điển thuật ngữ kỹ thuật và nghiệp vụ xuất bản sách. |
| [09_SHIPPING_INTEGRATION_GUIDE.md](file:///docs/09_SHIPPING_INTEGRATION_GUIDE.md) | Hướng dẫn tích hợp đối tác vận chuyển GHN và GHTK. |
| [10_BOOKMATCH_EVALUATION_REPORT.md](file:///docs/10_BOOKMATCH_EVALUATION_REPORT.md) | Báo cáo đánh giá thực nghiệm BookMatch AI vs Popularity Baseline. |
| [11_SYSTEM_HARDENING_EVALUATION_REPORT.md](file:///docs/11_SYSTEM_HARDENING_EVALUATION_REPORT.md) | Báo cáo kiểm thử tải, kiểm toán bảo mật và gia cố giao dịch Phase 13. |
| [12_DEMO_SCRIPT_AND_DEFENSE_QA.md](file:///docs/12_DEMO_SCRIPT_AND_DEFENSE_QA.md) | Kịch bản trình diễn trực tiếp và bộ câu hỏi bảo vệ đồ án tốt nghiệp. |
| [13_OPERATIONS_BACKUP_AND_RESTORE.md](file:///docs/13_OPERATIONS_BACKUP_AND_RESTORE.md) | Hướng dẫn vận hành sao lưu, khôi phục dữ liệu và xử lý sự cố. |
| [IMPLEMENTATION_STATUS.md](file:///docs/IMPLEMENTATION_STATUS.md) | Bảng theo dõi tiến độ tổng thể 14 Phase nghiệm thu hoàn tất. |
| [data_dictionary.md](file:///docs/database/data_dictionary.md) | Từ điển dữ liệu chi tiết cho toàn bộ 34 bảng cơ sở dữ liệu. |
| [erd.mmd](file:///docs/database/erd.mmd) | Sơ đồ thực thể quan hệ Entity Relationship Diagram (ERD). |

---

## 8. GIẤY PHÉP & TÁC QUYỀN

Dự án được phát triển phục vụ công tác đào tạo và bảo vệ đồ án tốt nghiệp chuyên ngành Kỹ thuật Phần mềm / Công nghệ Thông tin. Mọi quyền tác quyền thuộc về nhóm phát triển **NOVELIA BOOKS**.
