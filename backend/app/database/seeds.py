"""Idempotent seed data for NOVELIA BOOKS catalog, RBAC roles, and initial inventory.

All data entries are tagged with [DEMO SEED] in compliance with Phase 2 governance rules.
No actual personal data, secrets, or fake completed orders are injected.
Safe to run repeatedly without generating duplicate records.
"""

from datetime import datetime, timezone, date
from decimal import Decimal
import logging
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.models.user import Role, User, UserRole
from app.core.security import get_password_hash
from app.models.catalog import Publisher, Author, Category, Book, BookAuthor, BookCategory, BookImage
from app.models.inventory import Inventory, InventoryTransaction

logger = logging.getLogger("novelia.seeds")

DEMO_TAG = "[DEMO SEED]"

# 1. Standard RBAC Roles
ROLES_DATA = [
    {"name": "CUSTOMER", "description": "Standard retail customer with browsing, cart, order, and AI advisory access"},
    {"name": "STAFF", "description": "Store operational staff with inventory, order processing, and catalog update rights"},
    {"name": "ADMIN", "description": "System administrator with full RBAC, financial reports, and system configuration privileges"},
]

# Standard Demo Accounts for evaluation & defense
DEMO_USERS_DATA = [
    {
        "email": "admin@novelia.vn",
        "password": "AdminPass123!",
        "full_name": "Quản trị viên Hệ thống",
        "phone": "0901234567",
        "roles": ["ADMIN", "STAFF"],
    },
    {
        "email": "staff@novelia.vn",
        "password": "StaffPass123!",
        "full_name": "Nhân viên Điều vận",
        "phone": "0902345678",
        "roles": ["STAFF"],
    },
    {
        "email": "reader@novelia.vn",
        "password": "ReaderPass123!",
        "full_name": "Độc giả Thân thiết",
        "phone": "0903456789",
        "roles": ["CUSTOMER"],
    },
    {
        "email": "newbie@novelia.vn",
        "password": "ReaderPass123!",
        "full_name": "Độc giả Mới",
        "phone": "0904567890",
        "roles": ["CUSTOMER"],
    },
]

# 2. Publishers (8 realistic publishers)
PUBLISHERS_DATA = [
    {"name": "NXB Trẻ", "slug": "nxb-tre", "contact_info": "contact@nxbtre.com.vn", "website": "https://nxbtre.com.vn"},
    {"name": "NXB Kim Đồng", "slug": "nxb-kim-dong", "contact_info": "cskh@nxbkimdong.com.vn", "website": "https://nxbkimdong.com.vn"},
    {"name": "NXB Hội Nhà Văn", "slug": "nxb-hoi-nha-van", "contact_info": "info@nxbhoinhavan.vn", "website": "https://nxbhoinhavan.vn"},
    {"name": "NXB Phụ Nữ Việt Nam", "slug": "nxb-phu-nu-viet-nam", "contact_info": "truyenthong@nxbphunu.com.vn", "website": "https://nxbphunu.com.vn"},
    {"name": "NXB Tổng Hợp TP.HCM", "slug": "nxb-tong-hop-tphcm", "contact_info": "tonghop@nxbhcm.com.vn", "website": "https://nxbhcm.com.vn"},
    {"name": "NXB Thế Giới", "slug": "nxb-the-gioi", "contact_info": "thegioi@nxbthegioi.vn", "website": "https://nxbthegioi.vn"},
    {"name": "NXB Lao Động", "slug": "nxb-lao-dong", "contact_info": "nxblaodong@gmail.com", "website": "https://nxblaodong.com.vn"},
    {"name": "NXB Văn Học", "slug": "nxb-van-hoc", "contact_info": "nxbvanhoc@hn.vnn.vn", "website": "https://nxbvanhoc.vn"},
]

# 3. Categories (10 genres)
CATEGORIES_DATA = [
    {"name": "Văn học Việt Nam", "slug": "van-hoc-viet-nam", "description": "Tác phẩm kinh điển và hiện đại của các văn nhân Việt Nam", "display_order": 1},
    {"name": "Văn học Nước ngoài", "slug": "van-hoc-nuoc-ngoai", "description": "Tiểu thuyết, truyện ngắn xuất sắc dịch từ văn học thế giới", "display_order": 2},
    {"name": "Kinh tế & Quản trị", "slug": "kinh-te-quan-tri", "description": "Tư duy khởi nghiệp, quản trị doanh nghiệp, tài chính và đầu tư", "display_order": 3},
    {"name": "Kỹ năng sống & Phát triển", "slug": "ky-nang-song-phat-trien", "description": "Rèn luyện tư duy, phát triển thói quen và kỹ năng mềm", "display_order": 4},
    {"name": "Tâm lý học", "slug": "tam-ly-hoc", "description": "Khám phá chiều sâu tâm lý con người và khoa học hành vi", "display_order": 5},
    {"name": "Khoa học & Công nghệ", "slug": "khoa-hoc-cong-nghe", "description": "Trí tuệ nhân tạo, khoa học máy tính, vật lý và khám phá vũ trụ", "display_order": 6},
    {"name": "Lịch sử & Triết học", "slug": "lich-su-triet-hoc", "description": "Dòng chảy lịch sử nhân loại, tư tưởng triết học phương Đông và phương Tây", "display_order": 7},
    {"name": "Thiếu nhi & Tuổi mới lớn", "slug": "thieu-nhi-tuoi-moi-lon", "description": "Sách tranh, truyện phiêu lưu và bài học nhân văn cho độc giả trẻ", "display_order": 8},
    {"name": "Nghệ thuật & Thiết kế", "slug": "nghe-thuat-thiet-ke", "description": "Hội họa, kiến trúc, nhiếp ảnh và nghệ thuật thị giác", "display_order": 9},
    {"name": "Sách Ngoại văn", "slug": "sach-ngoai-van", "description": "Tác phẩm nguyên bản tiếng Anh, Pháp, Nhật Bản và đa ngôn ngữ", "display_order": 10},
]

