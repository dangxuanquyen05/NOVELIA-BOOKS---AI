# NOVELIA BOOKS — STOREFRONT UI/UX AUDIT (V3)

> **Báo cáo kiểm thử & Audit giao diện Storefront**  
> **Phiên bản:** Storefront Redesign V3  
> **Đối tượng:** Khách hàng, UI/UX Designer, Frontend Engineer  
> **Trạng thái:** Hoàn thành audit — Sẵn sàng tái cấu trúc  

---

## 1. TỔNG QUAN HIỆN TRẠNG GIAO DIỆN

Trước khi thực hiện Redesign V3 theo mẫu thiết kế tham khảo (Premium Editorial Bookstore), chúng tôi đã tiến hành chụp màn hình và phân tích toàn diện mã nguồn frontend:

- **Viewport kiểm tra ban đầu:** `1440x900px`, `768x1024px`, `375x812px`.
- **Entry point CSS:** `frontend/src/index.css` (Vanilla CSS bundle qua Vite).
- **Trang chính:** `frontend/src/components/CatalogStorefront.tsx`, `Header.tsx`, `BookMatchSection.tsx`, `BookCard.tsx`, `App.tsx`.

---

## 2. NGUYÊN NHÂN LỖI GIAO DIỆN & CHI TIẾT TỪNG THÀNH PHẦN

### 2.1. Lỗi CSS Entry Point & Tailwind Xung Đột
- **Hiện tượng:** Khối **BookMatch AI** hiển thị như các đoạn HTML thô, các tựa sách bị xếp dọc tuần tự, nút bấm thô ráp không có nền/viền đúng chuẩn, text tràn và không có hiệu ứng hover.
- **Nguyên nhân cốt lõi:** Trong file `BookMatchSection.tsx` và `CatalogStorefront.tsx`, các class tiện ích Tailwind (như `flex flex-col sm:flex-row`, `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`, `p-6 rounded-3xl bg-slate-900`, `max-w-7xl mx-auto`) được sử dụng nhưng project **chưa từng cấu hình Tailwind CSS / PostCSS** trong Vite. Vite chỉ đóng gói trực tiếp `frontend/src/index.css`. Vì vậy, 100% các class Tailwind đó bị trình duyệt bỏ qua, khiến BookMatch AI trở thành HTML unstyled.
- **Giải pháp:** Viết định nghĩa CSS thuần rõ ràng, có cấu trúc trong `frontend/src/index.css` cho toàn bộ các component của BookMatch và Storefront, loại bỏ sự phụ thuộc vào các utility class ảo chưa được compile.

---

### 2.2. Header & Thanh Điều Hướng (Navigation)
- **Vấn đề phát hiện:**
  1. Header chứa badge kỹ thuật: `PHASE 1-3: FOUNDATION & AUTH RBAC | PHASE 4: CATALOG | PHASE 5: INVENTORY & COMMERCE` — đây là thông tin nội bộ giai đoạn phát triển, không được phép hiển thị trên giao diện người mua sách.
  2. Không có thanh điều hướng menu chính ("Trang chủ", "Cửa hàng", "Danh mục", "Tác giả", "Nhà xuất bản", "Blog").
  3. Không có thanh tìm kiếm nhanh (Global Search Bar) trên header có placeholder tiếng Việt (`Tìm kiếm sách, tác giả, thể loại, ISBN...`).
  4. Thanh tab điều hướng của hệ thống hiện tại (`nav-tabs-bar`) xếp 10-12 nút bấm liên tiếp trên cùng một dòng, gây rối mắt, phá vỡ bố cục bookstore cao cấp và vỡ layout trên tablet/mobile.
  5. Menu người dùng chưa có Avatar pill/dropdown tinh tế để xem hồ sơ, đơn hàng hoặc đăng xuất.
- **Giải pháp:** Thiết kế lại `Header.tsx` đồng bộ với mẫu tham khảo: Logo NOVELIA BOOKS + slogan "Books for a better tomorrow", menu links có gạch chân active, search bar bo tròn dạng pill, wishlist badge, cart badge, và user menu dropdown / mobile drawer.

---

### 2.3. Khối Hero Section
- **Vấn đề phát hiện:**
  1. Bố cục hiện tại là một khung đơn chữ nhật ở giữa màn hình (`storefront-hero`), bên phải để trống một khoảng trắng khổng lồ mất cân đối.
  2. Thiếu nhãn thương hiệu nhỏ ("SÁCH HAY THAY ĐỔI CUỘC SỐNG").
  3. Tiêu đề chưa mang phong cách Editorial Bookstore thanh lịch bằng font Serif tiếng Việt ("Mở ra thế giới trong từng trang sách").
  4. Thiếu thanh tìm kiếm nổi bật ngay trong Hero với nút CTA "Tìm kiếm" màu đồng ấm áp.
  5. Thiếu hàng 4 điểm tin cậy (Trust Badges): Giao hàng toàn quốc, Sách chính hãng, Hỗ trợ 24/7, Đổi trả dễ dàng trong 7 ngày.
  6. Cột phải thiếu bố cục ảnh tĩnh vật sách nghệ thuật (Still-life composition) với chiều sâu, góc đọc sách thư thái và trích dẫn truyền cảm hứng đọc sách.
- **Giải pháp:** Xây dựng bố cục 2 cột (Desktop) và 1 cột (Mobile). Cột trái chứa nội dung kích thích đọc và tìm kiếm sách; cột phải chứa still-life sách chân thực có đổ bóng, sách đứng, sách chồng và quote card nghệ thuật.

