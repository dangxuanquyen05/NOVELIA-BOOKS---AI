"""Rule-based Fallback Engine for Novelia Books AI Assistant.

Provides instant (<50ms), zero-downtime responses when external LLM APIs
experience timeouts, outages, or missing API keys.
Supports Vietnamese accented and unaccented matching (via n-grams and token scoring)
and live database querying for book pricing, inventory, shipping rules, and order status.
"""

import re
import unicodedata
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.catalog import Book
from app.models.commerce import Order
from app.models.inventory import Inventory
from app.models.user import User

FALLBACK_RULES = [
    (
        r"\b(phí ship|phi ship|phí giao hàng|phi giao hang|chính sách giao hàng|chinh sach giao hang|phí vận chuyển|phi van chuyen|tiền ship|tien ship|bao lâu thì nhận|bao lau thi nhan|giao hàng mất mấy ngày)\b",
        "shipping",
    ),
    (
        r"\b(đơn hàng|don hang|order|giao chưa|giao chua|vận chuyển|van chuyen|tra cứu đơn|tra cuu don|lịch sử mua|lich su mua)\b",
        "order",
    ),
    (
        r"\b(giá|gia|bao nhiêu|bao nhieu|tiền|tien|price|cost|còn hàng không|con hang khong|tồn kho|ton kho|còn sách không|con sach khong)\b",
        "price_stock",
    ),
    (
        r"\b(tư vấn|tu van|gợi ý|goi y|nên đọc|nen doc|sách hay|sach hay|bán chạy|ban chay|mới nhất|moi nhat|sách hot|sach hot|đọc gì|doc gi|thể loại|the loai)\b",
        "recommendation",
    ),
    (
        r"^(xin chào|xin chao|chào|chao|hello|hi|hey|alo|bạn là ai|ban la ai)\b",
        "greeting",
    ),
]


def remove_accents(input_str: Optional[str]) -> str:
    """Normalize Vietnamese accented text into lowercase ASCII equivalent."""
    if not input_str:
        return ""
    s1 = unicodedata.normalize("NFD", str(input_str))
    s2 = "".join(c for c in s1 if unicodedata.category(c) != "Mn")
    return s2.replace("đ", "d").replace("Đ", "D").lower()


def format_currency(amount: Decimal | float | int) -> str:
    """Format monetary numbers according to Vietnamese convention (e.g. 120.000 đ)."""
    return f"{int(amount):,} đ".replace(",", ".")


def find_matching_books(db: Session, query: str, limit: int = 5) -> List[Book]:
    """Search for relevant books in the database matching title or author.

    Works robustly with accented and non-accented Vietnamese words.
    """
    clean_query = remove_accents(query)
    noise_words = {
        "gia", "bao", "nhieu", "tien", "la", "hien", "tai", "the", "nao", "co",
        "ngon", "khong", "mua", "o", "dau", "sach", "cuon", "quyen", "xin", "chao",
        "cho", "hoi", "toi", "minh", "ban", "con", "hang", "muon", "tim", "ve"
    }
    words_in_query = [w for w in clean_query.split() if w not in noise_words and len(w) > 1]
    filtered_clean_query = " ".join(words_in_query)

    try:
        books = (
            db.query(Book)
            .filter(Book.status == "ACTIVE")
            .limit(100)
            .all()
        )
    except Exception:
        return []

    scored: List[Tuple[int, Book]] = []
    for b in books:
        b_title_clean = remove_accents(b.title)
        b_author_clean = remove_accents(b.author or "")

        # 1. Exact full title match
        if b_title_clean in clean_query or clean_query in b_title_clean:
            scored.append((len(b_title_clean) * 4, b))
            continue

        # 2. Author match
        if b_author_clean and (b_author_clean in clean_query or clean_query in b_author_clean):
            scored.append((len(b_author_clean) * 3, b))
            continue

        # 3. N-gram matching (2-4 word phrases)
        title_words = b_title_clean.split()
        matched_ngram_len = 0
        for i in range(len(title_words)):
            for j in range(i + 2, len(title_words) + 1):
                ngram = " ".join(title_words[i:j])
                if ngram in clean_query or (filtered_clean_query and ngram in filtered_clean_query):
                    matched_ngram_len = max(matched_ngram_len, len(ngram))
        if matched_ngram_len > 0:
            scored.append((matched_ngram_len * 2, b))
            continue

        # 4. Individual keyword hits
        hits = 0
        for w in words_in_query:
            if w in b_title_clean or w in b_author_clean:
                hits += 1
        if hits >= 2 or (len(words_in_query) == 1 and hits == 1):
            scored.append((hits, b))

    scored.sort(key=lambda x: x[0], reverse=True)
    results: List[Book] = []
    seen = set()
    for _, b in scored:
        if b.id not in seen:
            seen.add(b.id)
            results.append(b)
        if len(results) >= limit:
            break
    return results


