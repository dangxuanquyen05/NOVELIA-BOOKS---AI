# NOVELIA BOOKS — TÀI LIỆU VẬN HÀNH, SAO LƯU (BACKUP) & KHÔI PHỤC (RESTORE)

> **Document ID:** DOC-13 / OPS-BACKUP  
> **Classification:** Production Operations & Disaster Recovery Guide  
> **Status:** APPROVED & VERIFIED  
> **Operating System:** Windows 10 / 11 (PowerShell)  
> **Database:** MySQL Server 8.x (InnoDB, utf8mb4)

---

## 1. CHIẾN LƯỢC SAO LƯU DỮ LIỆU (BACKUP STRATEGY)

Để đảm bảo an toàn tuyệt đối cho cơ sở dữ liệu thương mại điện tử **NOVELIA BOOKS** (chứa thông tin tài chính, đơn hàng, người dùng và nhật ký kiểm toán), hệ thống áp dụng chiến lược sao lưu định kỳ qua công cụ chuẩn `mysqldump`.

### 1.1. Sao lưu Toàn phần Cơ sở dữ liệu (Full Database Backup)
Mở **Windows PowerShell** và thực thi:

```powershell
# Tạo thư mục chứa file backup
$BackupDir = "c:\Users\dangx\OneDrive\Desktop\NOVELIA BOOKS\NOVELIA BOOKS - AI\database_backups"
New-Item -ItemType Directory -Force -Path $BackupDir

# Tạo tên file theo mốc thời gian UTC (YYYYMMDD_HHMMSS)
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupDir\novelia_books_full_$Timestamp.sql"

# Thực thi lệnh mysqldump (Thay đổi 'root' và password nếu cần)
mysqldump -u root -p `
  --default-character-set=utf8mb4 `
  --single-transaction `
  --quick `
  --routines `
  --triggers `
  novelia_books > $BackupFile

Write-Host "Sao lưu hoàn tất: $BackupFile" -ForegroundColor Green
```

### 1.2. Sao lưu Cấu trúc Schema (Schema Only — Không chứa dữ liệu)
Phục vụ đối chiếu migration hoặc tạo môi trường mới:
```powershell
mysqldump -u root -p --no-data --default-character-set=utf8mb4 novelia_books > "$BackupDir\novelia_schema_$Timestamp.sql"
```

### 1.3. Sao lưu Riêng Dữ liệu Bảng Giao dịch (Transactional Data Only)
Sao lưu các bảng biến động lớn: `orders`, `order_items`, `payments`, `shipments`, `audit_logs`:
```powershell
mysqldump -u root -p --no-create-info --default-character-set=utf8mb4 novelia_books `
  orders order_items payments shipments inventory_transactions audit_logs > "$BackupDir\novelia_transactions_$Timestamp.sql"
```

---

## 2. QUY TRÌNH PHỤC HỒI DỮ LIỆU (DISASTER RECOVERY / RESTORE)

Khi gặp sự cố hỏng hóc hoặc cần hoàn nguyên dữ liệu về mốc thời gian an toàn:

### Bước 2.1: Tạo mới Database đích sạch
Mở MySQL Command Line hoặc MySQL Workbench:
```sql
DROP DATABASE IF EXISTS novelia_books;
CREATE DATABASE novelia_books CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Bước 2.2: Nạp dữ liệu từ tệp sao lưu (Restore)
Trong Windows PowerShell:
```powershell
$RestoreFile = "c:\Users\dangx\OneDrive\Desktop\NOVELIA BOOKS\NOVELIA BOOKS - AI\database_backups\novelia_books_full_20261020_xxxxxx.sql"

# Khôi phục dữ liệu qua command mysql
mysql -u root -p --default-character-set=utf8mb4 novelia_books < $RestoreFile

Write-Host "Phục hồi cơ sở dữ liệu thành công!" -ForegroundColor Green
```

### Bước 2.3: Kiểm tra tính toàn vẹn sau khi khôi phục
Chạy script kiểm tra số lượng bản ghi:
```sql
USE novelia_books;
SELECT COUNT(*) AS total_users FROM users;
SELECT COUNT(*) AS total_books FROM books;
SELECT COUNT(*) AS total_orders FROM orders;
```

---

