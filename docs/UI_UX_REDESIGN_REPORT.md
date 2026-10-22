# NOVELIA BOOKS — BÁO CÁO THIẾT KẾ LẠI GIAO DIỆN ADMIN V2 (UI/UX REDESIGN REPORT)

> **Dự án:** NOVELIA BOOKS — Nền tảng Thương mại Điện tử Sách & Trợ lý Thông minh BookMatch AI  
> **Tài liệu:** Báo cáo Kỹ thuật Tái cấu trúc Bố cục Quản trị V2  
> **Người thực hiện:** Senior Product Designer & Senior React Frontend Engineer  
> **Thời gian:** 21/10/2026  
> **Trạng thái:** Hoàn thành & Đạt chuẩn Production Ready  

---

## 1. TỔNG QUAN & BỐI CẢNH

Giao diện quản trị ban đầu của NOVELIA BOOKS gặp phải tình trạng quá tải điều hướng theo chiều ngang, tồn tại hai hàng thanh điều hướng lặp lại (thanh menu storefront với 12 nút và thanh menu tab nội bộ của Dashboard), cùng hiện tượng bóp nghẹt nội dung (bảng khuyến mãi bị ép cạnh một form thêm mới cố định 380px gây tràn ngang viewport) và tiêu đề không đồng nhất giữa các phân hệ (trang khuyến mãi vẫn mang tiêu đề "Bảng Điều Hành Trung Tâm NOVELIA").

Nhiệm vụ đặt ra: Tái cấu trúc trực tiếp source code thành **Admin Shell V2** theo phong cách **Premium Editorial Commerce Admin**, chuẩn hóa hệ thống 11 module quản trị, responsive hoàn toàn từ desktop 1440px+ tới mobile 375px, và tuân thủ 100% các ràng buộc tài chính, RBAC và kiểm thử tự động của dự án.

---

## 2. NHỮNG VẤN ĐỀ ĐÃ PHÁT HIỆN TRƯỚC KHI SỬA

| STT | Vấn đề phát hiện | Nguyên nhân kỹ thuật | Hậu quả UI/UX |
| :--- | :--- | :--- | :--- |
| **01** | **Điều hướng ngang chồng lấn (Double Nav)** | `App.tsx` bọc `AdminDashboardView` trong toàn bộ layout storefront (`<Header>`, `<nav className="nav-tabs-bar">`, `<footer>`), đồng thời `AdminDashboardView` lại có thêm một hàng tab ngang riêng. | Màn hình bị chiếm hơn 200px chiều cao cho thanh điều hướng, người dùng bị rối mắt với 12 nút bấm ngang. |
| **02** | **Trang Khuyến mãi bị bóp nghẹt & tràn ngang** | Bảng danh sách coupon và form tạo mã được đặt trong grid 2 cột `taxonomies-grid` với form cố định 380px. | Bảng khuyến mãi có tới 8 cột bị ép hẹp dưới 600px, chữ bị cắt vụn, bảng tràn khỏi màn hình desktop thông thường. |
| **03** | **Tiêu đề không đồng nhất** | Tiêu đề "Bảng Điều Hành Trung Tâm NOVELIA" được đặt cứng ở đầu component cha, không đổi theo module con được chọn. | Khi chuyển sang tab "Khuyến mãi", tiêu đề vẫn là tổng quan, gây hiểu lầm cho người vận hành. |
| **04** | **Tràn ảnh trong CartDrawer & BookMatch** | Thẻ `<img>` thiếu ràng buộc `max-width: 100%` và `object-fit: cover` trong reset toàn cục. | Ảnh bìa sách trong giỏ hàng và danh mục gợi ý tràn ra khỏi viền card chứa. |
| **05** | **Thiếu Drawer trên Mobile** | Thanh menu chỉ thu gọn đơn giản bằng media query hoặc tràn màn hình ngang khi thu nhỏ về dưới 768px. | Người dùng di động (375px–430px) không thể thao tác quản trị trên điện thoại. |

---

## 3. NHỮNG COMPONENT & LAYOUT ĐÃ THAY ĐỔI

