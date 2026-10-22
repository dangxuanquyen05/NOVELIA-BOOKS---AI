# NOVELIA BOOKS — BÁO CÁO AUDIT GIAO DIỆN VÀ TRẢI NGHIỆM NGƯỜI DÙNG (UI/UX AUDIT)
**Dự án:** NOVELIA BOOKS — Enterprise E-Commerce Bookstore & AI Intelligence System  
**Ngày thực hiện:** 21/10/2026  
**Chuyên gia:** Senior UI/UX Designer, Design System Architect & Senior Frontend Engineer  
**Trạng thái kiểm tra:** Thực hiện trực tiếp trên môi trường đang chạy (`http://localhost:5173/`, FastAPI `http://127.0.0.1:8000`, MySQL Server `3306`).

---

## 1. TỔNG QUAN KIẾN TRÚC & TUÂN THỦ AGENTS.MD

Theo chỉ thị cốt lõi tại `AGENTS.md`:
1. **Backend là thẩm quyền tối cao:** Mọi tính toán tiền tệ (`DECIMAL(12,2)`), thuế, phí vận chuyển, trừ tồn kho và phân quyền phải được xác thực tại backend trong ACID transaction. Giao diện frontend là tầng trình diễn và tương tác, không được tự ý sửa đổi logic nghiệp vụ.
2. **RBAC nghiêm ngặt:** Hệ thống phân quyền chặt chẽ 3 vai trò: `CUSTOMER`, `STAFF`, `ADMIN`.
3. **AI có kiểm soát:** Novelia AI và BookMatch hoạt động dưới dạng cố vấn có ràng buộc ngữ cảnh người dùng, tool calling có xác nhận 2 pha cho thao tác sửa đổi dữ liệu (mutations).
4. **Không dùng mock giả tạo trong sản phẩm:** Dữ liệu hiển thị phải phản ánh đúng cơ sở dữ liệu thật MySQL (`novelia_books`), ngoại trừ chế độ test chuyên biệt.

---

## 2. HIỆN TRẠNG ROUTING, LAYOUT & COMPONENT

### 2.1 Cấu trúc Navigation & Router
- Ứng dụng hiện tại **không sử dụng React Router** dạng URL path đa tầng, mà quản lý trạng thái điều hướng qua state tập trung `activeTab` trong `App.tsx` với 11 tab chính:
  - `'health'`: Trạng thái kết nối hệ thống (FastAPI Backend + MySQL Server).
  - `'catalog'`: Cửa hàng sách & danh mục sản phẩm (Storefront).
  - `'login'`: Đăng nhập tài khoản.
  - `'register'`: Đăng ký tài khoản khách hàng mới.
  - `'profile'`: Hồ sơ người dùng & đổi mật khẩu.
  - `'addresses'`: Sổ địa chỉ giao hàng.
  - `'wishlist'`: Tác phẩm yêu thích của khách hàng.
  - `'orders'`: Lịch sử và chi tiết đơn hàng cá nhân.
  - `'inventory'`: Quản trị tồn kho thời gian thực (STAFF/ADMIN).
  - `'admin-orders'`: Quản lý đơn hàng, điều phối vận chuyển (STAFF/ADMIN).
  - `'admin-dashboard'`: Bảng điều hành kinh doanh tổng hợp (STAFF/ADMIN).
- **Vấn đề phát hiện:** Mặc định khi người dùng truy cập trang chủ, `activeTab` khởi tạo là `'health'`. Khách hàng lập tức nhìn thấy bảng kiểm tra kỹ thuật (MySQL SELECT 1, ping backend, hướng dẫn Workbench) thay vì nhìn thấy Cửa hàng sách cao cấp.
- Thanh điều hướng (`nav-tabs-bar`) được bố trí dạng một dải nút phẳng ngang, không có CSS định hình trong `index.css`, gom chung nút khách hàng với nút quản trị viên.