def get_book_available_stock(db: Session, book_id: int) -> int:
    """Retrieve available inventory stock for a given book."""
    try:
        inv = db.query(Inventory).filter(Inventory.book_id == book_id).first()
        if inv:
            return max(0, inv.physical_stock - inv.reserved_stock)
    except Exception:
        pass
    return 0


def get_fallback_response(
    db: Session,
    message: str,
    current_user: Optional[User] = None,
) -> Tuple[str, str]:
    """Execute rule-based matching with real-time DB data.

    Returns: (reply_text, intent_type)
    """
    msg = message.strip()
    msg_lower = msg.lower()

    matched_intent = None
    for pattern, intent in FALLBACK_RULES:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            matched_intent = intent
            break

    # 1. SHIPPING POLICY
    if matched_intent == "shipping":
        return (
            "🚚 **Chính sách Giao hàng & Vận chuyển của NOVELIA BOOKS**:\n\n"
            "• **Miễn phí vận chuyển (Freeship)**: Cho tất cả đơn hàng từ **500.000 đ** trở lên trên toàn quốc.\n"
            "• **Phí giao hàng tiêu chuẩn**: **30.000 đ** cho đơn hàng dưới 500.000 đ.\n"
            "• **Thời gian giao hàng dự kiến**: Từ 1 – 3 ngày làm việc (nội thành Hà Nội & TP.HCM nhận trong 24 – 48 giờ).\n"
            "• Tất cả sách đều được đóng gói hộp carton cứng cáp kèm màng bọc xốp chống sốc để đảm bảo sách đến tay Quý khách mới nguyên 100%!",
            "shipping",
        )

    # 2. ORDER TRACKING
    if matched_intent == "order":
        if not current_user:
            return (
                "📦 Quý khách vui lòng **Đăng nhập** tài khoản để tra cứu nhanh thông tin và tình trạng vận chuyển các đơn hàng của mình nhé!",
                "order",
            )
        try:
            recent_orders = (
                db.query(Order)
                .filter(Order.user_id == current_user.id)
                .order_by(Order.created_at.desc())
                .limit(3)
                .all()
            )
            if not recent_orders:
                return (
                    f"📦 Quý khách **{current_user.full_name}** hiện chưa có đơn hàng nào trên hệ thống NOVELIA BOOKS. "
                    f"Hãy chọn ngay những tựa sách yêu thích để lên đơn Quý khách nhé!",
                    "order",
                )
            lines = [f"📦 **Danh sách đơn hàng gần đây của Quý khách {current_user.full_name}:**\n"]
            for ord in recent_orders:
                status_vn = {
                    "PENDING": "Chờ thanh toán",
                    "CONFIRMED": "Đã xác nhận & Chuẩn bị sách",
                    "SHIPPED": "Đang giao hàng",
                    "DELIVERED": "Đã giao thành công",
                    "CANCELLED": "Đã hủy",
                }.get(ord.status, ord.status)
                lines.append(
                    f"• Mã đơn: **{ord.order_code}** | Tổng tiền: **{format_currency(ord.total_amount)}** | Trạng thái: **{status_vn}**"
                )
            lines.append("\n👉 Quý khách có thể vào mục **Đơn hàng của tôi** để xem chi tiết mã vận đơn và lộ trình nhé!")
            return ("\n".join(lines), "order")
        except Exception:
            return ("📦 Quý khách có thể xem chi tiết trạng thái đơn hàng tại mục **Đơn hàng của tôi**.", "order")

    # 3. BOOK PRICING & STOCK CHECK
    matching_books = find_matching_books(db, msg, limit=4)
    if matching_books:
        if len(matching_books) == 1:
            b = matching_books[0]
            stock = get_book_available_stock(db, b.id)
            stock_txt = f"còn **{stock} cuốn** sẵn sàng giao" if stock > 0 else "hiện đang tạm hết hàng"
            author_txt = f" của tác giả **{b.author}**" if b.author else ""
            category_txt = f" (thể loại *{b.category.name}*)" if b.category else ""
            return (
                f"📚 Tác phẩm **{b.title}**{author_txt}{category_txt} hiện có giá **{format_currency(b.price)}** ({stock_txt}).\n\n"
                f"Quý khách có thể đặt mua trực tiếp ngay trong cửa sổ chat này bằng cách nhắn: **'Mua 1 cuốn {b.title}'** hoặc thêm vào giỏ hàng nhé!",
                "price_stock",
            )
        else:
            lines = ["📚 **NOVELIA BOOKS tìm thấy các tác phẩm phù hợp với tìm kiếm của Quý khách:**\n"]
            for b in matching_books:
                stock = get_book_available_stock(db, b.id)
                stock_txt = f"Kho: {stock} cuốn" if stock > 0 else "Tạm hết"
                author_txt = f" - {b.author}" if b.author else ""
                lines.append(f"• **{b.title}**{author_txt}: **{format_currency(b.price)}** ({stock_txt})")
            lines.append("\n👉 Quý khách muốn tham khảo cuốn nào chi tiết hoặc muốn đặt mua trực tiếp không ạ?")
            return ("\n".join(lines), "price_stock")

    # 4. RECOMMENDATIONS
    if matched_intent == "recommendation":
        try:
            top_books = (
                db.query(Book)
                .filter(Book.status == "ACTIVE")
                .order_by(Book.rating_average.desc(), Book.total_reviews.desc())
                .limit(4)
                .all()
            )
            if top_books:
                lines = ["✨ **Gợi ý những tựa sách nổi bật và bán chạy nhất tại NOVELIA BOOKS:**\n"]
                for b in top_books:
                    stock = get_book_available_stock(db, b.id)
                    author_txt = f" ({b.author})" if b.author else ""
                    lines.append(f"• **{b.title}**{author_txt} — **{format_currency(b.price)}** (Đánh giá: ⭐ {float(b.rating_average):.1f}/5)")
                lines.append("\n👉 Quý khách có thể nhắn: **'Mua [số lượng] [tên sách]'** để em hỗ trợ lên đơn nhanh ngay tại đây nhé!")
                return ("\n".join(lines), "recommendation")
        except Exception:
            pass

    # 5. GREETING
    if matched_intent == "greeting":
        user_name = f" **{current_user.full_name}**" if current_user and current_user.full_name else ""
        return (
            f"Dạ chào Quý khách{user_name}! Em là **Novelia AI Assistant** — Trợ lý tư vấn sách và hỗ trợ mua sắm thông minh của NOVELIA BOOKS. 📖\n\n"
            f"Em có thể hỗ trợ Quý khách:\n"
            f"• 🔍 **Tra cứu sách**: Tìm sách theo tên, tác giả, thể loại và xem giá, tồn kho thực tế.\n"
            f"• ⚡ **Lên đơn hàng trực tiếp**: Nhắn câu lệnh tự nhiên (vd: *'Mua 2 cuốn Nhà Giả Kim'*) để chốt đơn và nhận mã VietQR ngay trong khung chat!\n"
            f"• 🚚 **Chính sách & Vận chuyển**: Tra cứu phí ship, chính sách freeship từ 500k.\n"
            f"• 📦 **Tra cứu đơn hàng**: Kiểm tra trạng thái đơn hàng của Quý khách.\n\n"
            f"Quý khách đang quan tâm đến cuốn sách nào hôm nay ạ?",
            "greeting",
        )

    # 6. DEFAULT POLITE FALLBACK
    return (
        "Dạ, Novelia AI luôn sẵn sàng hỗ trợ Quý khách! Quý khách có thể hỏi em về giá sách, tồn kho, gợi ý tựa sách hay, chính sách giao hàng hoặc nhắn **'Mua [tên sách]'** để em hỗ trợ lên đơn hàng trực tiếp nhé! 📚",
        "default",
    )