---

### 2.4. Khối BookMatch AI Section
- **Vấn đề phát hiện:**
  1. Bị vỡ layout hoàn toàn do class Tailwind không có CSS hỗ trợ.
  2. Thiếu badge nhận diện thương hiệu `AI | BOOKMATCH AI`.
  3. Thiếu bố cục banner giới thiệu tính năng cá nhân hóa riêng biệt với nút CTA `Khám phá BookMatch →`.
  4. Chưa có khung hiển thị trích dẫn gợi mở: *"Mỗi người đều có một hành trình đọc riêng..."* cùng hình minh họa nghệ thuật.
- **Giải pháp:** Tái cấu trúc thành banner BookMatch cao cấp nền sáng ấm/ivory viền ngọc bích nhạt, hiển thị đầy đủ thông tin đề xuất thực tế từ API `/api/v1/recommendations/personalized`, có loading skeleton, làm mới đề xuất, và mini card đề xuất sách thật.

---

### 2.5. Thanh Danh Mục Sách (Category Chips Bar)
- **Vấn đề phát hiện:**
  1. Hiện tại dùng nhãn "Chuyên mục nổi bật:" với các nút xám thô ráp.
  2. Không có icon đại diện cho từng thể loại sách (Văn học, Kinh tế, Kỹ năng, Thiếu nhi, Tâm lý, Khoa học, Lịch sử, Công nghệ, Ngoại ngữ).
  3. Chưa có thanh cuộn ngang mượt mà trên thiết bị di động.
- **Giải pháp:** Xây dựng Category Chips Bar với icon Lucide phù hợp cho từng thể loại, nút "Tất cả" active với màu nền Navy sang trọng, hỗ trợ bấm lọc trực tiếp qua API backend.

---

### 2.6. Khối Danh Sách Sách & Book Cards (Product Listing)
- **Vấn đề phát hiện:**
  1. Không phân khu vực rõ ràng: Thiếu các section tiêu đề như "🔥 Sách được yêu thích", "Sách bán chạy", "Sách mới", "Gợi ý dành cho bạn".
  2. Thẻ sách (`BookCard`) hiện tại có nút hành động ẩn trong overlay hover, trên mobile rất khó thao tác.
  3. Thẻ sách thiếu nút bấm kép tiện dụng: Nút `Thêm vào giỏ` màu Navy nổi bật và nút `Yêu thích ♡` hình tròn/vuông bên cạnh như mẫu thiết kế chuẩn.
  4. Thiếu hiển thị sao đánh giá và số lượng đánh giá thực tế (hoặc fallback chuẩn khi chưa có).
  5. Lưới sản phẩm chưa responsive tối ưu (trên màn hình 1440px cần hiển thị 4–5 cột cân đối, không để khoảng trống vô nghĩa).
- **Giải pháp:** Chuẩn hóa BookCard theo tỷ lệ 2:3, viền ấm nhẹ, bóng đổ mềm mại, hiển thị tên sách clamp 2 dòng, tác giả, giá tiền VND format chuẩn, trạng thái tồn kho thực tế và bộ nút kép trực quan.

---

### 2.7. Nút Floating Chat AI Assistant
- **Vấn đề phát hiện:** Hiện tại là thanh dài `NOVELIA AI Trợ lý Sách Thông Minh` màu cam lớn ở góc phải dưới, dễ che khuất thông tin thẻ sách cuối trang hoặc che nút thao tác.
- **Giải pháp:** Thiết kế lại thành nút tròn Floating Action Button (FAB) màu Dark Navy viền vàng đồng sang trọng, icon chat bubble và nhãn nhỏ `AI Assistant`, bấm mở panel chat mượt mà, hỗ trợ tốt trên mobile.

---

## 3. KẾ HOẠCH TRIỂN KHAI SỬA ĐỔI SOURCE CODE

| Bước | File mục tiêu | Nội dung triển khai |
| :--- | :--- | :--- |
| **B1** | `frontend/src/index.css` | Bổ sung Design Tokens và toàn bộ CSS cho Header V3, Hero 2-column, BookMatch Banner V3, Category Chips, Book Cards V3, Sections Grid. |
| **B2** | `frontend/src/components/Header.tsx` | Thiết kế lại Header V3 hoàn chỉnh: Logo + Subtitle, Menu chính, Search bar tiếng Việt, Badges Wishlist/Cart, User Account, Mobile Drawer. |
| **B3** | `frontend/src/components/BookCard.tsx` | Tái cấu trúc thẻ sách: bìa tỷ lệ chuẩn, tên clamp 2 dòng, tác giả, giá, tồn kho thực tế, nút [Thêm vào giỏ] + [Wishlist]. |
| **B4** | `frontend/src/components/BookMatchSection.tsx` | Redesign BookMatch AI thành card banner nghệ thuật với API thật, giữ nguyên các test id và hàm telemetry. |
| **B5** | `frontend/src/components/CatalogStorefront.tsx` | Tích hợp Hero 2 cột, BookMatch AI, Category Chips bar, các Section tuyển chọn ("Sách được yêu thích", "Tất cả tác phẩm"), bộ lọc & tìm kiếm đồng bộ API. |
| **B6** | `frontend/src/App.tsx` | Tích hợp Header V3 mới với điều hướng các tab (Catalog, Wishlist, Orders, Profile, Admin Dashboard). |
| **B7** | Kiểm thử & Nghiệm thu | Chạy `npm test` (63 tests), `npm run build`, kiểm tra browser viewport 1440px, 768px, 375px. |