## 3. QUẢN LÝ MIGRATION & CHIẾN LƯỢC ROLLBACK (ALEMBIC)

Toàn bộ lược đồ cơ sở dữ liệu được quản lý phiên bản qua Alembic trong thư mục `backend/alembic/`.

### 3.1. Nâng cấp lên phiên bản mới nhất
```powershell
cd "c:\Users\dangx\OneDrive\Desktop\NOVELIA BOOKS\NOVELIA BOOKS - AI\backend"
.\.venv\Scripts\alembic.exe upgrade head
```

### 3.2. Kiểm tra phiên bản hiện tại của Database
```powershell
.\.venv\Scripts\alembic.exe current
```

### 3.3. Quy trình Rollback khi Migration gặp lỗi
Nếu một migration mới phát sinh lỗi, hoàn nguyên về revision liền trước:
```powershell
# Hoàn nguyên 1 bước revision
.\.venv\Scripts\alembic.exe downgrade -1

# Hoàn nguyên về phiên bản cơ sở ban đầu (Clean slate)
.\.venv\Scripts\alembic.exe downgrade base
```

---

## 4. MA TRẬN CHUYỂN ĐỔI MÔI TRƯỜNG (MOCK vs SANDBOX vs LIVE)

Hệ thống NOVELIA BOOKS được kiến trúc hóa để chuyển đổi linh hoạt qua file biến môi trường `backend/.env`:

| Phân hệ tích hợp | Môi trường Mock (Mặc định) | Môi trường Sandbox | Môi trường Live Production |
| :--- | :--- | :--- | :--- |
| **Trợ lý AI (LLM)** | `AI_PROVIDER=mock`<br>(Phản hồi nhanh in-memory) | `AI_PROVIDER=gemini`<br>`GEMINI_API_KEY=AIzaSy...`<br>`GEMINI_MODEL=gemini-1.5-flash` | `AI_PROVIDER=gemini`<br>`GEMINI_API_KEY=ProductionKey`<br>`AI_TIMEOUT_SECONDS=20` |
| **Cổng Giao vận** | `SHIPPING_ENVIRONMENT=mock`<br>(Sinh mã vận đơn và tracking giả lập) | `SHIPPING_ENVIRONMENT=sandbox`<br>`GHN_TOKEN=TestToken`<br>`GHN_SHOP_ID=12345` | `SHIPPING_ENVIRONMENT=live`<br>`GHN_TOKEN=LiveProductionToken`<br>`DEFAULT_SHIPPING_CARRIER=GHN` |
| **Cổng Thanh toán** | `PAYMENT_ENVIRONMENT=mock`<br>(Ký chữ ký HMAC giả lập) | `PAYMENT_ENVIRONMENT=sandbox`<br>`VNPAY_TMN_CODE=TEST_CODE`<br>`VNPAY_HASH_SECRET=Secret` | `PAYMENT_ENVIRONMENT=live`<br>`VNPAY_TMN_CODE=LiveMerchant`<br>`VNPAY_HASH_SECRET=LiveSecret` |
| **Dịch vụ Email** | `EMAIL_PROVIDER=mock`<br>(Lưu email trong bộ nhớ, `is_mock=True`) | `EMAIL_PROVIDER=smtp`<br>`SMTP_HOST=smtp.mailtrap.io`<br>`SMTP_PORT=2525` | `EMAIL_PROVIDER=smtp`<br>`SMTP_HOST=smtp.gmail.com`<br>`SMTP_PORT=587`<br>`SMTP_USER=...` |

---

## 5. BẢO TRÌ VÀ GIÁM SÁT HỆ THỐNG ĐỊNH KỲ

1. **Rà soát Log Kiểm toán:** Định kỳ hàng tuần kiểm tra bảng `audit_logs` để phát hiện các hoạt động bất thường (thay đổi vai trò người dùng, điều chỉnh kho số lượng lớn).
2. **Kiểm tra Token Thu hồi (Blacklist):** Dọn dẹp các token hết hạn trong cơ chế blacklist để tối ưu dung lượng bộ nhớ.
3. **Giám sát Dung lượng Ổ đĩa MySQL:** Đảm bảo thư mục lưu trữ dữ liệu MySQL (`C:\ProgramData\MySQL\MySQL Server 8.0\Data`) còn tối thiểu 20% dung lượng trống.