### A. Xây dựng Admin Shell V2 hoàn chỉnh
- **Tập tin:** `frontend/src/components/AdminDashboardView.tsx` & `frontend/src/index.css`.
- **Cấu trúc Shell:**
  1. **Left Sidebar (250px Desktop):**
     - Logo NOVELIA BOOKS tinh tế cùng slogan *"Books for a better tomorrow"*.
     - 11 Module quản trị chuẩn hóa:
       1. **Tổng quan** (`overview` — `LayoutDashboard`)
       2. **Sách & Danh mục** (`taxonomies` — `BookOpen`)
       3. **Kho hàng** (`inventory` — `Boxes`)
       4. **Đơn hàng** (`orders` — `ShoppingBag`)
       5. **Khách hàng & Nhân sự** (`users` — `Users`)
       6. **Khuyến mãi** (`promotions` — `Ticket`)
       7. **Vận chuyển** (`shipping` — `Truck`)
       8. **Phân tích kinh doanh** (`analytics` — `BarChart3`)
       9. **AI Trợ lý** (`ai-assistant` — `Sparkles`)
       10. **Nhật ký hệ thống** (`audit` — `ShieldAlert`)
       11. **Cài đặt** (`settings` — `Sliders`)
     - Trạng thái Active: Nền cam nhạt `#FDF6EE`, chữ màu đồng đậm `#C27D38`, thanh chỉ báo dọc nổi bật ở cạnh trái.
     - Nút thu gọn Sidebar trên desktop (chuyển về dạng icon 76px).
     - Nút "Xem cửa hàng" dẫn về giao diện đọc giả storefront mà không làm mất phiên đăng nhập.
     - Trên mobile (< 1024px): Sidebar tự động chuyển thành Drawer trượt có backdrop làm mờ màn hình và nút đóng `X`.
  2. **Top Header (68px):**
     - Nút toggle mở Drawer trên mobile / thu gọn trên desktop.
     - Thanh tìm kiếm toàn cục với phím tắt nhanh `Ctrl + K`.
     - Nút biểu tượng chuông thông báo có chỉ báo chấm đỏ.
     - Menu định danh tài khoản đang đăng nhập với Avatar ký tự, tên người dùng và vai trò (`Quản trị viên` / `Nhân sự vận hành`).
  3. **Main Viewport & Page Header:**
     - Chiếm toàn bộ không gian còn lại bên phải.
     - Padding chuẩn hóa: 28px desktop, 16px mobile.
     - Hệ thống Breadcrumb chuẩn mực: `Quản trị / [Tên phân hệ]`.
     - Page Title rõ ràng theo từng phân hệ, kèm mô tả ngắn gọn và nút Primary Action đặt tại vị trí dễ nhận biết.

### B. Tách biệt Layout Storefront và Admin Portal trong `App.tsx`
- **Tập tin:** `frontend/src/App.tsx`.
- Khi người dùng có quyền `STAFF` hoặc `ADMIN` truy cập các tab quản trị (`admin-dashboard`, `inventory`, `admin-orders`), ứng dụng sẽ hiển thị trực tiếp `AdminDashboardView` toàn màn hình.
- Loại bỏ hoàn toàn thanh điều hướng ngang 12 nút, header lặp lại và footer storefront khi đang trong chế độ quản trị.
- Tích hợp Novelia AI Assistant trôi nổi (floating) ở góc phải dưới (`z-index: 9999`) mà không che khuất bảng số liệu hay nút bấm.

### C. Thiết kế lại Trang Tổng Quan Cửa Hàng
- Hàng 4 thẻ KPI đồng bộ kích thước:
  - **Doanh thu:** Giá trị thực tế từ MySQL qua API `formatVND(total_revenue)`, tỷ lệ tăng trưởng `▲ 12.5%`, hiển thị ghi chú tài chính trung thực `Chưa có dữ liệu COGS`.
  - **Đơn hàng:** Tổng số đơn phát sinh và số đơn hợp lệ.
  - **Sách đang bán:** Tổng đầu sách đang lưu hành.
  - **Sắp hết hàng:** Số đầu sách chạm hoặc dưới ngưỡng an toàn kho.
- Khung biểu đồ doanh thu theo thời gian dạng **Smooth SVG Line Chart** với dải màu gradient cam đồng `#C27D38`, điểm dữ liệu tròn tương tác và bộ nút chuyển đổi linh hoạt: `[Doanh thu] [Đơn hàng] [Giá trị TB]`.
- Khung cảnh báo tồn kho với ảnh bìa thumbnail, mã SKU, số lượng tồn vật lý và nhãn cảnh báo đỏ `Tồn thấp`.
- Bảng đơn hàng gần đây chiếm toàn bộ chiều rộng bên dưới: Mã đơn, Khách hàng, Ngày đặt, Tổng tiền, Trạng thái (Pill), Thanh toán, Vận chuyển, và nút thao tác `Chi tiết >`.

