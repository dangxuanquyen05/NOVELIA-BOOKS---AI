# NOVELIA BOOKS — SECURITY ARCHITECTURE & DATA PROTECTION SPECIFICATION

> **Document ID:** DOC-05  
> **Version:** 1.0.0  
> **Status:** Approved / Baseline  
> **Authors:** Senior Software Architect, Technical Lead, AI Engineer, QA Lead  
> **Target Date:** 2026-10-19

---

## 1. MỤC TIÊU & NGUYÊN TẮC BẢO MẬT CỐT LÕI

Hệ thống **NOVELIA BOOKS** coi an toàn thông tin và bảo vệ quyền riêng tư của khách hàng là ưu tiên hàng đầu. Kiến trúc bảo mật được thiết kế tuân theo khung tiêu chuẩn **OWASP Top 10** và nguyên tắc **Zero Trust** (Không bao giờ tin tưởng, luôn luôn xác thực).

1. **Nguyên tắc đặc quyền tối thiểu (Least Privilege):** Mỗi người dùng, dịch vụ, và công cụ AI chỉ được cấp quyền hạn tối thiểu vừa đủ để hoàn thành chức năng được giao.
2. **Không tin tưởng dữ liệu từ Client (Never Trust Client Data):** Toàn bộ dữ liệu gửi từ trình duyệt (giá, vai trò, số lượng tồn kho, mã giảm giá, định danh người dùng) đều phải được xác thực và tính toán lại ở backend.
3. **Phòng vệ theo chiều sâu (Defense in Depth):** Bảo vệ nhiều lớp độc lập: từ cấu hình mạng, tường lửa ứng dụng (WAF), mã hóa truyền tải (TLS/HTTPS), kiểm soát phiên làm việc, phân quyền API cho đến ràng buộc toàn vẹn cơ sở dữ liệu.

---

## 2. XÁC THỰC & QUẢN LÝ PHIÊN LÀM VIỆC (AUTHENTICATION & SESSION)

### 2.1. Quản lý Mật khẩu & Băm mật khẩu (Password Hashing)
- Mật khẩu người dùng được băm bằng thuật toán **Argon2id** (hoặc **bcrypt** với salt rounds tối thiểu là 12).
- Tuyệt đối không lưu trữ mật khẩu ở dạng rõ (plain text) hoặc sử dụng các hàm băm lỗi thời (MD5, SHA1).
- Chính sách mật khẩu: Tối thiểu 8 ký tự, bao gồm ít nhất 1 chữ hoa, 1 chữ thường, 1 chữ số và 1 ký tự đặc biệt.

### 2.2. Cơ chế Token (JWT & Refresh Token Rotation)
- **Access Token:**
  - Định dạng: JSON Web Token (JWT) ký bằng thuật toán HMAC-SHA256 (`HS256`) hoặc RSA (`RS256`).
  - Thời hạn ngắn: **15 đến 30 phút** để hạn chế rủi ro lộ token.
  - Payload: Chứa `sub` (User ID), `email`, `role`, và thời hạn `exp`. Tuyệt đối không chứa mật khẩu hoặc dữ liệu nhạy cảm trong payload.
- **Refresh Token:**
  - Sử dụng chuỗi ngẫu nhiên có độ dài entropy cao (Cryptographically Secure Pseudo-Random Number Generator - CSPRNG).
  - Lưu trữ dưới dạng băm trong bảng `refresh_tokens`.
  - Cơ chế **Refresh Token Rotation (RTR):** Mỗi lần cấp phát Access Token mới, Refresh Token cũ sẽ bị vô hiệu hóa và một Refresh Token mới được sinh ra. Nếu một Refresh Token đã thu hồi bị sử dụng lại, hệ thống lập tức hủy toàn bộ phiên làm việc của người dùng đó (phát hiện tấn công đánh cắp token).
- **Lưu trữ an toàn tại Client:**
  - Khuyến nghị lưu trữ Refresh Token trong **HTTP-Only, Secure, SameSite=Lax** Cookie để ngăn chặn 100% việc mã độc JavaScript (XSS) đánh cắp phiên đăng nhập.

---

## 3. PHÂN QUYỀN TRUY CẬP (AUTHORIZATION & RBAC)

### 3.1. Phân quyền cấp độ API (FastAPI Dependency Injection)
Mọi API riêng tư đều được bảo vệ bởi chuỗi kiểm tra độc lập tại backend:

```python
# app/api/deps.py
async def get_current_active_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Xác thực token, kiểm tra tài khoản còn hoạt động trong DB."""
    payload = verify_jwt_token(token)
    user = user_repo.get_by_id(db, payload.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Tài khoản không hợp lệ hoặc đã bị khóa.")
    return user

def require_roles(allowed_roles: list[UserRole]):
    """Kiểm tra quyền hạn bắt buộc theo vai trò."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập tài nguyên này.")
        return current_user
    return role_checker
```

### 3.2. Phòng chống lỗ hổng IDOR (Insecure Direct Object References)
- Khi người dùng truy vấn tài nguyên (ví dụ: `GET /api/v1/orders/{order_id}`):
  - Backend **luôn luôn** kiểm tra điều kiện sở hữu: `order.user_id == current_user.id`.
  - Chỉ người dùng có vai trò `STAFF` hoặc `ADMIN` mới được phép bỏ qua điều kiện sở hữu này để xem đơn hàng của khách hàng khác.

---

## 4. BẢO VỆ CHỐNG TẤN CÔNG ĐẦU VÀO (INPUT VALIDATION & INJECTION DEFENSE)

### 4.1. Chống tấn công SQL Injection
- 100% các câu truy vấn cơ sở dữ liệu được thực thi thông qua **SQLAlchemy 2.x ORM / Core** với cơ chế tham số hóa tự động (Parameterized Queries).
- Nghiêm cấm hoàn toàn việc nối chuỗi thô để tạo câu lệnh SQL (String Concatenation).

### 4.2. Chống tấn công XSS (Cross-Site Scripting)
- **Frontend React:** Tận dụng cơ chế tự động escape mã HTML của JSX.
- **Dữ liệu đánh giá & Bình luận:** Lọc và loại bỏ mã HTML độc hại bằng thư viện chuẩn hóa (như DOMPurify hoặc bleach ở backend) trước khi lưu trữ hoặc hiển thị.
- Thiết lập Content Security Policy (CSP) chặt chẽ trên HTTP response headers.

### 4.3. Xác thực cấu trúc dữ liệu với Pydantic v2
- Mọi dữ liệu đầu vào (Body, Query Params, Path Params) đều bắt buộc phải định nghĩa schema Pydantic với các ràng buộc kiểu dữ liệu, độ dài và regex rõ ràng.
- FastAPI tự động từ chối mọi yêu cầu không đúng định dạng với mã lỗi `422 Unprocessable Entity` trước khi dữ liệu tiếp cận tầng Service.

---

## 5. QUẢN LÝ BÍ MẬT & CẤU HÌNH (SECRETS MANAGEMENT)

1. **Quản lý biến môi trường an toàn:**
   - Sử dụng thư viện `pydantic-settings` để nạp cấu hình từ file `.env` kèm xác thực kiểu dữ liệu.
   - File `.env` chứa mật khẩu database, khóa bí mật JWT, và API key của AI Provider **BẮT BUỘC** phải được đưa vào `.gitignore`.
2. **File cấu hình mẫu (`.env.example`):**
   - Cung cấp file `.env.example` chứa toàn bộ tên các biến môi trường cần thiết kèm mô tả chi tiết, nhưng chỉ để giá trị mặc định hoặc dữ liệu giả lập (dummy).
3. **Tuyệt đối không hardcode bí mật:**
   - Không lưu trữ bất kỳ mật khẩu, private key, token hay chuỗi kết nối nhạy cảm nào trực tiếp trong mã nguồn Python hoặc TypeScript.

---

## 6. BẢO VỆ DỮ LIỆU NHẠY CẢM & QUY TẮC GHI LOG (LOGGING POLICY)

- **Quy tắc làm sạch Log (Data Sanitization & Redaction):**
  - Hệ thống ghi log (Logger) tự động ẩn các trường nhạy cảm: `password`, `hashed_password`, `access_token`, `refresh_token`, `credit_card_number`, `cvv`.
  - Tuyệt đối không ghi thông tin nhạy cảm vào `stdout`, file log hoặc `ai_audit_logs`.
- **Bảo mật kênh truyền (Transport Security):**
  - Môi trường sản xuất bắt buộc sử dụng giao thức HTTPS (TLS 1.3).
  - Cookie mang cờ bảo mật: `HttpOnly=True`, `Secure=True`, `SameSite=Lax`.

---

## 7. CẤU HÌNH BẢO MẬT CORS & HTTP HEADERS

```python
# Cấu hình CORS chặt chẽ tại app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Chỉ cho phép frontend hợp lệ
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
```

Bổ sung các HTTP Security Headers tiêu chuẩn cho mọi phản hồi:
- `X-Content-Type-Options: nosniff` (Chống đoán định MIME type)
- `X-Frame-Options: DENY` (Chống tấn công Clickjacking)
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (Trên môi trường HTTPS)