# 4. Authors (25 authors)
AUTHORS_DATA = [
    {"name": "Nguyễn Nhật Ánh", "slug": "nguyen-nhat-anh", "nationality": "Việt Nam", "birth_year": 1955, "bio": "Nhà văn chuyên viết cho thiếu nhi và tuổi trẻ được yêu mến nhất Việt Nam."},
    {"name": "Nam Cao", "slug": "nam-cao", "nationality": "Việt Nam", "birth_year": 1915, "bio": "Nhà văn hiện thực xuất sắc của nền văn học Việt Nam thế kỷ 20."},
    {"name": "Vũ Trọng Phụng", "slug": "vu-trong-phung", "nationality": "Việt Nam", "birth_year": 1912, "bio": "Vua phóng sự đất Bắc với những tác phẩm châm biếm xã hội sâu cay."},
    {"name": "Nguyễn Du", "slug": "nguyen-du", "nationality": "Việt Nam", "birth_year": 1765, "bio": "Đại thi hào dân tộc Việt Nam, danh nhân văn hóa thế giới."},
    {"name": "Bảo Ninh", "slug": "bao-ninh", "nationality": "Việt Nam", "birth_year": 1952, "bio": "Nhà văn quân đội nổi tiếng thế giới với tác phẩm Nỗi buồn chiến tranh."},
    {"name": "Tô Hoài", "slug": "to-hoai", "nationality": "Việt Nam", "birth_year": 1920, "bio": "Nhà văn lớn với kiệt tác Dế Mèn phiêu lưu ký gắn liền với nhiều thế hệ."},
    {"name": "Haruki Murakami", "slug": "haruki-murakami", "nationality": "Nhật Bản", "birth_year": 1949, "bio": "Nhà văn đương đại Nhật Bản với phong cách hiện thực huyền ảo quyến rũ."},
    {"name": "George Orwell", "slug": "george-orwell", "nationality": "Vương quốc Anh", "birth_year": 1903, "bio": "Tác giả của những kiệt tác văn học chính trị và phản địa đàng thế giới."},
    {"name": "Yuval Noah Harari", "slug": "yuval-noah-harari", "nationality": "Israel", "birth_year": 1976, "bio": "Nhà sử học, triết gia và tác giả của bộ ba sách Sapiens, Homo Deus và 21 Bài học."},
    {"name": "James Clear", "slug": "james-clear", "nationality": "Hoa Kỳ", "birth_year": 1986, "bio": "Chuyên gia về thói quen, tác giả cuốn sách bán chạy kỷ lục Atomic Habits."},
    {"name": "Dale Carnegie", "slug": "dale-carnegie", "nationality": "Hoa Kỳ", "birth_year": 1888, "bio": "Nhà tiên phong trong nghệ thuật giao tiếp và thuật đắc nhân tâm."},
    {"name": "Daniel Kahneman", "slug": "daniel-kahneman", "nationality": "Hoa Kỳ / Israel", "birth_year": 1934, "bio": "Nhà tâm lý học đoạt giải Nobel Kinh tế, tác giả cuốn Tư duy nhanh và chậm."},
    {"name": "Walter Isaacson", "slug": "walter-isaacson", "nationality": "Hoa Kỳ", "birth_year": 1952, "bio": "Nhà viết tiểu sử hàng đầu về Steve Jobs, Leonardo da Vinci, Einstein và Elon Musk."},
    {"name": "J.K. Rowling", "slug": "jk-rowling", "nationality": "Vương quốc Anh", "birth_year": 1965, "bio": "Tác giả của thiên sử thi thiếu nhi thế giới Harry Potter."},
    {"name": "Antoine de Saint-Exupéry", "slug": "antoine-de-saint-exupery", "nationality": "Pháp", "birth_year": 1900, "bio": "Nhà văn phi công người Pháp, tác giả kiệt tác Hoàng tử bé."},
    {"name": "Paulo Coelho", "slug": "paulo-coelho", "nationality": "Brazil", "birth_year": 1947, "bio": "Tiểu thuyết gia người Brazil với tác phẩm Nhà giả kim dịch ra hơn 80 thứ tiếng."},
    {"name": "Victor Hugo", "slug": "victor-hugo", "nationality": "Pháp", "birth_year": 1802, "bio": "Đại văn hào người Pháp của chủ nghĩa lãng mạn với Những người khốn khổ."},
    {"name": "Franz Kafka", "slug": "franz-kafka", "nationality": "Áo - Hung / Séc", "birth_year": 1883, "bio": "Một trong những tác giả lớn nhất của văn học thế kỷ 20 với Hóa thân và Vụ án."},
    {"name": "Albert Camus", "slug": "albert-camus", "nationality": "Pháp", "birth_year": 1913, "bio": "Triết gia và nhà văn đoạt giải Nobel Văn học, tác giả cuốn Người xa lạ."},
    {"name": "Fyodor Dostoevsky", "slug": "fyodor-dostoevsky", "nationality": "Nga", "birth_year": 1821, "bio": "Đại văn hào Nga khám phá chiều sâu tâm lý con người trong Tội ác và hình phạt."},
    {"name": "Mark Manson", "slug": "mark-manson", "nationality": "Hoa Kỳ", "birth_year": 1984, "bio": "Tác giả của cuốn sách nổi tiếng Nghệ thuật tinh tế của việc đếch quan tâm."},
    {"name": "Morgan Housel", "slug": "morgan-housel", "nationality": "Hoa Kỳ", "birth_year": 1984, "bio": "Chuyên gia tài chính hành vi, tác giả cuốn Tâm lý học về tiền."},
    {"name": "Peter Thiel", "slug": "peter-thiel", "nationality": "Hoa Kỳ", "birth_year": 1967, "bio": "Nhà đầu tư mạo hiểm Thung lũng Silicon, đồng sáng lập PayPal và tác giả Zero to One."},
    {"name": "Ray Dalio", "slug": "ray-dalio", "nationality": "Hoa Kỳ", "birth_year": 1949, "bio": "Nhà sáng lập quỹ đầu cơ Bridgewater Associates, tác giả cuốn sách Các nguyên tắc (Principles)."},
    {"name": "Nguyễn Tuân", "slug": "nguyen-tuan", "nationality": "Việt Nam", "birth_year": 1910, "bio": "Cây bút bậc thầy về tùy bút và ngôn ngữ nghệ thuật Việt Nam."},
]