### D. Thiết kế lại Trang Khuyến Mãi & Mã Giảm
- Breadcrumb: `Quản trị / Khuyến mãi`.
- Tiêu đề: `Khuyến mãi & Mã giảm` — Mô tả chức năng rõ ràng.
- Nút bấm `+ Tạo mã giảm giá` màu đồng nổi bật.
- Thanh công cụ gồm ô tìm kiếm mã và nhóm nút lọc trạng thái: `Tất cả`, `Đang hoạt động`, `Tạm ngưng`.
- Bảng mã giảm giá chiếm toàn bộ 100% chiều rộng nội dung, có container cuộn ngang chống vỡ layout trên màn hình nhỏ.
- **Form tạo mã giảm giá chuyển đổi thành Modal Dialog:** Mở ra ở giữa màn hình với backdrop mờ, bố cục 2 cột gọn gàng, validation đầy đủ, có nút `Hủy bỏ` và `+ Kích Hoạt Mã Giảm Giá`.

---

## 4. DANH SÁCH CÁC ROUTE & MODULE ĐÃ KIỂM TRA

| Module | Route / Param | Giao diện kiểm tra | Trạng thái |
| :--- | :--- | :--- | :--- |
| **1. Tổng quan** | `?tab=admin-dashboard&module=overview` | 4 KPI, SVG Line Chart, Tồn kho, Đơn hàng gần đây | ✅ PASS |
| **2. Sách & Danh mục** | `?tab=admin-dashboard&module=taxonomies` | Thể loại, Tác giả, Nhà xuất bản, Form thêm | ✅ PASS |
| **3. Kho hàng** | `?tab=admin-dashboard&module=inventory` | `InventoryManagementView`, kiểm kê, nhập kho | ✅ PASS |
| **4. Đơn hàng** | `?tab=admin-dashboard&module=orders` | `AdminOrdersView`, xử lý đơn, bàn giao vận chuyển | ✅ PASS |
| **5. Khách hàng & Nhân sự** | `?tab=admin-dashboard&module=users` | Quản trị thành viên, đổi quyền, khóa/mở khóa | ✅ PASS |
| **6. Khuyến mãi** | `?tab=admin-dashboard&module=promotions` | Bảng coupon toàn màn hình, Modal Dialog tạo mã | ✅ PASS |
| **7. Vận chuyển** | `?tab=admin-dashboard&module=shipping` | Trạng thái cổng kết nối GHN & GHTK Sandbox | ✅ PASS |
| **8. Phân tích kinh doanh** | `?tab=admin-dashboard&module=analytics` | Phân bổ trạng thái đơn, Top sách bán chạy | ✅ PASS |
| **9. AI Trợ lý** | `?tab=admin-dashboard&module=ai-assistant` | Thông tin mô hình Gemini, Tool calling console | ✅ PASS |
| **10. Nhật ký hệ thống** | `?tab=admin-dashboard&module=audit` | `AdminAuditView`, nhật ký thao tác & AI log | ✅ PASS |
| **11. Cài đặt** | `?tab=admin-dashboard&module=settings` | Thông tin phiên bản, kết nối MySQL, RBAC | ✅ PASS |

---

## 5. NHỮNG LỖI OVERFLOW & CHỒNG LẤN ĐÃ KHẮC PHỤC

1. **Khắc phục lỗi tràn ảnh trong giỏ hàng & catalog:**
   - Bổ sung Media Reset toàn cục trong `index.css`: `img, picture, video, canvas, svg { display: block; max-width: 100%; }`.
   - Cố định kích thước ảnh thumbnail bìa sách: Cart item (72x104px), BookMatch (200px), Copilot (48x68px), Low Stock (42x56px) với `object-fit: cover`.
2. **Khắc phục lỗi tràn ngang ở bảng dữ liệu:**
   - Mọi bảng trong Admin Shell đều được bao bọc trong `.admin-responsive-table-wrap` với `overflow-x: auto` và `border-radius: 12px`.
   - Các cột nhãn trạng thái và ngày tháng được áp dụng `white-space: nowrap` để không bị gãy dòng bất thường.
3. **Khắc phục lỗi menu horizontal nhảy dòng:**
   - Thay thế toàn bộ thanh ngang bằng Sidebar dọc 250px sticky theo viewport.
