# NOVELIA BOOKS — BÁO CÁO REDESIGN ADMIN CONTROL CENTER V4
**Dự án:** NOVELIA BOOKS — Nền tảng Thương mại Điện tử Sách & Trợ lý AI  
**Phân hệ:** Admin Executive Dashboard & Store Operations Control Center  
**Phiên bản:** Redesign V4 (Premium Editorial Commerce Admin)  
**Tiêu chuẩn kiến trúc:** Tuân thủ 100% [AGENTS.md](file:///AGENTS.md) và [02_ARCHITECTURE.md](file:///docs/02_ARCHITECTURE.md)

---

## 1. TỔNG HỢP NGUYÊN NHÂN CÁC VẤN ĐỀ TRƯỚC REDESIGN

Dựa trên phân tích mã nguồn và đối chiếu với screenshot báo cáo của người dùng:

1. **Thẻ KPI Doanh thu bị lệch chiều cao so với 3 thẻ còn lại:**
   - *Nguyên nhân:* Thẻ Doanh thu trước đây nhồi nhét quá nhiều thông tin tài chính chi tiết (`Tổng Doanh thu Gộp`, `Tiền Thực thu (Dòng tiền)`, huy hiệu `Chưa có dữ liệu COGS`, và đoạn văn bản giải thích `profit_note`) trực tiếp vào trong nội dung thẻ, trong khi 3 thẻ KPI còn lại chỉ có chỉ số chính và tỷ lệ tăng trưởng.
2. **Biểu đồ doanh thu bị chồng lấn nhãn ngày trên trục X:**
   - *Nguyên nhân:* Hàm render biểu đồ SVG cũ duyệt qua 100% các điểm dữ liệu (`points.map(...)`) và vẽ phần tử `<text>` cho từng điểm. Khi chọn kỳ xem 30 ngày hoặc 90 ngày, 30-90 nhãn ngày chen chúc trong chiều rộng 600px khiến chữ đè lên nhau thành vệt đen không đọc được.
3. **Khu vực tồn kho & sách bán chạy thiếu phân cấp thị giác:**
   - *Nguyên nhân:* Thiếu các class CSS chuyên biệt; phần trạng thái an toàn chỉ là text đơn giản; danh sách top sách bán chạy chưa hiển thị ảnh bìa trực quan, thông tin SKU và liên kết chi tiết chưa cân đối.
4. **Style các nút/tab và bảng bị rò rỉ mặc định của trình duyệt:**
   - *Nguyên nhân:* Các class như `.admin-table-v2`, `.admin-period-box`, `.admin-bestsellers-header` chưa được định nghĩa đầy đủ trong `index.css`, dẫn tới việc các phần tử hiển thị dạng thô hoặc thiếu padding/border đồng bộ.
5. **Khoảng cách (spacing) giữa các hàng chưa chuẩn:**
   - *Nguyên nhân:* Thiếu layout wrapper đồng nhất giữa hàng KPI, hàng giữa (Biểu đồ 60% + Tồn kho 40%) và hàng dưới (Bảng đơn hàng).
6. **Nguy cơ che khuất nội dung bởi Trợ lý AI:**
   - *Nguyên nhân:* Nút floating FAB của Novelia AI Assistant nằm cố định ở góc dưới bên phải (`fixed bottom-8 right-8`), nếu container bảng không có padding đáy an toàn sẽ che khuất nút thao tác hoặc phân trang của dòng đơn hàng cuối cùng.

---

## 2. CÁC TẬP TIN ĐÃ CHỈNH SỬA & GIẢI PHÁP TRIỂN KHAI

### 2.1. Mã nguồn Frontend:
- [frontend/src/components/AdminDashboardView.tsx](file:///frontend/src/components/AdminDashboardView.tsx):
  - Tách bạch cấu trúc 4 thẻ KPI doanh thu, đơn hàng, sách đang bán, sắp hết hàng với chiều cao cân đối tuyệt đối (`min-height: 145px`).
  - Đưa phần kiểm toán tài chính và giá vốn COGS ra thanh banner chuyên biệt `admin-financial-truth-strip` đặt ngay dưới hàng KPI: hiển thị rõ ràng Doanh thu Gộp, Tiền Thực thu, cảnh báo thiếu COGS mà không làm vỡ giao diện thẻ.
  - Tái cấu trúc hàm `renderTimelineChart`: thuật toán lấy mẫu nhãn trục X thông minh (`tickStep = Math.ceil(coords.length / 7)`), chỉ hiển thị tối đa 6-7 nhãn cách đều, chuyển định dạng ngày sang `DD/MM`, bổ sung tooltip tương tác khi hover điểm dữ liệu và đường gióng phụ trợ.
  - Thiết kế lại khu vực Tồn kho cần chú ý: khi kho an toàn, hiển thị banner bảo chứng tích cực với icon `CheckCircle2`; khu vực Top 5 sách bán chạy hiển thị danh sách với ảnh bìa thực tế, SKU, số cuốn đã bán và link điều hướng.
  - Chuẩn hóa bảng Đơn hàng gần đây với cấu trúc 8 cột, định dạng ngày giờ chuẩn Việt Nam (`DD/MM/YYYY HH:mm`), huy hiệu trạng thái đơn (`status-pill`), thanh toán, vận chuyển và nút `Chi tiết →`.
  - Tích hợp bộ chọn thời gian hiển thị nhãn dải ngày thực tế (ví dụ: `7 ngày qua (15/10/2026 - 22/10/2026)`), đồng thời duy trì các nút bấm truy cập nhanh `7 ngày`, `30 ngày`, `90 ngày` tương thích 100% với các bài kiểm thử Vitest.
  - Nâng cấp Header với huy hiệu thông báo số `3` màu cam đồng và avatar người dùng `Quản Trị Viên` / `Administrator`.

- [frontend/src/index.css](file:///frontend/src/index.css):
  - Bổ sung toàn diện hệ thống class CSS chuẩn Premium Editorial Commerce Admin:
    - `.admin-period-box`
    - `.admin-notification-count-badge`
    - `.admin-kpi-grid` (4 cột desktop, 2 cột tablet, 1 cột mobile)
    - `.admin-kpi-card` & các bubble icon màu amber, orange, blue, red
    - `.admin-financial-truth-strip`, `.admin-cogs-pill`, `.admin-profit-note`
    - `.admin-overview-middle-grid` (1.7fr 1.1fr desktop, 1fr mobile)
    - `.admin-chart-tooltip`
    - `.admin-stock-safe-banner` & `.admin-stock-safe-icon`
    - `.admin-bestsellers-header`, `.admin-bestseller-row`, `.admin-bestseller-thumb`
    - `.admin-table-v2`, `.admin-responsive-table-wrap`, `.admin-action-btn-sm`
  - Bổ sung khoảng đệm an toàn `padding-bottom: 5rem` cho `.admin-content-wrapper` đảm bảo nút Novelia AI Assistant không bao giờ che khuất dữ liệu bảng.

---

## 3. CÁC API & DỮ LIỆU ĐƯỢC SỬ DỤNG (BACKEND & MYSQL)

Dự án giữ nguyên vẹn 100% backend FastAPI và cơ sở dữ liệu MySQL, không sử dụng dữ liệu giả:

| Endpoint | Phương thức | Dữ liệu cung cấp cho Dashboard |
| :--- | :---: | :--- |
| `/api/v1/admin/dashboard/summary?period={period}` | `GET` | Tổng doanh thu, tiền thực thu, tổng đơn, số sách, tồn kho thấp, chuỗi dữ liệu biểu đồ timeline, top sách bán chạy và phân bổ trạng thái đơn. |
| `/api/v1/orders/admin?page=1&size=6` | `GET` | Danh sách 6 đơn hàng phát sinh gần nhất kèm thông tin người nhận, tổng tiền, trạng thái đơn, thanh toán và vận chuyển. |
| `/api/v1/ai/health` | `GET` | Trạng thái sẵn sàng và phiên bản của Trợ lý AI Assistant / Copilot. |

---

## 4. KẾT QUẢ KIỂM THỬ HỆ THỐNG

### 4.1. Frontend Unit & Integration Tests (Vitest)
```powershell
npm test -- --run
```
- **Kết quả:** **11 / 11 Test Suites PASSED** (**63 / 63 Tests PASSED**).
- Bao gồm kiểm tra nghiêm ngặt tính chân thực tài chính (Financial Truthfulness — không tạo lãi giả khi thiếu COGS), chuyển đổi kỳ lọc thời gian (`7 ngày`, `30 ngày`), kiểm soát phân quyền RBAC và quản trị danh mục.

### 4.2. Static Type Checking & Linting
```powershell
npm run type-check
npm run lint
```
- **Kết quả:** **0 lỗi TypeScript** (`tsc --noEmit`), **0 cảnh báo ESLint**.

### 4.3. Production Build Validation
```powershell
npm run build
```
- **Kết quả:** Biên dịch thành công trong 6.37 giây (`dist/index.html`, `dist/assets/index-CesFMjLc.css`, `dist/assets/index-CDzvjcv-.js`).

### 4.4. Backend Tests (Pytest)
```powershell
python -m pytest
```
- **Kết quả:** **209 / 209 Tests PASSED** (100% passed trong 11.31 giây).

---

## 5. KIỂM THỬ GIAO DIỆN & RESPONSIVE (BROWSER SUBAGENT & SCREENSHOTS)

Đã thực hiện kiểm tra thực tế bằng trình duyệt tại 5 độ phân giải mục tiêu:

| Viewport | Kích thước | Tệp hình ảnh ghi nhận | Đánh giá giao diện |
| :--- | :---: | :--- | :--- |
| **Desktop Wide** | `1440 x 900` | [admin_dashboard_1440x900.png](file:///C:/Users/dangx/.gemini/antigravity-ide/brain/2b3b799f-0e4e-478a-bacb-038bad6fe7a3/admin_dashboard_1440x900_1792651718358.png) | 4 thẻ KPI cân đối ngang nhau, dải tài chính COGS rõ ràng, biểu đồ 60% và tồn kho 40% cân xứng, bảng đơn hàng thoáng đãng. |
| **Desktop Small** | `1024 x 768` | [admin_dashboard_1024x768.png](file:///C:/Users/dangx/.gemini/antigravity-ide/brain/2b3b799f-0e4e-478a-bacb-038bad6fe7a3/admin_dashboard_1024x768_1792651733688.png) | Sidebar tự động thu gọn sang chế độ drawer, 4 thẻ KPI chuyển thành lưới 2x2 cân đối, biểu đồ hiển thị mượt mà. |
| **Tablet Portrait** | `768 x 1024` | [admin_dashboard_768x1024.png](file:///C:/Users/dangx/.gemini/antigravity-ide/brain/2b3b799f-0e4e-478a-bacb-038bad6fe7a3/admin_dashboard_768x1024_1792651742994.png) | Bố cục 1 cột nội dung, không có hiện tượng vỡ khung hay tràn ngang viewport ngoài ý muốn. |
| **Mobile Standard** | `430 x 932` | [admin_dashboard_430x932.png](file:///C:/Users/dangx/.gemini/antigravity-ide/brain/2b3b799f-0e4e-478a-bacb-038bad6fe7a3/admin_dashboard_430x932_1792651752481.png) | 4 thẻ KPI xếp dọc 1 cột, biểu đồ và bảng đơn hàng hỗ trợ cuộn ngang linh hoạt (`touch scroll`), nút AI Assistant gọn gàng ở góc. |
| **Mobile Compact** | `375 x 812` | [admin_dashboard_375x812.png](file:///C:/Users/dangx/.gemini/antigravity-ide/brain/2b3b799f-0e4e-478a-bacb-038bad6fe7a3/admin_dashboard_375x812_1792651766443.png) | Bố cục mobile tối ưu, kích thước font chữ dễ đọc, nút bấm có diện tích chạm thoải mái. |

---

## 6. DANH SÁCH LỖI CÒN TỒN TẠI
- **Không có lỗi tồn đọng.** Toàn bộ 63 bài kiểm tra frontend, 209 bài kiểm tra backend, kiểm tra tĩnh TypeScript và quy trình đóng gói sản xuất đều đạt trạng thái **PASS 100%**. Giao diện thực tế khớp hoàn toàn với định hướng thiết kế **Premium Editorial Commerce Admin**.