### 2.2 Danh mục Layouts & Components hiện hữu
- **Giao diện dùng chung & Khung trang:**
  - `Header.tsx`: Thanh tiêu đề mang huy hiệu dev *"Phase 1-3: Foundation & Auth RBAC | Phase 4: Catalog | Phase 5: Inventory & Commerce"*, thiếu thanh tìm kiếm tích hợp và danh mục thả xuống.
  - `NotificationCenter.tsx`: Chuông thông báo realtime tích hợp SSE.
  - `CartDrawer.tsx`: Ngăn trượt giỏ hàng bên phải màn hình.
  - `CheckoutModal.tsx`: Hộp thoại đặt hàng đa bước (Địa chỉ, Voucher, Vận chuyển GHN/GHTK, Thanh toán COD/VietQR Napas).
  - `DiagnosticGuide.tsx` & `StatusCard.tsx`: Thẻ đo kiểm trạng thái hệ thống.
- **Storefront & Catalog:**
  - `CatalogStorefront.tsx`: Danh mục sách, bộ lọc bên trái (`FilterSidebar.tsx`), phân trang.
  - `BookCard.tsx`: Card hiển thị sách, nút yêu thích, nút mua nhanh, nhãn giảm giá.
  - `BookDetailModal.tsx`: Hộp thoại chi tiết tác phẩm, tác giả, tồn kho, mô tả, đánh giá.
  - `BookMatchSection.tsx`: Khu vực gợi ý AI BookMatch theo thể loại và sở thích.
  - `ReviewSection.tsx`: Đánh giá 5 sao từ khách hàng đã mua sách.
- **Xác thực & Khách hàng:**
  - `LoginForm.tsx`, `RegisterForm.tsx`, `ProfileView.tsx`, `AddressBookView.tsx`, `WishlistView.tsx`, `OrderHistoryView.tsx`.
- **Quản trị & Điều hành:**
  - `AdminDashboardView.tsx` (1663 dòng): Gồm KPI Overview, Taxonomies (Danh mục, Tác giả, Nhà xuất bản), User Governance (Phân quyền người dùng), Khuyến mãi (Coupons).
  - `AdminOrdersView.tsx`: Quản lý danh sách đơn hàng, xuất kho, điều phối vận chuyển, in mã vận đơn.
  - `InventoryManagementView.tsx`: Kiểm kê kho sách, cập nhật số lượng vật lý và khả dụng.
  - `AdminAuditView.tsx`: Tra cứu nhật ký kiểm toán hệ thống và nhật ký AI.
- **Trí tuệ nhân tạo:**
  - `NoveliaAIAssistant.tsx`: Chatbot AI hỗ trợ mua sách (Customer) và Copilot tra cứu quản trị (Staff/Admin).

---

## 3. CÁC VẤN ĐỀ CHI TIẾT ĐƯỢC PHÁT HIỆN QUA AUDIT TRỰC TIẾP

### 3.1 Bố cục & Nhịp điệu thị giác (Layout & Visual Rhythm)
- **Thiếu nhịp điệu thương hiệu sách:** Toàn bộ website được bao phủ bởi nền tối đen/xanh không gian (`#070D1F`), giống một sàn giao dịch tiền mã hóa hoặc bảng điều khiển server viễn thông hơn là một hiệu sách văn học cao cấp.
- **Trang chủ bị nén thành một khối danh mục:** Storefront hiện tại chỉ có một banner màu xanh đậm với vài gạch đầu dòng, ngay dưới là BookMatch và lưới sản phẩm kèm sidebar. Thiếu hoàn toàn các phân khu biên tập: Sách Mới Tuyển Chọn, Sách Bán Chạy Trong Tuần, Bộ Sưu Tập Tác Giả Tiêu Biểu, Banner Khuyến Mãi Biên Tập.
- **Header đơn điệu:** Chiếm diện tích nhưng không có thanh tìm kiếm sách ngay tại trung tâm, thiếu menu thể loại nhanh (Văn học, Kinh tế, Tâm lý, Thiếu nhi...), buộc người dùng phải kéo xuống sidebar mới lọc được.