# 5. Books (35 books with catalog metadata)
BOOKS_DATA = [
    {
        "isbn": "9786041182345",
        "sku": "NOV-LIT-001",
        "title": "Mắt Biếc",
        "slug": "mat-biec",
        "publisher_slug": "nxb-tre",
        "category_slugs": ["van-hoc-viet-nam"],
        "author_slugs": ["nguyen-nhat-anh"],
        "price": Decimal("110000.00"),
        "original_price": Decimal("125000.00"),
        "page_count": 300,
        "weight_grams": 350,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Câu chuyện tình đầu trong sáng, khắc khoải của Ngạn dành cho Hà Lan - cô bạn gái có đôi mắt biếc biếc như bầu trời quê hương Đo Đo.",
        "sample_text": "Tôi gửi tình yêu cho mùa hè, nhưng mùa hè không giữ được. Mùa hè chỉ biết làm nắng gắt và mưa rào...",
        "cover_image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 1, 15),
        "stock": 45,
    },
    {
        "isbn": "9786041182352",
        "sku": "NOV-LIT-002",
        "title": "Cho Tôi Xin Một Vé Đi Tuổi Thơ",
        "slug": "cho-toi-xin-mot-ve-di-tuoi-tho",
        "publisher_slug": "nxb-tre",
        "category_slugs": ["van-hoc-viet-nam", "thieu-nhi-tuoi-moi-lon"],
        "author_slugs": ["nguyen-nhat-anh"],
        "price": Decimal("95000.00"),
        "original_price": Decimal("105000.00"),
        "page_count": 212,
        "weight_grams": 280,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tấm vé kỳ diệu đưa người lớn trở về với thế giới tuổi thơ vô tư lự, đầy ắp tiếng cười và những trò nghịch ngợm ngây ngô.",
        "sample_text": "Tôi viết cuốn sách này không dành cho trẻ em. Tôi viết cho những ai từng là trẻ em.",
        "cover_image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2019, 5, 20),
        "stock": 60,
    },
    {
        "isbn": "9786042183011",
        "sku": "NOV-LIT-003",
        "title": "Dế Mèn Phiêu Lưu Ký",
        "slug": "de-men-phieu-luu-ky",
        "publisher_slug": "nxb-kim-dong",
        "category_slugs": ["van-hoc-viet-nam", "thieu-nhi-tuoi-moi-lon"],
        "author_slugs": ["to-hoai"],
        "price": Decimal("68000.00"),
        "original_price": Decimal("75000.00"),
        "page_count": 188,
        "weight_grams": 250,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tác phẩm kinh điển về hành trình phiêu lưu, vượt qua nông nổi tuổi trẻ để học bài học về tình bạn, lòng bao dung và khát vọng hòa bình.",
        "sample_text": "Tôi sống độc lập từ thuở bé. Ấy là tục lệ lâu đời trong họ dế chúng tôi...",
        "cover_image_url": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 6, 1),
        "stock": 80,
    },
    {
        "isbn": "9786049890123",
        "sku": "NOV-LIT-004",
        "title": "Chí Phèo & Những Truyện Ngắn Chọn Lọc",
        "slug": "chi-pheo-truyen-ngan-chon-loc",
        "publisher_slug": "nxb-van-hoc",
        "category_slugs": ["van-hoc-viet-nam"],
        "author_slugs": ["nam-cao"],
        "price": Decimal("85000.00"),
        "original_price": Decimal("95000.00"),
        "page_count": 270,
        "weight_grams": 320,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tuyển tập những kiệt tác văn học hiện thực phê phán đỉnh cao về thân phận người nông dân và trí thức nghèo trước Cách mạng.",
        "sample_text": "Hắn vừa đi vừa chửi. Bao giờ cũng thế, cứ rượu xong là hắn chửi...",
        "cover_image_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2018, 9, 10),
        "stock": 35,
    },
    {
        "isbn": "9786049890130",
        "sku": "NOV-LIT-005",
        "title": "Số Đỏ",
        "slug": "so-do",
        "publisher_slug": "nxb-van-hoc",
        "category_slugs": ["van-hoc-viet-nam"],
        "author_slugs": ["vu-trong-phung"],
        "price": Decimal("92000.00"),
        "original_price": Decimal("100000.00"),
        "page_count": 260,
        "weight_grams": 310,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tiểu thuyết châm biếm sâu cay bậc nhất văn học Việt Nam về sự lố lăng của tầng lớp thị dân âu hóa nửa mùa.",
        "sample_text": "Hỡi ôi! Người đời thường hay ghen tị với những sự may mắn lạ lùng của người khác...",
        "cover_image_url": "https://images.unsplash.com/photo-1476275466078-4007374efbbe?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2019, 3, 14),
        "stock": 40,
    },
    {
        "isbn": "9786049673450",
        "sku": "NOV-LIT-006",
        "title": "Nỗi Buồn Chiến Tranh",
        "slug": "noi-buon-chien-tranh",
        "publisher_slug": "nxb-hoi-nha-van",
        "category_slugs": ["van-hoc-viet-nam"],
        "author_slugs": ["bao-ninh"],
        "price": Decimal("120000.00"),
        "original_price": Decimal("135000.00"),
        "page_count": 310,
        "weight_grams": 380,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tác phẩm đoạt nhiều giải thưởng quốc tế, khắc họa chiến tranh từ góc nhìn bi tráng, thấm đẫm tính nhân bản sâu sắc.",
        "sample_text": "Chiến tranh là một vùng hồi ức đen thẳm, nơi ký ức và hiện thực hòa lẫn trong tiếng mưa rừng dầm dề...",
        "cover_image_url": "https://images.unsplash.com/photo-1495640388908-05fa85288e61?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 4, 30),
        "stock": 25,
    },
    {
        "isbn": "9786049890147",
        "sku": "NOV-LIT-007",
        "title": "Truyện Kiều (Bản Khảo Đính)",
        "slug": "truyen-kieu-ban-khao-dinh",
        "publisher_slug": "nxb-van-hoc",
        "category_slugs": ["van-hoc-viet-nam"],
        "author_slugs": ["nguyen-du"],
        "price": Decimal("150000.00"),
        "original_price": Decimal("180000.00"),
        "page_count": 380,
        "weight_grams": 450,
        "cover_type": "HARDCOVER",
        "description": f"{DEMO_TAG} Kiệt tác thi ca bất hủ gồm 3254 câu thơ lục bát, di sản văn hóa đỉnh cao của dân tộc Việt Nam.",
        "sample_text": "Trăm năm trong cõi người ta / Chữ tài chữ mệnh khéo là ghét nhau...",
        "cover_image_url": "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 8, 15),
        "stock": 30,
    },
    {
        "isbn": "9786049673467",
        "sku": "NOV-INT-008",
        "title": "Rừng Na Uy (Norwegian Wood)",
        "slug": "rung-na-uy",
        "publisher_slug": "nxb-hoi-nha-van",
        "category_slugs": ["van-hoc-nuoc-ngoai"],
        "author_slugs": ["haruki-murakami"],
        "price": Decimal("135000.00"),
        "original_price": Decimal("150000.00"),
        "page_count": 420,
        "weight_grams": 480,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Câu chuyện về sự mất mát, tình yêu và nỗi cô đơn của tuổi trẻ Tokyo những năm 1960.",
        "sample_text": "Cái chết không phải là đối nghịch của sự sống mà là một phần của sự sống.",
        "cover_image_url": "https://images.unsplash.com/photo-1491841550275-ad7854e35ca6?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2019, 10, 10),
        "stock": 50,
    },
    {
        "isbn": "9786049673474",
        "sku": "NOV-INT-009",
        "title": "1Q84 (Tập 1 & 2)",
        "slug": "1q84-tap-1-2",
        "publisher_slug": "nxb-hoi-nha-van",
        "category_slugs": ["van-hoc-nuoc-ngoai"],
        "author_slugs": ["haruki-murakami"],
        "price": Decimal("260000.00"),
        "original_price": Decimal("290000.00"),
        "page_count": 840,
        "weight_grams": 950,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Thế giới song song kỳ ảo nơi có hai mặt trăng chiếu rọi số phận của Aomame và Tengo.",
        "sample_text": "Đừng để bị lừa dối bởi vẻ ngoài. Thực tại luôn chỉ có một, nhưng có thể có nhiều cách diễn giải.",
        "cover_image_url": "https://images.unsplash.com/photo-1532012164546-f432f2e3777f?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 11, 20),
        "stock": 20,
    },
    {
        "isbn": "9786049673481",
        "sku": "NOV-INT-010",
        "title": "1984 (Một Chín Tám Tư)",
        "slug": "1984-george-orwell",
        "publisher_slug": "nxb-hoi-nha-van",
        "category_slugs": ["van-hoc-nuoc-ngoai"],
        "author_slugs": ["george-orwell"],
        "price": Decimal("115000.00"),
        "original_price": Decimal("130000.00"),
        "page_count": 360,
        "weight_grams": 400,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tác phẩm kinh điển phản địa đàng cảnh báo về sự giám sát toàn trị và kiểm soát tư tưởng con người.",
        "sample_text": "Chiến tranh là Hòa bình. Tự do là Nô lệ. Ngu dốt là Sức mạnh.",
        "cover_image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 2, 1),
        "stock": 35,
    },
    {
        "isbn": "9786049673498",
        "sku": "NOV-INT-011",
        "title": "Chuyện Ở Nông Trại (Animal Farm)",
        "slug": "chuyen-o-nong-trai",
        "publisher_slug": "nxb-hoi-nha-van",
        "category_slugs": ["van-hoc-nuoc-ngoai"],
        "author_slugs": ["george-orwell"],
        "price": Decimal("75000.00"),
        "original_price": Decimal("85000.00"),
        "page_count": 160,
        "weight_grams": 220,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Truyện ngụ ngôn chính trị sắc sảo về sự tha hóa của quyền lực tuyệt đối trong một nông trại nổi dậy.",
        "sample_text": "Mọi con vật đều bình đẳng, nhưng một số con vật bình đẳng hơn những con vật khác.",
        "cover_image_url": "https://images.unsplash.com/photo-1509021436665-8f07dbf5bf1d?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2019, 7, 15),
        "stock": 45,
    },
    {
        "isbn": "9786041182369",
        "sku": "NOV-LIT-012",
        "title": "Hoàng Tử Bé (Le Petit Prince)",
        "slug": "hoang-tu-be",
        "publisher_slug": "nxb-tre",
        "category_slugs": ["van-hoc-nuoc-ngoai", "thieu-nhi-tuoi-moi-lon"],
        "author_slugs": ["antoine-de-saint-exupery"],
        "price": Decimal("85000.00"),
        "original_price": Decimal("95000.00"),
        "page_count": 140,
        "weight_grams": 200,
        "cover_type": "HARDCOVER",
        "description": f"{DEMO_TAG} Cuốn sách triết lý giản dị mà sâu sắc nhất về tình yêu, sự gắn kết và cách nhìn cuộc đời bằng trái tim.",
        "sample_text": "Người ta chỉ thấy rõ bằng trái tim. Những gì thiết yếu đều vô hình đối với mắt trần.",
        "cover_image_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 3, 25),
        "stock": 70,
    },
    {
        "isbn": "9786049673504",
        "sku": "NOV-LIT-013",
        "title": "Nhà Giả Kim (The Alchemist)",
        "slug": "nha-gia-kim",
        "publisher_slug": "nxb-hoi-nha-van",
        "category_slugs": ["van-hoc-nuoc-ngoai", "ky-nang-song-phat-trien"],
        "author_slugs": ["paulo-coelho"],
        "price": Decimal("89000.00"),
        "original_price": Decimal("99000.00"),
        "page_count": 228,
        "weight_grams": 260,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Hành trình theo đuổi vận mệnh của chàng chăn cừu Santiago qua sa mạc Bắc Phi tìm kho báu kim tự tháp.",
        "sample_text": "Khi bạn thực sự khao khát một điều gì, toàn bộ vũ trụ sẽ hợp lực giúp bạn đạt được điều đó.",
        "cover_image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 5, 10),
        "stock": 90,
    },
    {
        "isbn": "9786049890154",
        "sku": "NOV-LIT-014",
        "title": "Những Người Khốn Khổ (Hộp 2 Tập)",
        "slug": "nhung-nguoi-khon-kho-hop-2-tap",
        "publisher_slug": "nxb-van-hoc",
        "category_slugs": ["van-hoc-nuoc-ngoai"],
        "author_slugs": ["victor-hugo"],
        "price": Decimal("380000.00"),
        "original_price": Decimal("420000.00"),
        "page_count": 1400,
        "weight_grams": 1600,
        "cover_type": "HARDCOVER",
        "description": f"{DEMO_TAG} Bản hùng ca vĩ đại về tình thương, công lý và sự cứu chuộc tâm hồn của Jean Valjean giữa Paris thế kỷ 19.",
        "sample_text": "Yêu hay đã từng yêu, thế là đủ rồi. Không cần đòi hỏi gì hơn trong cuộc đời này nữa.",
        "cover_image_url": "https://images.unsplash.com/photo-1476275466078-4007374efbbe?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2019, 12, 1),
        "stock": 15,
    },
    {
        "isbn": "9786049673511",
        "sku": "NOV-LIT-015",
        "title": "Hóa Thân (The Metamorphosis)",
        "slug": "hoa-than-franz-kafka",
        "publisher_slug": "nxb-hoi-nha-van",
        "category_slugs": ["van-hoc-nuoc-ngoai"],
        "author_slugs": ["franz-kafka"],
        "price": Decimal("72000.00"),
        "original_price": Decimal("80000.00"),
        "page_count": 160,
        "weight_grams": 210,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Câu chuyện ám ảnh về chàng trai Gregor Samsa một sáng thức dậy thấy mình biến thành một con côn trùng khổng lồ.",
        "sample_text": "Một buổi sáng thức dậy sau những giấc mộng bất an, Gregor Samsa thấy mình đã biến thành một con bọ khổng lồ ngay trên giường.",
        "cover_image_url": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 8, 12),
        "stock": 30,
    },
    {
        "isbn": "9786049673528",
        "sku": "NOV-LIT-016",
        "title": "Người Xa Lạ (L'Étranger)",
        "slug": "nguoi-xa-la-albert-camus",
        "publisher_slug": "nxb-hoi-nha-van",
        "category_slugs": ["van-hoc-nuoc-ngoai", "lich-su-triet-hoc"],
        "author_slugs": ["albert-camus"],
        "price": Decimal("88000.00"),
        "original_price": Decimal("98000.00"),
        "page_count": 190,
        "weight_grams": 240,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tác phẩm kinh điển về triết lý phi lý của Albert Camus, kể về Meursault - một người cự tuyệt nói dối cảm xúc của mình.",
        "sample_text": "Hôm nay mẹ mất. Hoặc có thể là hôm qua, tôi cũng không rõ nữa.",
        "cover_image_url": "https://images.unsplash.com/photo-1495640388908-05fa85288e61?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 9, 5),
        "stock": 28,
    },
    {
        "isbn": "9786049890161",
        "sku": "NOV-LIT-017",
        "title": "Tội Ác Và Hình Phạt",
        "slug": "toi-ac-va-hinh-phat",
        "publisher_slug": "nxb-van-hoc",
        "category_slugs": ["van-hoc-nuoc-ngoai", "tam-ly-hoc"],
        "author_slugs": ["fyodor-dostoevsky"],
        "price": Decimal("195000.00"),
        "original_price": Decimal("220000.00"),
        "page_count": 680,
        "weight_grams": 720,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Cuộc đấu tranh nội tâm dữ dội của chàng sinh viên Raskolnikov sau khi phạm phải tội ác tày trời để chứng minh học thuyết vĩ nhân.",
        "sample_text": "Phải chăng tôi là một con sâu bọ run rẩy hay tôi có quyền vượt qua mọi chuẩn mực?",
        "cover_image_url": "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2019, 4, 18),
        "stock": 22,
    },
    {
        "isbn": "9786047728901",
        "sku": "NOV-SCI-018",
        "title": "Sapiens: Lược Sử Loài Người",
        "slug": "sapiens-luoc-su-loai-nguoi",
        "publisher_slug": "nxb-the-gioi",
        "category_slugs": ["lich-su-triet-hoc", "khoa-hoc-cong-nghe"],
        "author_slugs": ["yuval-noah-harari"],
        "price": Decimal("230000.00"),
        "original_price": Decimal("260000.00"),
        "page_count": 560,
        "weight_grams": 650,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tác phẩm chấn động lịch sử khám phá hành trình một loài vượn người không có gì nổi bật trở thành kẻ thống trị hành tinh.",
        "sample_text": "Chúng ta kiểm soát thế giới vì chúng ta là loài duy nhất có thể tin vào những câu chuyện không có thật trong tự nhiên.",
        "cover_image_url": "https://images.unsplash.com/photo-1532012164546-f432f2e3777f?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 1, 10),
        "stock": 55,
    },
    {
        "isbn": "9786047728918",
        "sku": "NOV-SCI-019",
        "title": "Homo Deus: Lược Sử Tương Lai",
        "slug": "homo-deus-luoc-su-tuong-lai",
        "publisher_slug": "nxb-the-gioi",
        "category_slugs": ["khoa-hoc-cong-nghe", "lich-su-triet-hoc"],
        "author_slugs": ["yuval-noah-harari"],
        "price": Decimal("245000.00"),
        "original_price": Decimal("275000.00"),
        "page_count": 520,
        "weight_grams": 620,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Bức tranh tương lai khi con người dùng công nghệ sinh học và trí tuệ nhân tạo để nâng cấp chính mình thành thần thánh.",
        "sample_text": "Trong thế kỷ 21, dự án lớn thứ ba của nhân loại sẽ là đạt được quyền năng của thần thánh: biến Homo sapiens thành Homo deus.",
        "cover_image_url": "https://images.unsplash.com/photo-1509021436665-8f07dbf5bf1d?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 5, 20),
        "stock": 35,
    },
    {
        "isbn": "9786047728925",
        "sku": "NOV-SCI-020",
        "title": "21 Bài Học Cho Thế Kỷ 21",
        "slug": "21-bai-hoc-cho-the-ky-21",
        "publisher_slug": "nxb-the-gioi",
        "category_slugs": ["khoa-hoc-cong-nghe", "lich-su-triet-hoc"],
        "author_slugs": ["yuval-noah-harari"],
        "price": Decimal("210000.00"),
        "original_price": Decimal("240000.00"),
        "page_count": 480,
        "weight_grams": 580,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Những câu hỏi cấp thiết nhất của hiện tại: AI, tin giả, chiến tranh hạt nhân, khủng hoảng khí hậu và ý nghĩa cuộc sống.",
        "sample_text": "Trong một thế giới ngập tràn thông tin vô giá trị, sự rõ ràng chính là quyền lực.",
        "cover_image_url": "https://images.unsplash.com/photo-1491841550275-ad7854e35ca6?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2022, 2, 14),
        "stock": 40,
    },
    {
        "isbn": "9786047728932",
        "sku": "NOV-SLF-021",
        "title": "Atomic Habits - Thói Quen Nguyên Tử",
        "slug": "atomic-habits-thoi-quen-nguyen-tu",
        "publisher_slug": "nxb-the-gioi",
        "category_slugs": ["ky-nang-song-phat-trien", "tam-ly-hoc"],
        "author_slugs": ["james-clear"],
        "price": Decimal("165000.00"),
        "original_price": Decimal("189000.00"),
        "page_count": 320,
        "weight_grams": 410,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Phương pháp khoa học để thay đổi 1% mỗi ngày, tạo nên sự chuyển biến phi thường trong công việc và cuộc sống.",
        "sample_text": "Bạn không vươn tới tầm cao của mục tiêu, bạn rơi xuống ngang mức của các hệ thống mà bạn xây dựng.",
        "cover_image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 7, 7),
        "stock": 120,
    },
    {
        "isbn": "9786045890123",
        "sku": "NOV-SLF-022",
        "title": "Đắc Nhân Tâm (How to Win Friends and Influence People)",
        "slug": "dac-nhan-tam",
        "publisher_slug": "nxb-tong-hop-tphcm",
        "category_slugs": ["ky-nang-song-phat-trien"],
        "author_slugs": ["dale-carnegie"],
        "price": Decimal("86000.00"),
        "original_price": Decimal("98000.00"),
        "page_count": 320,
        "weight_grams": 390,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Cuốn sách kinh điển nhất mọi thời đại về nghệ thuật giao tiếp, thấu hiểu và gắn kết lòng người.",
        "sample_text": "Hãy khen ngợi người khác một cách chân thành và không tiếc lời tán thưởng.",
        "cover_image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 10, 1),
        "stock": 150,
    },
    {
        "isbn": "9786047728949",
        "sku": "NOV-PSY-023",
        "title": "Tư Duy Nhanh Và Chậm (Thinking, Fast and Slow)",
        "slug": "tu-duy-nhanh-va-cham",
        "publisher_slug": "nxb-the-gioi",
        "category_slugs": ["tam-ly-hoc", "kinh-te-quan-tri"],
        "author_slugs": ["daniel-kahneman"],
        "price": Decimal("240000.00"),
        "original_price": Decimal("275000.00"),
        "page_count": 620,
        "weight_grams": 740,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Công trình đoạt giải Nobel khám phá hai hệ thống chi phối mọi quyết định và ảo tưởng nhận thức của con người.",
        "sample_text": "Hệ thống 1 hoạt động tự động và nhanh chóng, ít hoặc không cần nỗ lực, trong khi Hệ thống 2 đòi hỏi sự tập trung cao độ.",
        "cover_image_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 9, 15),
        "stock": 45,
    },
    {
        "isbn": "9786045890130",
        "sku": "NOV-ECO-024",
        "title": "Tâm Lý Học Về Tiền (The Psychology of Money)",
        "slug": "tam-ly-hoc-ve-tien",
        "publisher_slug": "nxb-tong-hop-tphcm",
        "category_slugs": ["kinh-te-quan-tri", "tam-ly-hoc"],
        "author_slugs": ["morgan-housel"],
        "price": Decimal("155000.00"),
        "original_price": Decimal("180000.00"),
        "page_count": 380,
        "weight_grams": 420,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} 19 câu chuyện sâu sắc lý giải tại sao hành vi và cảm xúc quyết định thành công tài chính hơn là toán học.",
        "sample_text": "Làm tốt với tiền bạc ít liên quan đến việc bạn thông minh thế nào, mà liên quan nhiều đến cách bạn hành xử.",
        "cover_image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 12, 1),
        "stock": 85,
    },
    {
        "isbn": "9786041182376",
        "sku": "NOV-ECO-025",
        "title": "Từ Không Đến Một (Zero to One)",
        "slug": "tu-khong-den-mot",
        "publisher_slug": "nxb-tre",
        "category_slugs": ["kinh-te-quan-tri", "khoa-hoc-cong-nghe"],
        "author_slugs": ["peter-thiel"],
        "price": Decimal("125000.00"),
        "original_price": Decimal("145000.00"),
        "page_count": 250,
        "weight_grams": 330,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Bài học khởi nghiệp từ huyền thoại Peter Thiel về cách tạo ra những điều đột phá thay vì cạnh tranh sao chép.",
        "sample_text": "Mỗi khoảnh khắc trong kinh doanh chỉ xảy ra một lần. Người tạo ra hệ điều hành tiếp theo sẽ không phải là Bill Gates.",
        "cover_image_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 6, 18),
        "stock": 50,
    },
    {
        "isbn": "9786047728956",
        "sku": "NOV-ECO-026",
        "title": "Các Nguyên Tắc: Cuộc Sống Và Công Việc (Principles)",
        "slug": "cac-nguyen-tac-principles",
        "publisher_slug": "nxb-the-gioi",
        "category_slugs": ["kinh-te-quan-tri", "ky-nang-song-phat-trien"],
        "author_slugs": ["ray-dalio"],
        "price": Decimal("320000.00"),
        "original_price": Decimal("360000.00"),
        "page_count": 680,
        "weight_grams": 850,
        "cover_type": "HARDCOVER",
        "description": f"{DEMO_TAG} Bộ nguyên tắc thực tế của nhà đầu tư huyền thoại Ray Dalio giúp xây dựng văn hóa minh bạch triệt để.",
        "sample_text": "Đau đớn + Suy ngẫm = Tiến bộ. Đó là công thức cốt lõi của mọi sự phát triển.",
        "cover_image_url": "https://images.unsplash.com/photo-1509021436665-8f07dbf5bf1d?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 4, 10),
        "stock": 30,
    },
    {
        "isbn": "9786047728963",
        "sku": "NOV-BIO-027",
        "title": "Steve Jobs (Tiểu Sử Chính Thức)",
        "slug": "steve-jobs-tieu-su",
        "publisher_slug": "nxb-the-gioi",
        "category_slugs": ["kinh-te-quan-tri", "khoa-hoc-cong-nghe"],
        "author_slugs": ["walter-isaacson"],
        "price": Decimal("280000.00"),
        "original_price": Decimal("310000.00"),
        "page_count": 750,
        "weight_grams": 920,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tiểu sử toàn diện nhất về huyền thoại công nghệ Steve Jobs, người đã thay đổi cách nhân loại giao tiếp và giải trí.",
        "sample_text": "Những kẻ đủ điên rồ để nghĩ rằng họ có thể thay đổi thế giới chính là những người làm được điều đó.",
        "cover_image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2018, 11, 5),
        "stock": 40,
    },
    {
        "isbn": "9786047728970",
        "sku": "NOV-SLF-028",
        "title": "Nghệ Thuật Tinh Tế Của Việc Đếch Quan Tâm",
        "slug": "nghe-thuat-tinh-te-cua-viec-dech-quan-tam",
        "publisher_slug": "nxb-the-gioi",
        "category_slugs": ["ky-nang-song-phat-trien", "tam-ly-hoc"],
        "author_slugs": ["mark-manson"],
        "price": Decimal("110000.00"),
        "original_price": Decimal("128000.00"),
        "page_count": 280,
        "weight_grams": 340,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Lời khuyên thẳng thắn, không màu mè về cách lựa chọn những điều thực sự quan trọng trong một cuộc đời hữu hạn.",
        "sample_text": "Chìa khóa cho một cuộc sống tốt đẹp không phải là quan tâm nhiều hơn, mà là chỉ quan tâm đến những gì thực sự có ý nghĩa.",
        "cover_image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 3, 10),
        "stock": 65,
    },
    {
        "isbn": "9786041182383",
        "sku": "NOV-MAG-029",
        "title": "Harry Potter Và Hòn Đá Phù Thủy (Tập 1)",
        "slug": "harry-potter-va-hon-da-phu-thuy",
        "publisher_slug": "nxb-tre",
        "category_slugs": ["thieu-nhi-tuoi-moi-lon", "van-hoc-nuoc-ngoai"],
        "author_slugs": ["jk-rowling"],
        "price": Decimal("145000.00"),
        "original_price": Decimal("165000.00"),
        "page_count": 360,
        "weight_grams": 430,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Cánh cổng mở ra thế giới phù thủy Hogwarts kỳ diệu cùng cậu bé Harry Potter và những người bạn thân thiết.",
        "sample_text": "Phải có lòng dũng cảm lớn mới dám chống lại kẻ thù, nhưng cũng cần lòng dũng cảm tương tự để chống lại bạn bè mình.",
        "cover_image_url": "https://images.unsplash.com/photo-1532012164546-f432f2e3777f?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 10, 31),
        "stock": 100,
    },
    {
        "isbn": "9786041182390",
        "sku": "NOV-MAG-030",
        "title": "Harry Potter Và Phòng Chứa Bí Mật (Tập 2)",
        "slug": "harry-potter-va-phong-chua-bi-mat",
        "publisher_slug": "nxb-tre",
        "category_slugs": ["thieu-nhi-tuoi-moi-lon", "van-hoc-nuoc-ngoai"],
        "author_slugs": ["jk-rowling"],
        "price": Decimal("155000.00"),
        "original_price": Decimal("175000.00"),
        "page_count": 400,
        "weight_grams": 460,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Năm học thứ hai đầy thử thách khi căn phòng huyền bí mở ra đe dọa sinh mệnh học sinh trường Hogwarts.",
        "sample_text": "Chính những lựa chọn của chúng ta, chứ không phải năng lực, mới thể hiện chân thực chúng ta là ai.",
        "cover_image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 12, 15),
        "stock": 90,
    },
    {
        "isbn": "9786045890147",
        "sku": "NOV-LIT-031",
        "title": "Vang Bóng Một Thời",
        "slug": "vang-bong-mot-thoi",
        "publisher_slug": "nxb-tong-hop-tphcm",
        "category_slugs": ["van-hoc-viet-nam", "nghe-thuat-thiet-ke"],
        "author_slugs": ["nguyen-tuan"],
        "price": Decimal("85000.00"),
        "original_price": Decimal("95000.00"),
        "page_count": 210,
        "weight_grams": 270,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Tuyển tập tùy bút bậc thầy về những thú chơi tao nhã và vẻ đẹp văn hóa truyền thống thanh tao của người xưa.",
        "sample_text": "Chữ người tử tù - một cảnh tượng xưa nay chưa từng có trong chốn lao tù tăm tối.",
        "cover_image_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2019, 8, 20),
        "stock": 30,
    },
    {
        "isbn": "9786047728987",
        "sku": "NOV-ART-032",
        "title": "Câu Chuyện Nghệ Thuật (The Story of Art)",
        "slug": "cau-chuyen-nghe-thuat",
        "publisher_slug": "nxb-the-gioi",
        "category_slugs": ["nghe-thuat-thiet-ke", "lich-su-triet-hoc"],
        "author_slugs": ["walter-isaacson"],  # placeholder demo author
        "price": Decimal("480000.00"),
        "original_price": Decimal("550000.00"),
        "page_count": 680,
        "weight_grams": 1200,
        "cover_type": "HARDCOVER",
        "description": f"{DEMO_TAG} Tác phẩm kinh điển nhập môn lịch sử nghệ thuật nhân loại từ hang động thời tiền sử đến mỹ thuật hiện đại.",
        "sample_text": "Thực sự không có thứ gọi là Nghệ thuật. Chỉ có những người nghệ sĩ sáng tạo.",
        "cover_image_url": "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 6, 30),
        "stock": 18,
    },
    {
        "isbn": "9786045612345",
        "sku": "NOV-ENG-033",
        "title": "The Great Gatsby (Original English Edition)",
        "slug": "the-great-gatsby-english",
        "publisher_slug": "nxb-phu-nu-viet-nam",
        "category_slugs": ["sach-ngoai-van", "van-hoc-nuoc-ngoai"],
        "author_slugs": ["george-orwell"],  # placeholder demo author
        "price": Decimal("140000.00"),
        "original_price": Decimal("160000.00"),
        "page_count": 240,
        "weight_grams": 290,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Bản tiếng Anh nguyên tác kiệt tác văn học Mỹ về giấc mơ vàng son và sự sụp đổ của ảo tưởng thế kỷ 20.",
        "sample_text": "So we beat on, boats against the current, borne back ceaselessly into the past.",
        "cover_image_url": "https://images.unsplash.com/photo-1476275466078-4007374efbbe?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 11, 10),
        "stock": 35,
    },
    {
        "isbn": "9786045612352",
        "sku": "NOV-ENG-034",
        "title": "To Kill a Mockingbird (Original English Edition)",
        "slug": "to-kill-a-mockingbird-english",
        "publisher_slug": "nxb-phu-nu-viet-nam",
        "category_slugs": ["sach-ngoai-van", "van-hoc-nuoc-ngoai"],
        "author_slugs": ["george-orwell"],  # placeholder demo author
        "price": Decimal("160000.00"),
        "original_price": Decimal("185000.00"),
        "page_count": 380,
        "weight_grams": 410,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} Bản tiếng Anh tiểu thuyết kinh điển về lòng dũng cảm, công lý và sự thấu hiểu qua con mắt cô bé Scout.",
        "sample_text": "You never really understand a person until you consider things from his point of view.",
        "cover_image_url": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2021, 8, 22),
        "stock": 40,
    },
    {
        "isbn": "9786041182406",
        "sku": "NOV-LIT-035",
        "title": "Tôi Thấy Hoa Vàng Trên Cỏ Xanh",
        "slug": "toi-thay-hoa-vang-tren-co-xanh",
        "publisher_slug": "nxb-tre",
        "category_slugs": ["van-hoc-viet-nam", "thieu-nhi-tuoi-moi-lon"],
        "author_slugs": ["nguyen-nhat-anh"],
        "price": Decimal("115000.00"),
        "original_price": Decimal("130000.00"),
        "page_count": 378,
        "weight_grams": 440,
        "cover_type": "PAPERBACK",
        "description": f"{DEMO_TAG} 81 mẩu chuyện nhỏ lung linh về tình anh em, tình làng nghĩa xóm và tuổi thơ êm đềm ở một làng quê nghèo miền Trung.",
        "sample_text": "Ngồi im trong gió nghe đêm rớt / Chợt thấy hoa vàng trên cỏ xanh...",
        "cover_image_url": "https://images.unsplash.com/photo-1495640388908-05fa85288e61?auto=format&fit=crop&w=600&q=80",
        "published_date": date(2020, 4, 15),
        "stock": 95,
    },
]