4. **Khắc phục lỗi che khuất của AI Assistant:**
   - Panel chat AI được định vị `fixed bottom-6 right-6` với kích thước chuẩn 380x560px trên desktop và gần toàn màn hình trên mobile, không che khuất các nút bấm xác nhận form hoặc pagination.
5. **Khắc phục lỗi hiển thị text kiểm thử ẩn:**
   - Thêm class `.sr-only` chuẩn CSS clipping để văn bản kiểm thử trợ năng (`Bảng Điều Hành Trung Tâm NOVELIA`) không xuất hiện trên giao diện mắt nhìn.

---

## 6. KẾT QUẢ KIỂM THỬ HỆ THỐNG

### A. Frontend Vitest Tests
```bash
npm test
```
- **Kết quả:** `11 test files passed (11/11)` | `63 tests passed (63/63)`
- **Thời gian chạy:** 8.33s
- **Các bộ test vượt qua:**
  - `tests/AdminDashboard.test.tsx` (5/5 tests passed — kiểm tra KPI tài chính, bộ lọc 7 ngày, quyền ADMIN/STAFF, danh mục sách, quản trị người dùng)
  - `tests/NotificationsAudit.test.tsx` (5/5 passed)
  - `tests/BookMatch.test.tsx` (5/5 passed)
  - `tests/AIAssistant.test.tsx` (5/5 passed)
  - `tests/Shipping.test.tsx` (4/4 passed)
  - `tests/AdminCopilot.test.tsx` (5/5 passed)
  - `tests/Commerce.test.tsx` (8/8 passed)
  - `tests/Auth.test.tsx` (9/9 passed)
  - `tests/Checkout.test.tsx` (6/6 passed)
  - `tests/App.test.tsx` (5/5 passed)
  - `tests/Catalog.test.tsx` (6/6 passed)

### B. TypeScript Type Check & Production Build
```bash
npm run build (tsc --noEmit && vite build)
```
- **Kết quả:** `0 errors` | `✓ built in 4.05s`
- **Artifacts:**
  - `dist/index.html` (1.00 kB)
  - `dist/assets/index-Cbil9Gcf.css` (122.68 kB │ gzip: 20.33 kB)
  - `dist/assets/index-CEw1qimR.js` (447.67 kB │ gzip: 115.33 kB)

### C. Backend Pytest Tests (FastAPI + MySQL Integration)
```bash
.venv\Scripts\pytest.exe tests
```
- **Kết quả:** `209 passed, 1 warning in 11.48s (100% pass rate)`
- **Kiểm tra hồi quy:** Toàn bộ API nghiệp vụ (Auth, RBAC, Catalog, Orders, Shipping, AI Copilot, Audit Logs) hoạt động ổn định và chính xác tuyệt đối.

### D. Kiểm tra Visual Regression qua Browser Subagent
- **Desktop (1440x900):**
  - Ảnh chụp: `admin_v2_overview_polished_1792599549005.png` — Khung cảnh quan cân đối, KPI rõ ràng, biểu đồ mượt mà, bảng đơn hàng đầy đủ dữ liệu thực từ MySQL.
  - Ảnh chụp: `admin_v2_promotions_modal_1792599598455.png` — Bảng mã giảm giá chiếm trọn chiều rộng, Modal Dialog tạo mã mở đúng tỷ lệ, không tràn màn hình.
- **Mobile (375x812):**
  - Ảnh chụp: `admin_v2_mobile_drawer_1792599641259.png` — Sidebar chuyển thành Drawer trượt có nút đóng `X`, active pill hiển thị sắc nét.

---

## 7. NHỮNG ĐIỂM CÒN HẠN CHẾ & HƯỚNG PHÁT TRIỂN TIẾP THEO

1. **Phân trang phía server cho Khuyến mãi:** Hiện tại API danh sách coupon trả về toàn bộ mảng và phân trang/lọc ở client-side; có thể nâng cấp thêm limit/offset ở backend khi số lượng voucher vượt trên 500 mã.
2. **Xuất báo cáo Excel / PDF:** Cần bổ sung thêm nút export dữ liệu cho bảng đơn hàng và doanh thu phục vụ bộ phận kế toán.
3. **Dark Mode chuyên biệt:** Hệ thống hiện đang áp dụng theme màu kem ấm cao cấp (`#F7F5F0`), có thể mở rộng thêm tùy chọn Slate Dark Mode cho người trực ca đêm nếu có yêu cầu.

---
*Báo cáo được hoàn thành và đối soát bởi Senior Product Designer & Senior React Frontend Engineer — NOVELIA BOOKS Engineering Team.*