### 3.2 Hệ màu sắc (Color Palette)
- **Màu hiện tại:** Nền `#070D1F`, `#0D1733`, card viền phát sáng `--accent-gold-glow` (`rgba(229, 168, 105, 0.25)`), chữ trắng gắt `#FFFFFF`.
- **Hạn chế:** Tạo cảm giác chói mắt khi đọc mô tả sách dài. Bìa sách thật (vốn có nhiều màu sắc và nền trắng/vàng) bị tương phản quá gắt trên nền tối mịt, làm giảm vẻ đẹp của thiết kế bìa sách in.
- **Mục tiêu mới:** Chuyển sang phong cách **PREMIUM EDITORIAL BOOKSTORE**:
  - Background: Warm ivory `#F7F5F0` (màu giấy in cao cấp).
  - Surface/Card: Trắng tinh khiết `#FFFFFF` hoặc giấy kem sáng `#FCFBF9`.
  - Primary text: Dark ink `#202536` cho độ tương phản đọc sách tối ưu theo tiêu chuẩn WCAG AAA.
  - Brand Primary: Deep Navy `#24324A` (thanh lịch, uy tín).
  - Accent: Muted Copper / Warm Ochre `#C27D38` hoặc Muted Teal `#2A7B88`.
  - Border: Subtle warm grey `#E5E0D8`.

### 3.3 Typography & Phông chữ
- Phông chữ hiện dùng `Plus Jakarta Sans` và `Playfair Display`.
- Phân cấp kích thước (type scale) chưa chuẩn hóa: Tiêu đề thẻ sách (`.book-card-title`) bị giới hạn 2 dòng nhưng cỡ chữ 0.98rem hơi thô; khoảng cách dòng (line-height) giữa các thẻ chưa tạo cảm giác trang nhã của ngành xuất bản sách.
- Thiếu các nhãn thể loại, metadata ISBN, tên nhà xuất bản có phong cách typographic tinh tế.

### 3.4 Card sản phẩm & Xử lý ảnh sách
- Tỷ lệ khung ảnh bìa `2 / 3` đã có nhưng chưa có hiệu ứng đổ bóng mô phỏng gáy sách in (book spine shadow & paper elevation).
- Các nút tương tác nhanh (Thêm giỏ, Yêu thích) bị chồng lấn dạng lớp phủ đen (`.book-card-overlay`) che khuất hoàn toàn bìa sách khi hover.
- Nút yêu thích (`book-card-wishlist-btn`) nằm lơ lửng góc trên bìa sách dễ che mất tên tác giả hoặc tên tựa sách in trên góc bìa.
- Ảnh fallback hiện trỏ tới link Unsplash ngẫu nhiên, cần có fallback bìa sách SVG thanh lịch mang nhận diện NOVELIA BOOKS khi ảnh bị lỗi mạng.

### 3.5 Bảng điều hành Admin (Admin Shell & Dashboard)
- `AdminDashboardView.tsx` hiện tại là một file quá lớn (1663 dòng, 70KB) tích hợp cả 4 tab con và gọi thêm `AdminAuditView`.
- Bố cục thiếu sidebar điều hướng cố định (collapsible sidebar) chuẩn Enterprise Admin, hiện đang sử dụng tab lồng trong tab khiến người quản trị mất phương hướng.
- `AdminOrdersView` và `InventoryManagementView` lại nằm ở tab ngoài cấp cao nhất trong `App.tsx` thay vì được tích hợp đồng bộ vào phân hệ Quản trị.
- Biểu đồ timeline và phân bổ trạng thái đơn hàng sử dụng các thanh HTML tùy biến với màu sắc chưa hài hòa.

### 3.6 Trợ lý Novelia AI & Copilot
- Widget chat mở ra cửa sổ nhỏ cố định góc phải, kích thước 420px hơi hẹp khi hiển thị bảng phân tích tài chính hoặc danh sách nhiều thẻ sách từ tool calling.
- Phát hiện 3 lỗi cú pháp ESLint trong `NoveliaAIAssistant.tsx` (escape vô nghĩa `\)` tại các biểu thức regex dòng 309, 343, 361) khiến lệnh `npm run lint` bị dừng với mã lỗi 1.

---

## 4. KẾT QUẢ KIỂM THỬ BAN ĐẦU (BASELINE TEST RESULTS)