def seed_all(db: Session) -> Dict[str, int]:
    """Run full idempotent demo seed process.
    
    Returns:
        Dictionary of seeded entities count.
    """
    stats = {
        "roles": 0,
        "users": 0,
        "publishers": 0,
        "categories": 0,
        "authors": 0,
        "books": 0,
        "inventory": 0,
    }

    # 1. Seed Roles
    for role_info in ROLES_DATA:
        existing_role = db.query(Role).filter(Role.name == role_info["name"]).first()
        if not existing_role:
            role = Role(**role_info)
            db.add(role)
            stats["roles"] += 1
    db.flush()

    # 2. Seed Publishers
    publisher_map = {}
    for pub_info in PUBLISHERS_DATA:
        existing_pub = db.query(Publisher).filter(Publisher.slug == pub_info["slug"]).first()
        if not existing_pub:
            pub = Publisher(**pub_info)
            db.add(pub)
            db.flush()
            publisher_map[pub.slug] = pub.id
            stats["publishers"] += 1
        else:
            publisher_map[existing_pub.slug] = existing_pub.id

    # 3. Seed Categories
    category_map = {}
    for cat_info in CATEGORIES_DATA:
        existing_cat = db.query(Category).filter(Category.slug == cat_info["slug"]).first()
        if not existing_cat:
            cat = Category(**cat_info)
            db.add(cat)
            db.flush()
            category_map[cat.slug] = cat.id
            stats["categories"] += 1
        else:
            category_map[existing_cat.slug] = existing_cat.id

    # 4. Seed Authors
    author_map = {}
    for auth_info in AUTHORS_DATA:
        existing_auth = db.query(Author).filter(Author.slug == auth_info["slug"]).first()
        if not existing_auth:
            auth = Author(**auth_info)
            db.add(auth)
            db.flush()
            author_map[auth.slug] = auth.id
            stats["authors"] += 1
        else:
            author_map[existing_auth.slug] = existing_auth.id

    # 5. Seed Books & Inventory
    for book_info in BOOKS_DATA:
        existing_book = db.query(Book).filter((Book.isbn == book_info["isbn"]) | (Book.slug == book_info["slug"])).first()
        if not existing_book:
            pub_id = publisher_map.get(book_info["publisher_slug"])
            book = Book(
                isbn=book_info["isbn"],
                sku=book_info["sku"],
                title=book_info["title"],
                slug=book_info["slug"],
                publisher_id=pub_id,
                price=book_info["price"],
                original_price=book_info["original_price"],
                page_count=book_info["page_count"],
                weight_grams=book_info["weight_grams"],
                cover_type=book_info["cover_type"],
                description=book_info["description"],
                sample_text=book_info.get("sample_text"),
                cover_image_url=book_info["cover_image_url"],
                status="ACTIVE",
                published_date=book_info["published_date"],
            )
            db.add(book)
            db.flush()
            stats["books"] += 1

            # Connect Author
            for order_idx, auth_slug in enumerate(book_info["author_slugs"]):
                a_id = author_map.get(auth_slug)
                if a_id:
                    ba = BookAuthor(
                        book_id=book.id,
                        author_id=a_id,
                        is_primary=(order_idx == 0),
                        order_index=order_idx,
                    )
                    db.add(ba)

            # Connect Categories
            for cat_slug in book_info["category_slugs"]:
                c_id = category_map.get(cat_slug)
                if c_id:
                    bc = BookCategory(book_id=book.id, category_id=c_id)
                    db.add(bc)

            # Add Cover Image
            bi = BookImage(
                book_id=book.id,
                image_url=book_info["cover_image_url"],
                alt_text=f"Bìa sách {book.title}",
                display_order=0,
                is_cover=True,
            )
            db.add(bi)

            # Create Inventory
            inv = Inventory(
                book_id=book.id,
                physical_stock=book_info["stock"],
                reserved_stock=0,
                low_stock_threshold=10,
            )
            db.add(inv)
            db.flush()
            stats["inventory"] += 1

            # Create initial inventory transaction
            trans = InventoryTransaction(
                inventory_id=inv.id,
                transaction_type="IMPORT",
                quantity_change=book_info["stock"],
                stock_after=book_info["stock"],
                reference_code=f"INIT-SEED-{book.sku}",
                notes=f"{DEMO_TAG} Khởi tạo tồn kho ban đầu cho sách demo",
            )
            db.add(trans)
        else:
            # Book exists, ensure inventory exists
            existing_inv = db.query(Inventory).filter(Inventory.book_id == existing_book.id).first()
            if not existing_inv:
                inv = Inventory(
                    book_id=existing_book.id,
                    physical_stock=book_info["stock"],
                    reserved_stock=0,
                    low_stock_threshold=10,
                )
                db.add(inv)
                db.flush()
                stats["inventory"] += 1

    # 6. Seed Demo Users
    for user_info in DEMO_USERS_DATA:
        user = db.query(User).filter(User.email == user_info["email"]).first()
        hashed = get_password_hash(user_info["password"])
        if not user:
            user = User(
                email=user_info["email"],
                hashed_password=hashed,
                full_name=user_info["full_name"],
                phone=user_info.get("phone"),
                is_active=True,
            )
            db.add(user)
            db.flush()
            stats["users"] += 1
        else:
            user.hashed_password = hashed
            user.full_name = user_info["full_name"]
            user.is_active = True
            db.flush()

        # Assign RBAC roles
        for role_name in user_info["roles"]:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=f"Role {role_name}")
                db.add(role)
                db.flush()

            existing_ur = (
                db.query(UserRole)
                .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
                .first()
            )
            if not existing_ur:
                ur = UserRole(user_id=user.id, role_id=role.id)
                db.add(ur)
                db.flush()

    db.commit()
    logger.info("Demo seed completed successfully: %s", stats)
    return stats


if __name__ == "__main__":
    import sys
    from app.database.connection import SessionLocal

    print("Running NOVELIA BOOKS demo data seeder...")
    db = SessionLocal()
    try:
        results = seed_all(db)
        print(f"Seed finished successfully! Statistics: {results}")
    except Exception as exc:
        db.rollback()
        print(f"Seed failed with error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()
