# NOVELIA BOOKS — DATABASE SCHEMA & PERSISTENCE PLAN

> **Document ID:** DOC-03  
> **Version:** 2.0.0 (Synchronized with Phase 2 Implementation)  
> **Status:** Implemented & Verified  
> **Authors:** Senior Software Architect, Technical Lead, AI Engineer, QA Lead  
> **Target Date:** 2026-10-20  
> **Companion References:** [Data Dictionary](file:///docs/database/data_dictionary.md) | [ERD Mermaid Diagram](file:///docs/database/erd.mmd)

---

## 1. PERSISTENCE ENGINE & CORE PRINCIPLES

Hệ thống cơ sở dữ liệu của **NOVELIA BOOKS** sử dụng **MySQL Server 8.x** (InnoDB, `utf8mb4_unicode_ci`) làm nguồn lưu trữ dữ liệu nghiệp vụ chính (Single Source of Truth), tuân thủ các nguyên tắc thiết kế dữ liệu khắt khe:

1. **Chuẩn hóa & Ràng buộc toàn vẹn (ACID & Normalization):**
   - Thiết kế 34 bảng quan hệ chuẩn hóa theo chuẩn 3NF, phân tách thành 8 nhóm miền nghiệp vụ rõ ràng.
   - 100% các quan hệ giữa các bảng được ràng buộc bằng Khóa ngoại (`FOREIGN KEY`) và hành vi bảo vệ (`ON DELETE RESTRICT`, `ON DELETE CASCADE`, hoặc `ON DELETE SET NULL` có chủ đích).
2. **Kiểu dữ liệu tiền tệ chính xác (Zero Precision Loss):**
   - Tuyệt đối không sử dụng `FLOAT` hoặc `DOUBLE` cho giá cả, chiết khấu hoặc doanh thu.
   - Toàn bộ giá tiền, phí vận chuyển và số tiền thanh toán sử dụng kiểu `DECIMAL(12, 2)` kèm `CheckConstraint >= 0`.
3. **Bảo tồn Snapshot lịch sử (Order Snapshotting):**
   - Bảng chi tiết đơn hàng (`order_items`) bắt buộc lưu trữ: `price_at_purchase`, `book_title_snapshot`, `book_isbn_snapshot`, `book_sku_snapshot`.
   - Nếu trong tương lai sách thay đổi giá, đổi tên hoặc bị gỡ khỏi danh mục bán, dữ liệu của các đơn hàng trong quá khứ tuyệt đối không bị biến động hay sai lệch báo cáo kế toán.
4. **Kiểm soát đồng thời & Chống tồn kho âm (Concurrency Control):**
   - Bảng `inventory` chia rõ `physical_stock` và `reserved_stock`. Available stock tính toán động theo `physical_stock - reserved_stock`.
   - Ràng buộc kiểm tra cấp database (`CHECK (physical_stock >= reserved_stock)` và `CHECK (physical_stock >= 0)`) ngăn chặn triệt để tình trạng bán vượt tồn kho (overselling).
   - Mọi biến động tồn kho đều được ghi vết tại bảng `inventory_transactions`.
5. **Môi trường Database tách biệt hoàn toàn:**
   - Database phát triển (Development): `novelia_books`
   - Database kiểm thử (Integration Testing): `novelia_books_test`
   - Tuyệt đối không chạy kiểm thử trên database phát triển; không dùng SQLite để thay thế MySQL trong kiểm thử tích hợp.

---

## 2. TỔNG QUAN 34 BẢNG THEO 8 NHÓM MIỀN

1. **USERS & ACCESS (5 bảng):** `roles`, `users`, `user_roles`, `user_addresses`, `user_preferences`.
2. **CATALOG (7 bảng):** `publishers`, `authors`, `categories`, `books`, `book_authors`, `book_categories`, `book_images`.
3. **INVENTORY (2 bảng):** `inventory`, `inventory_transactions`.
4. **COMMERCE (8 bảng):** `carts`, `cart_items`, `wishlists`, `wishlist_items`, `orders`, `order_items`, `coupons`, `coupon_usages`.
5. **PAYMENT & SHIPPING (4 bảng):** `payments`, `refund_requests`, `shipments`, `shipment_events`.
6. **CUSTOMER EXPERIENCE (2 bảng):** `reviews`, `notifications`.
7. **AI ECOSYSTEM (5 bảng):** `ai_conversations`, `ai_messages`, `ai_action_logs`, `user_book_events`, `book_recommendations`.
8. **SYSTEM AUDITING (1 bảng):** `audit_logs`.

---

## 3. MIGRATION & SEEDING STRATEGY

1. **Alembic Migration Architecture:**
   - Thiết lập cấu hình tại `backend/alembic.ini` và `backend/alembic/env.py`.
   - Migration ban đầu: `backend/alembic/versions/0001_initial_schema.py` chứa đầy đủ logic DDL cho cả `upgrade()` và `downgrade()`.
   - Chuỗi kết nối database được lấy tự động từ `app.core.config.settings.database_url`, không lưu mật khẩu trong `alembic.ini`.
2. **Deterministic & Idempotent Seeding:**
   - File seed: `backend/app/database/seeds.py`.
   - Bao gồm: 3 RBAC roles (`CUSTOMER`, `STAFF`, `ADMIN`), 8 nhà xuất bản, 10 thể loại, 25 tác giả, 35 đầu sách mẫu kèm tồn kho và lịch sử nhập kho ban đầu.
   - Tất cả dữ liệu mô phỏng được gắn thẻ `[DEMO SEED]`.
   - Cơ chế chạy lại an toàn: kiểm tra slug/ISBN trước khi thêm mới, tránh trùng lặp dữ liệu khi chạy lại nhiều lần.