- **Vitest Frontend:** 11 test suites (63 tests) **ĐỀU VƯỢT QUA (PASS 100%)** trong 9.25s.
  - Các ràng buộc test: `App.test.tsx` kiểm tra nhãn `Phase 1-3: Foundation & Auth RBAC`, `Hướng dẫn Thiết lập MySQL Workbench`, và các testid quan trọng (`status-card-mysql-database`, `book-card-1`, `dispatch-order-modal`, v.v.). Redesign bắt buộc phải bảo tồn trọn vẹn các test này.
- **Production Build:** `npm run build` thành công trong 3.23s (dist: index.html 1.00 kB, js 415.26 kB, css 94.77 kB).
- **ESLint:** Gặp 3 lỗi tại `NoveliaAIAssistant.tsx` cần khắc phục ngay.
- **Trạng thái dịch vụ kết nối thật:**
  - Backend FastAPI: `http://127.0.0.1:8000` — `ONLINE / HEALTHY` (~73ms).
  - MySQL Database: `localhost:3306` — `CONNECTED / HEALTHY` (Database `novelia_books`).

---

## 5. KẾ HOẠCH TRIỂN KHAI REDESIGN THEO TỪNG GIAI ĐOẠN

1. **Giai đoạn 1 — Design System & Design Tokens:**
   - Xây dựng bảng biến CSS tokens chuẩn `PREMIUM EDITORIAL BOOKSTORE` (Ivory `#F7F5F0`, Ink `#202536`, Navy `#24324A`, Copper `#C27D38`, Border `#E5E0D8`).
   - Xây dựng bộ component cốt lõi: Button, Input, Select, Badge, Card, Modal, Dropdown, Table, Skeleton, Empty State, Notification Toast.
   - Sửa lỗi cú pháp lint trong `NoveliaAIAssistant.tsx`.

2. **Giai đoạn 2 — Đại tu Storefront & Book Catalog:**
   - Nâng cấp Header: Logo thương hiệu sách cao cấp, thanh tìm kiếm sách tức thì, điều hướng danh mục trực quan, giỏ hàng & wishlist rõ ràng.
   - Thiết kế lại Trang chủ: Hero biên tập xuất bản đỉnh cao, phân khu Sách Mới, Sách Nổi Bật, BookMatch AI độc quyền, Banner chương trình ưu đãi, Footer xuất bản thương mại trang trọng.
   - Chuẩn hóa Product Card: Tỷ lệ ảnh chuẩn, gáy sách nghệ thuật, typography phân cấp rõ ràng, trạng thái tồn kho trực quan, nút yêu thích và giỏ hàng tinh tế.
   - Làm mới Modal Chi tiết tác phẩm, Đánh giá và Gợi ý liên quan.

3. **Giai đoạn 3 — Đại tu Cart, Checkout & Customer Portal:**
   - Ngăn kéo Giỏ hàng (`CartDrawer`) & Quy trình Đặt hàng (`CheckoutModal`): Tách bạch chi phí, thông tin vận chuyển, mã giảm giá và phương thức thanh toán minh bạch.
   - Khu vực Khách hàng: Hồ sơ tài khoản, Sổ địa chỉ, Lịch sử & Chi tiết đơn hàng, Theo dõi vận chuyển thời gian thực.

4. **Giai đoạn 4 — Đại tu Bảng điều hành Quản trị (Admin Portal):**
   - Xây dựng Admin Shell thống nhất với Sidebar thu gọn chuyên nghiệp, Header Breadcrumb, chuyển đổi mượt mà giữa Tổng quan, Đơn hàng, Tồn kho, Phân loại, Người dùng, Khuyến mãi và Audit logs.
   - Tối ưu hóa bảng dữ liệu, KPI cards, cảnh báo tồn kho và bộ lọc thời gian.

5. **Giai đoạn 5 — Tinh chỉnh Novelia AI Assistant & Copilot:**
   - Giao diện chat sang trọng, panel rộng rãi, mini-book card sắc sảo, hiển thị trạng thái suy luận/tool calling và hộp thoại xác nhận an toàn cho thao tác cập nhật dữ liệu.

6. **Giai đoạn 6 — Kiểm thử, Đo lường Responsive & Lập Báo cáo Nghiệm thu:**
   - Kiểm tra đa kích thước (375px, 768px, 1024px, 1440px), chạy lại toàn bộ 63 tests, kiểm tra lint, type-check, build production và chụp ảnh kiểm chứng.
