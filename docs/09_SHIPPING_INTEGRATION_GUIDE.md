# TÀI LIỆU HƯỚNG DẪN TÍCH HỢP VẬN CHUYỂN (SHIPPING INTEGRATION GUIDE)

> **Dự án:** NOVELIA BOOKS — Phase 8: Shipping Integration  
> **Phiên bản:** 1.0  
> **Trạng thái:** Active & Production-Ready  
> **Nhà cung cấp hỗ trợ:** Giao Hàng Nhanh (GHN Open API v2), Giao Hàng Tiết Kiệm (GHTK API), Mock Logistics Provider

---

## 1. TỔNG QUAN KIẾN TRÚC & NGUYÊN TẮC THIẾT KẾ

Hệ thống Logistics và Điều vận của NOVELIA BOOKS được xây dựng theo mô hình **Provider Pattern** kết hợp với kiến trúc **Layered Hexagonal Architecture**:

```
                       +-----------------------------+
                       |   FastAPI Shipping Router   |
                       |    (/api/v1/shipping)       |
                       +--------------+--------------+
                                      |
                                      v
                       +-----------------------------+
                       |       ShippingService       |
                       | (ACID State Reconciliation) |
                       +--------------+--------------+
                                      |
                                      v
                       +-----------------------------+
                       |    ShippingProvider (ABC)   |
                       +---+----------+----------+---+
                           |          |          |
                           v          v          v
                  +--------+   +------+---+   +--+--------+
                  |  GHN   |   |   GHTK   |   |   MOCK    |
                  |Adapter |   | Adapter  |   |  Adapter  |
                  +--------+   +----------+   +-----------+
```

### 4 Nguyên tắc Cốt lõi:
1. **Tuyệt đối trung thực (Realism Directive):**
   - Hệ thống **không bịa đặt endpoint hoặc giả mạo mã vận đơn bưu cục như thật** khi chưa kết nối tài khoản doanh nghiệp.
   - Nếu chạy ở chế độ `SHIPPING_ENVIRONMENT=live` mà chưa cấu hình token doanh nghiệp, hệ thống áp dụng cơ chế an toàn **Live Blocked Safety Guard** (`LiveIntegrationBlockedError` / HTTP 503) và thông báo minh bạch `LIVE INTEGRATION is BLOCKED`.
2. **Backend Authoritative & ACID Consistency:**
   - Mọi trạng thái vận đơn, đối soát COD và chuyển dịch trạng thái đơn hàng đều được kiểm soát và ghi nhận trong cơ sở dữ liệu MySQL (`shipments`, `shipment_events`, `orders`, `payments`).
3. **Idempotency & Chống Callback Lặp (Replay Protection):**
   - Bộ lọc `ShipmentRepository.has_event_occurred` bảo vệ hệ thống trước các webhook gửi trùng lặp hoặc bưu cục retry nhiều lần.
4. **Tự động Đối soát Thu hộ COD:**
   - Khi nhận webhook sự kiện `DELIVERED`, hệ thống tự động hoàn tất đơn hàng (`Order.status = COMPLETED`), đồng thời tự động cập nhật thanh toán COD từ `PENDING` sang `PAID` kèm dấu thời gian `paid_at`.

---

## 2. CHÍNH SÁCH "LIVE INTEGRATION IS BLOCKED"

> [!CAUTION]
> **THÔNG BÁO QUAN TRỌNG VỀ TÍCH HỢP TRỰC TIẾP (LIVE INTEGRATION BLOCKED):**  
> Khi chưa có tài khoản doanh nghiệp chính thức và API Token từ Ban quản lý bưu cục GHN hoặc GHTK, các yêu cầu điều vận trực tiếp ở chế độ `live` sẽ **BỊ KHÓA TOÀN DIỆN (BLOCKED)**.  
> Để phục vụ phát triển, nghiệm thu và kiểm thử tự động, hệ thống sử dụng **MockShippingAdapter** (`SHIPPING_ENVIRONMENT=mock` hoặc `SHIPPING_ENVIRONMENT=sandbox`).

### Bảng trạng thái vận hành:

| Biến môi trường `SHIPPING_ENVIRONMENT` | Token đối tác | Hành vi hệ thống | Mã phản hồi HTTP |
| :--- | :--- | :--- | :--- |
| `mock` / `sandbox` | Không bắt buộc | Điều vận qua `MockShippingAdapter` với mã vận đơn `MOCK_...` và mô phỏng lộ trình bưu cục chuẩn xác | `201 CREATED` |
| `live` | Thiếu `GHN_TOKEN` / `GHTK_TOKEN` | **BLOCKED:** Kích hoạt `LiveIntegrationBlockedError`. Không sinh mã giả mạo | `503 SERVICE UNAVAILABLE` |
| `live` | Đã cấu hình Token hợp lệ | Kết nối Open API chính thức của đối tác để cấp mã vận đơn thật từ hệ thống bưu cục | `201 CREATED` |

---

## 3. THÔNG SỐ KỸ THUẬT API CHÍNH THỨC GHN (GIAO HÀNG NHANH)

Hệ thống tích hợp theo tài liệu chính thức: **GHN Open API v2 (Shiip Public API)**.

### 3.1. Thông tin Endpoint
- **Môi trường Dev / Sandbox:** `https://dev-online-gateway.ghn.vn/shiip/public-api`
- **Môi trường Production:** `https://online-gateway.ghn.vn/shiip/public-api`
- **Tạo đơn hàng:** `POST /v2/shipping-order/create`
- **Tra cứu vận đơn:** `POST /v2/shipping-order/detail`
- **Hủy vận đơn:** `POST /v2/shipping-order/cancel`

### 3.2. Cơ chế Xác thực
Headers bắt buộc trong mọi request:
```http
Token: <GHN_TOKEN>
ShopId: <GHN_SHOP_ID>
Content-Type: application/json
```

### 3.3. Cấu trúc Payload Tạo Đơn GHN
```json
{
  "payment_type_id": 2,
  "note": "Don hang tu Novelia Books - NVL-20261020-001",
  "required_note": "CHOXEMHANGKHONGTHU",
  "client_order_code": "NVL-20261020-001",
  "to_name": "Nguyễn Văn Đọc",
  "to_phone": "0987654321",
  "to_address": "Số 10 Phạm Văn Đồng",
  "to_ward_code": "1A0101",
  "to_district_id": 1442,
  "cod_amount": 280000,
  "weight": 500,
  "length": 20,
  "width": 15,
  "height": 5,
  "service_type_id": 2,
  "items": [
    {
      "name": "Nhà Giả Kim",
      "code": "BK-NHK-01",
      "quantity": 2,
      "price": 125000
    }
  ]
}
```

### 3.4. Bảng Ánh xạ Trạng thái GHN sang Trạng thái Novelia:

| Mã trạng thái GHN | Trạng thái Shipment | Trạng thái Order tương ứng |
| :--- | :--- | :--- |
| `ready_to_pick` | `READY_TO_PICK` | Giữ nguyên (`CONFIRMED` / `PROCESSING`) |
| `picking` / `storing` | `PICKING` | Giữ nguyên (`PROCESSING`) |
| `delivering` / `transporting` | `IN_TRANSIT` | Chuyển sang `SHIPPING` |
| `delivered` | `DELIVERED` | Chuyển sang `COMPLETED` + Đối soát COD thành `PAID` |
| `delivery_fail` | `FAILED` | Giữ nguyên kèm checkpoint cảnh báo |
| `returned` / `cancel` | `RETURNED` | Chuyển sang `CANCELLED` |

---

## 4. THÔNG SỐ KỸ THUẬT API CHÍNH THỨC GHTK (GIAO HÀNG TIẾT KIỆM)

Hệ thống tích hợp theo tài liệu chính thức: **GHTK Open API Specification**.

### 4.1. Thông tin Endpoint
- **Môi trường Sandbox:** `https://services.giaohangtietkiem.vn/services/shipment`
- **Môi trường Production:** `https://services.giaohangtietkiem.vn/services/shipment`
- **Tạo đơn hàng:** `POST /order`
- **Tra cứu vận đơn:** `GET /v2/cache/{tracking_code}`
- **Hủy vận đơn:** `POST /cancel/{tracking_code}`

### 4.2. Cơ chế Xác thực
Headers bắt buộc:
```http
Token: <GHTK_TOKEN>
Content-Type: application/json
```

### 4.3. Cấu trúc Payload Tạo Đơn GHTK
```json
{
  "products": [
    {
      "name": "Nhà Giả Kim",
      "weight": 0.25,
      "quantity": 2,
      "product_code": "BK-NHK-01"
    }
  ],
  "order": {
    "id": "NVL-20261020-001",
    "pick_name": "Novelia Books Warehouse",
    "pick_address": "Số 1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội",
    "pick_tel": "0901234567",
    "tel": "0987654321",
    "name": "Nguyễn Văn Đọc",
    "address": "Số 10 Phạm Văn Đồng",
    "province": "Hà Nội",
    "district": "Cầu Giấy",
    "ward": "Dịch Vọng Hậu",
    "is_freeship": 0,
    "pick_money": 280000,
    "note": "Cho xem hang khong cho thu",
    "value": 280000
  }
}
```

### 4.4. Bảng Ánh xạ Trạng thái GHTK:

| Mã trạng thái GHTK (Status ID) | Trạng thái Shipment | Trạng thái Order tương ứng |
| :--- | :--- | :--- |
| `1`, `2` (Chờ tiếp nhận / Đã tiếp nhận) | `READY_TO_PICK` | Giữ nguyên |
| `3`, `12` (Đã lấy hàng / Đang lưu kho) | `PICKING` | Giữ nguyên |
| `4`, `13` (Đang giao hàng / Luân chuyển) | `IN_TRANSIT` | Chuyển sang `SHIPPING` |
| `5`, `6` (Đã giao hàng / Đã đối soát) | `DELIVERED` | Chuyển sang `COMPLETED` + Đối soát COD thành `PAID` |
| `9`, `10` (Không giao được / Chờ trả) | `FAILED` | Giữ nguyên |
| `11`, `21` (Đã trả hàng / Đã hủy) | `RETURNED` | Chuyển sang `CANCELLED` |

---

## 5. BẢO MẬT WEBHOOK & CƠ CHẾ ĐỐI SOÁT COD

### 5.1. Xác thực Chữ ký Số Webhook (HMAC Verification)
Tất cả webhook gửi đến endpoint `/api/v1/shipping/webhook/{carrier}` đều phải kèm chữ ký số HMAC-SHA256 trong HTTP header:
- Header: `X-Hub-Signature` hoặc `X-GHTK-Signature`
- Thuật toán: `HMAC-SHA256(raw_request_body, webhook_secret)`
- Nếu chữ ký không khớp, hệ thống từ chối ngay lập tức với mã lỗi `401 UNAUTHORIZED`.

### 5.2. Chống Replay Attack (Idempotent Checkpoint Recording)
```python
# Kiểm tra sự kiện trùng lặp trước khi ghi nhật ký hoặc thay đổi trạng thái
if ShipmentRepository.has_event_occurred(db, shipment.id, event_data.status, event_data.occurred_at):
    return {"status": "ignored", "message": "Duplicate event callback ignored"}
```

### 5.3. Tự động Đối soát Doanh thu COD (Automatic COD Reconciliation)
Khi nhận sự kiện `DELIVERED`:
```python
if shipment.status == "DELIVERED":
    order.status = "COMPLETED"
    if order.payment and order.payment.payment_method == "COD" and order.payment.payment_status == "PENDING":
        order.payment.payment_status = "PAID"
        order.payment.paid_at = event_data.occurred_at
```

---

## 6. DANH MỤC CÁC BIẾN MÔI TRƯỜNG CẤU HÌNH (.ENV)

Bổ sung các tham số sau vào file `backend/.env`:

```ini
# ============================================================================
# LOGISTICS & SHIPPING CONFIGURATION (PHASE 8)
# ============================================================================

# Môi trường: 'mock', 'sandbox', hoặc 'live'
SHIPPING_ENVIRONMENT=mock

# Nhà vận chuyển mặc định: 'GHN', 'GHTK', hoặc 'MOCK'
DEFAULT_SHIPPING_CARRIER=GHN

# Cấu hình Giao Hàng Nhanh (GHN)
GHN_API_URL=https://dev-online-gateway.ghn.vn/shiip/public-api
GHN_TOKEN=
GHN_SHOP_ID=
GHN_CLIENT_PHONE=0901234567
GHN_WEBHOOK_SECRET=novelia_ghn_webhook_secret_key_2026

# Cấu hình Giao Hàng Tiết Kiệm (GHTK)
GHTK_API_URL=https://services.giaohangtietkiem.vn/services/shipment
GHTK_TOKEN=
GHTK_WEBHOOK_SECRET=novelia_ghtk_webhook_secret_key_2026
```

---

## 7. KẾT QUẢ KIỂM THỬ HỆ THỐNG (TEST RESULTS MATRIX)

### 7.1. Backend Test Suite (Pytest - 13/13 Pass)
- `test_shipping_provider_status`: Kiểm tra cờ trạng thái nhà vận chuyển và phát hiện live blocked.
- `test_dispatch_order_requires_staff_role`: Xác thực phân quyền RBAC (chặn Customer tự điều vận).
- `test_dispatch_order_invalid_status_rejected`: Chặn tạo vận đơn cho đơn chưa xác nhận (`PENDING` hoặc `CANCELLED`).
- `test_dispatch_order_success_mock`: Tạo vận đơn thành công, sinh tracking code, cập nhật đơn sang `SHIPPING`.
- `test_duplicate_dispatch_rejected`: Chặn tạo nhiều vận đơn trên cùng 1 đơn hàng.
- `test_live_integration_blocked_without_credentials`: Kích hoạt lỗi 503 khi live mode thiếu token.
- `test_customer_get_tracking_own_order`: Khách hàng tra cứu hành trình đơn của mình.
- `test_customer_cannot_get_tracking_other_user_order`: Ngăn chặn vi phạm bảo mật chéo (Tenant Isolation).
- `test_public_tracking_lookup`: Tra cứu công khai qua mã vận đơn bưu cục.
- `test_webhook_invalid_signature_rejected`: Từ chối webhook có chữ ký sai.
- `test_webhook_status_transition_in_transit`: Webhook `IN_TRANSIT` đồng bộ `Order.status = SHIPPING`.
- `test_webhook_delivered_reconciles_cod_payment`: Webhook `DELIVERED` hoàn tất đơn và đổi COD sang `PAID`.
- `test_webhook_duplicate_callback_ignored`: Bỏ qua callback lặp không ghi nhận trùng.

### 7.2. Frontend Test Suite (Vitest - 4/4 Pass)
- `AdminOrdersView displays carrier pills, provider status, and allows order dispatching`: Hiển thị chip nhà vận chuyển, mở modal điều vận, điền thông số gói hàng và gọi API tạo vận đơn.
- `AdminOrdersView opens tracking timeline modal with checkpoint history`: Mở modal tra cứu hành trình bưu tá với timeline chi tiết.
- `OrderHistoryView shows shipment badge and allows customer to view delivery timeline`: Khách hàng xem huy hiệu mã vận đơn và xem timeline giao hàng.
- `Handles carrier blocked error gracefully when live integration credentials are not configured`: Xử lý thông báo lỗi `LIVE INTEGRATION is BLOCKED` an toàn và thân thiện trên giao diện.

---

## 8. HƯỚNG DẪN CHUYỂN ĐỔI SANG MÔI TRƯỜNG PRODUCTION (GO-LIVE CHECKLIST)

Khi cửa hàng ký hợp đồng chính thức với GHN / GHTK:
1. Đăng nhập [GHN Khách Hàng Doanh Nghiệp](https://khachhang.ghn.vn) lấy `API Token` và `Shop ID`.
2. Đăng ký Webhook URL với GHN: `https://api.novelia.vn/api/v1/shipping/webhook/ghn`.
3. Đăng nhập [GHTK Đối Tác](https://khachhang.giaohangtietkiem.vn) lấy `Partner Token`.
4. Điền các giá trị vào file `.env` trên máy chủ production:
   - `SHIPPING_ENVIRONMENT=live`
   - `GHN_TOKEN=<live_token>`
   - `GHN_SHOP_ID=<live_shop_id>`
   - `GHTK_TOKEN=<live_token>`
5. Khởi động lại dịch vụ backend. Kiểm tra endpoint `/api/v1/shipping/providers/status`:
   - Kết quả trả về `is_live_ready: true` cho cả GHN và GHTK.
