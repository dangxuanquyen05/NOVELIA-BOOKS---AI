"""Conversational Ordering Assistant Service for Novelia Books.

Implements direct, multi-turn conversational ordering inside the chat interface:
1. Detects order intent from natural Vietnamese language.
2. Extracts book title, quantity, recipient name, phone, address, and payment method.
3. Manages multi-turn dialogue state (awaiting info -> awaiting payment method -> checkout).
4. Provides interactive Choice Cards for payment selection (COD vs VietQR Napas 247).
5. Executes authoritative, atomic order creation with pessimistic inventory locking (SELECT ... FOR UPDATE).
6. Generates dynamic VietQR codes directly in chat for cashless Mobile Banking payments.
"""

import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.integrations.ai.fallback import (
    find_matching_books,
    format_currency,
    get_book_available_stock,
    remove_accents,
)
from app.integrations.payment.vietqr import get_vietqr_info, get_vietqr_url
from app.models.catalog import Book
from app.models.commerce import Order, OrderItem
from app.models.inventory import Inventory
from app.models.payment_shipping import Payment, Shipment
from app.models.user import User

ORDER_TRIGGERS = [
    r"\b(mua|đặt|dat|lên đơn|len don|tạo đơn|tao don|order|mua sách|mua sach|đặt sách|dat sach|ship cho|gửi cho|gui cho|lấy cho|lay cho|giao cho|chốt đơn|chot don|chốt sách|chot sach)\b"
]

CANCEL_TRIGGERS = [
    r"\b(hủy|huy|thôi|thoi|không mua|khong mua|dừng|dung|bỏ qua|bo qua|hủy đơn|huy don)\b"
]

CONFIRM_TRIGGERS = [
    r"\b(đồng ý|dong y|ok|okie|xác nhận|xac nhan|đúng rồi|dung roi|chuẩn|chuan|yes|giao đi|giao di|tạo luôn|tao luon|được|duoc|chốt|chot)\b"
]

PHONE_PATTERN = r"(?:\b(?:\+84|0)[35789](?:[\s.-]?\d){8}\b)"

PAYMENT_COD_PATTERN = r"\b(cod|tiền mặt|tien mat|trả sau|tra sau|khi nhận|khi nhan|nhận hàng mới trả|nhan hang moi tra|nhận sách mới trả|nhan sach thanh toan)\b"
PAYMENT_VIETQR_PATTERN = r"\b(vietqr|qr|chuyển khoản|chuyen khoan|ck|ngân hàng|ngan hang|chuyển tiền|chuyen tien|banking|napas|quét mã|quet ma|bằng qr|bang qr)\b"

# Ephemeral in-memory conversational draft cache keyed by session_uuid
_ORDER_DRAFTS: Dict[str, Dict[str, Any]] = {}


def sanitize_name(name: Optional[str], default_name: str = "Quý khách") -> str:
    """Sanitize recipient name to fit standard length and prevent special characters."""
    if not name or not isinstance(name, str):
        return default_name
    cleaned = name.strip()
    if len(cleaned) < 2 or len(cleaned) > 50:
        return default_name
    if any(ch in cleaned for ch in [":", "/", "\\", "$", "%", "^", "*", "{", "}", "[", "]", "|", "<", ">"]):
        return default_name
    blacklist = {"đ", "vnd", "vnđ", "dong", "sach", "cuon", "quyen", "tap", "k", "dong"}
    words = set(cleaned.lower().split())
    if words & blacklist:
        return default_name
    return cleaned


def extract_phone(text: str) -> Optional[str]:
    """Extract standard Vietnamese 10-digit mobile phone number."""
    match = re.search(PHONE_PATTERN, text)
    if match:
        clean = re.sub(r"[^\d]", "", match.group(0))
        if clean.startswith("84"):
            clean = "0" + clean[2:]
        if len(clean) == 10 and clean.startswith(("03", "05", "07", "08", "09")):
            return clean

    keyword_match = re.search(
        r"(?:sđt|sdt|đt|dt|phone|tel|số đt|số điện thoại)\s*[:\s]*((?:\+84|0)[\d\s.-]{9,13})",
        text,
        re.IGNORECASE,
    )
    if keyword_match:
        clean = re.sub(r"[^\d]", "", keyword_match.group(1))
        if clean.startswith("84"):
            clean = "0" + clean[2:]
        if len(clean) == 10 and clean.startswith(("03", "05", "07", "08", "09")):
            return clean

    return None


def extract_quantity(text: str, book_title: str = "") -> int:
    """Extract purchase quantity (e.g. '2 cuốn', '1 bộ', 'mua 3'). Defaults to 1."""
    text_lower = text.lower()
    unit_match = re.search(
        r"(\d+)\s*(cuốn|cuon|quyển|quyen|bản|ban|bộ|bo|tập|tap)\b",
        text_lower,
    )
    if unit_match:
        try:
            return max(1, int(unit_match.group(1)))
        except ValueError:
            pass

    action_match = re.search(r"(?:mua|lấy|đặt|cho|order|chốt)\s+(\d+)\b", text_lower)
    if action_match:
        try:
            return max(1, int(action_match.group(1)))
        except ValueError:
            pass

    any_num = re.search(r"\b(\d+)\b", text_lower)
    if any_num and len(text.split()) <= 8:
        try:
            val = int(any_num.group(1))
            if 1 <= val <= 100:
                return val
        except ValueError:
            pass

    return 1


def extract_payment_method(text: str) -> Optional[str]:
    """Extract payment choice: 'COD' or 'VIETQR'."""
    text_lower = text.lower().strip()
    stripped = text_lower.strip(" .!?,;:()[]{}")
    if stripped in ("1", "chọn 1", "chon 1", "phương thức 1", "hình thức 1", "cod"):
        return "COD"
    if stripped in ("2", "chọn 2", "chon 2", "phương thức 2", "hình thức 2", "vietqr", "qr", "chuyển khoản"):
        return "VIETQR"

    has_vietqr = bool(re.search(PAYMENT_VIETQR_PATTERN, text_lower))
    has_cod = bool(re.search(PAYMENT_COD_PATTERN, text_lower))

    if has_vietqr and not has_cod:
        return "VIETQR"
    if has_cod and not has_vietqr:
        return "COD"
    if has_vietqr and has_cod:
        m_vqr = re.search(PAYMENT_VIETQR_PATTERN, text_lower)
        m_cod = re.search(PAYMENT_COD_PATTERN, text_lower)
        if m_vqr and m_cod and m_vqr.start() > m_cod.start():
            return "VIETQR"
        return "COD"
    return None


def extract_address_and_name(text: str, phone: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Extract recipient name and delivery street address from conversational text."""
    cleaned = text
    if phone:
        cleaned = re.sub(
            rf"(?:sđt|sdt|đt|dt|số đt|số điện thoại|so dien thoai|tel|phone)?\s*[:\s]*{phone}",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

    # Recipient name matching
    name_match = re.search(
        r"\b(?:tên\s*(?:người\s*nhận|là)?|người\s*nhận|nguoi\s*nhan|anh|chị|chi|em|bác|bac)\s*[:\s]+([^\n,.;]+?)(?=\s+(?:ở|tại|sđt|sdt|đt|dt|phone|số|so\b)|[,\n.;]|$)",
        cleaned,
        re.IGNORECASE,
    )
    extracted_name = None
    if name_match:
        candidate = name_match.group(1).strip()
        if 2 <= len(candidate) <= 40 and re.match(r"^[A-Za-zÀ-ỹ\s]+$", candidate):
            blacklist = {"đ", "vnd", "vnđ", "dong", "giao", "ship", "mua", "dat", "sach", "don", "hang"}
            if not (set(candidate.lower().split()) & blacklist):
                extracted_name = candidate
                cleaned = cleaned.replace(name_match.group(0), "")

    # Address matching
    addr_match = re.search(r"(?:địa chỉ|ở|tại|giao đến|giao về|giao tại|dc|đc)\s*[:\s]+([^\n]+)", cleaned, re.IGNORECASE)
    if addr_match:
        extracted_addr = addr_match.group(1).strip()
    else:
        addr_cues = ["đường", "phố", "ngõ", "ngách", "số", "quận", "huyện", "phường", "xã", "thành phố", "hà nội", "hcm", "đà nẵng", "hải phòng", "cần thơ"]
        cleaned_lower = cleaned.lower()
        if any(cue in cleaned_lower for cue in addr_cues):
            junk_pattern = r"^(?:sđt|sdt|đt|dt|số điện thoại|so dien thoai|giao|gui|ship|đến|den|về|ve|cho)\s*[:\s]*"
            extracted_addr = re.sub(junk_pattern, "", cleaned.strip(), flags=re.IGNORECASE)
        else:
            extracted_addr = None

    if extracted_addr:
        extracted_addr = re.sub(r"[,.\s]*(?:sđt|sdt|đt|dt|số đt|số điện thoại|phone|tel)?\s*$", "", extracted_addr, flags=re.IGNORECASE)
        extracted_addr = re.sub(r"[,.\s]*(?:thanh toán|tt|pttt)?\s*(?:cod|tiền mặt|chuyển khoản|vietqr).*$", "", extracted_addr, flags=re.IGNORECASE)
        extracted_addr = extracted_addr.strip(",. ")
        if len(extracted_addr) > 255:
            extracted_addr = extracted_addr[:255]

    return extracted_name, extracted_addr


def format_payment_method_prompt(book: Book, qty: int, name: str, phone: str, address: str, is_update: bool = False) -> str:
    """Format payment method selection prompt with interactive Choice Cards."""
    subtotal = Decimal(str(book.price)) * Decimal(str(qty))
    shipping_fee = Decimal("0.00") if subtotal >= Decimal("500000.00") else Decimal("30000.00")
    total_amount = subtotal + shipping_fee
    ship_txt = "Miễn phí vận chuyển (Freeship)" if shipping_fee == 0 else format_currency(shipping_fee)

    header = "📖 **Đã cập nhật thông tin nhận sách:**" if is_update else "📖 **Xác nhận thông tin đặt sách:**"

    return (
        f"{header}\n\n"
        f"• Tác phẩm: **{qty} cuốn × {book.title}** ({format_currency(subtotal)})\n"
        f"• Phí giao hàng: **{ship_txt}** (Freeship từ 500.000 đ)\n"
        f"• Tổng thanh toán: **{format_currency(total_amount)}**\n"
        f"• Người nhận: **{name}** — {phone}\n"
        f"• Địa chỉ nhận sách: **{address}**\n\n"
        f"👉 **Quý khách muốn thanh toán theo hình thức nào ạ?**\n\n"
        f"[choice:Thanh toán khi nhận hàng (COD)|Trả tiền mặt cho nhân viên giao hàng khi nhận sách|💵](COD)\n"
        f"[choice:Chuyển khoản VietQR|Quét mã QR Napas 247 qua app Mobile Banking ngân hàng|💳](Chuyển khoản VietQR)\n\n"
        f"*(Quý khách hãy bấm chọn một trong 2 nút ở trên hoặc nhắn tin **'COD'** / **'Chuyển khoản'** để em chốt đơn ngay nhé!)*"
    )


def execute_direct_order(
    db: Session,
    user: User,
    book: Book,
    quantity: int,
    recipient_name: str,
    phone: str,
    address: str,
    payment_method: str,
) -> Order:
    """Execute authoritative direct order creation with pessimistic row-locking on inventory."""
    # Pessimistic locking: SELECT ... FOR UPDATE
    inv = (
        db.query(Inventory)
        .filter(Inventory.book_id == book.id)
        .with_for_update()
        .first()
    )
    if not inv:
        raise ValueError(f"Tác phẩm '{book.title}' không có dữ liệu tồn kho.")

    available = inv.physical_stock - inv.reserved_stock
    if available < quantity:
        raise ValueError(f"Tác phẩm '{book.title}' chỉ còn {available} cuốn khả dụng, không đủ số lượng yêu cầu.")

    # Re-fetch authoritative book price
    book_price = Decimal(str(book.price))
    subtotal = book_price * Decimal(str(quantity))
    shipping_fee = Decimal("0.00") if subtotal >= Decimal("500000.00") else Decimal("30000.00")
    total_amount = (subtotal + shipping_fee).quantize(Decimal("0.01"))

    # Reserve inventory stock safely
    inv.reserved_stock += quantity

    timestamp_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:6].upper()
    order_code = f"NVL-{timestamp_prefix}-{random_suffix}"
    payment_code = f"PAY-{uuid.uuid4().hex[:8].upper()}"

    initial_status = "CONFIRMED" if payment_method == "COD" else "PENDING"

    order = Order(
        order_code=order_code,
        user_id=user.id,
        subtotal_amount=subtotal.quantize(Decimal("0.01")),
        shipping_fee=shipping_fee.quantize(Decimal("0.01")),
        discount_amount=Decimal("0.00"),
        total_amount=total_amount,
        status=initial_status,
        recipient_name=recipient_name,
        recipient_phone=phone,
        shipping_province="Toàn quốc",
        shipping_district="Nội địa",
        shipping_ward="Giao nhanh",
        shipping_street_address=address,
        customer_notes="Đặt hàng trực tiếp qua Novelia AI Assistant",
        staff_notes=f"Kênh đàm thoại AI ({payment_method})",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(order)
    db.flush()

    order_item = OrderItem(
        order_id=order.id,
        book_id=book.id,
        book_title_snapshot=book.title,
        book_isbn_snapshot=book.isbn,
        book_sku_snapshot=book.sku,
        price_at_purchase=book_price,
        quantity=quantity,
        subtotal=subtotal,
        created_at=datetime.now(timezone.utc),
    )
    db.add(order_item)

    payment = Payment(
        order_id=order.id,
        payment_code=payment_code,
        payment_method=payment_method,
        amount=total_amount,
        status="SUCCESS" if payment_method == "COD" else "PENDING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(payment)

    shipment = Shipment(
        order_id=order.id,
        tracking_number=f"TRK-{order_code[-8:]}",
        shipping_provider="GHN",
        shipping_fee=shipping_fee,
        status="PENDING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(shipment)

    db.commit()
    db.refresh(order)
    return order


def format_order_success_message(order: Order, book: Book, qty: int) -> str:
    """Format successful order confirmation message with VietQR or COD details."""
    subtotal = Decimal(str(book.price)) * Decimal(str(qty))
    ship_txt = "Miễn phí vận chuyển" if order.shipping_fee == 0 else format_currency(order.shipping_fee)

    base_info = (
        f"🎉 **ĐẶT SÁCH THÀNH CÔNG QUA NOVELIA AI ASSISTANT!**\n\n"
        f"• Mã đơn hàng: **{order.order_code}**\n"
        f"• Tác phẩm: **{qty} cuốn × {book.title}** ({format_currency(subtotal)})\n"
        f"• Phí vận chuyển: **{ship_txt}** (Freeship từ 500.000 đ)\n"
        f"• Tổng thanh toán: **{format_currency(order.total_amount)}**\n"
        f"• Người nhận: **{order.recipient_name}** — {order.recipient_phone}\n"
        f"• Địa chỉ nhận: {order.shipping_street_address}\n\n"
    )

    if order.payment and order.payment.payment_method == "VIETQR":
        qr_url = get_vietqr_url(order.order_code, order.total_amount)
        qr_info = get_vietqr_info(order.order_code, order.total_amount)
        payment_section = (
            f"💳 **Hình thức thanh toán: Chuyển khoản VietQR (Napas 247)**\n\n"
            f"![Mã VietQR thanh toán {order.order_code}]({qr_url})\n\n"
            f"• Ngân hàng thụ hưởng: **{qr_info['bank_name']}** ({qr_info['bank_id']})\n"
            f"• Số tài khoản: **{qr_info['account_no']}** ({qr_info['account_name']})\n"
            f"• Số tiền: **{format_currency(order.total_amount)}**\n"
            f"• Nội dung chuyển khoản: **{order.order_code}**\n\n"
            f"👉 [Bấm vào đây để xem chi tiết đơn hàng](/orders/{order.order_code})\n\n"
            f"*(Quý khách chỉ cần mở app ngân hàng bất kỳ, quét mã QR trên là hệ thống tự điền chính xác số tiền và nội dung CK ạ!)*\n\n"
            f"Cảm ơn Quý khách đã tin chọn sách tại NOVELIA BOOKS! Sách sẽ được đóng gói cẩn thận và gửi đến Quý khách sớm nhất."
        )
    else:  # COD
        payment_section = (
            f"💵 **Hình thức thanh toán: Thanh toán tiền mặt khi nhận hàng (COD)**\n"
            f"• Trạng thái đơn: **Đã xác nhận & Đang chuẩn bị sách**\n"
            f"• Shipper sẽ liên hệ số điện thoại **{order.recipient_phone}** trước khi giao sách.\n"
            f"• Quý khách vui lòng chuẩn bị số tiền **{format_currency(order.total_amount)}** khi nhận sách nhé.\n\n"
            f"👉 [Bấm vào đây để xem chi tiết đơn hàng](/orders/{order.order_code})\n\n"
            f"Cảm ơn Quý khách đã đồng hành cùng NOVELIA BOOKS! Chúc Quý khách có những giây phút đọc sách thật trọn vẹn và ý nghĩa! 📚"
        )

    return base_info + payment_section


class OrderAssistantService:
    """Orchestrator for natural language multi-turn order workflows."""

    @classmethod
    def handle_order_conversation(
        cls,
        db: Session,
        message: str,
        session_uuid: str,
        current_user: Optional[User] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Process conversational order requests.

        Returns: (handled: bool, reply_text: str, structured_payload: Optional[Dict])
        """
        msg = message.strip()
        msg_lower = msg.lower()
        draft = _ORDER_DRAFTS.get(session_uuid)

        # 1. CANCEL INTENT
        if draft and any(re.search(pat, msg_lower, re.IGNORECASE) for pat in CANCEL_TRIGGERS):
            _ORDER_DRAFTS.pop(session_uuid, None)
            return True, "Dạ vâng, em đã hủy yêu cầu lên đơn hàng. Quý khách có muốn em tư vấn thêm cuốn sách nào khác không ạ? 📚", None

        # 2. ONGOING ORDER DRAFT PROCESSING
        if draft:
            step = draft.get("step")
            book_id = draft.get("book_id")
            qty = draft.get("quantity", 1)

            book = db.query(Book).filter(Book.id == book_id, Book.status == "ACTIVE").first()
            if not book:
                _ORDER_DRAFTS.pop(session_uuid, None)
                return True, "Rất tiếc, cuốn sách Quý khách chọn hiện không còn khả dụng trên hệ thống. Quý khách vui lòng chọn cuốn khác nhé!", None

            user_default_name = current_user.full_name if current_user and current_user.full_name else "Quý khách"

            # Step A: Awaiting Payment Method
            if step in ("awaiting_payment_method", "awaiting_confirm"):
                pm = extract_payment_method(msg)
                if pm:
                    recipient_name = sanitize_name(draft.get("full_name"), user_default_name)
                    phone = draft.get("phone") or (current_user.phone if current_user else "0988776655")
                    address = draft.get("address") or "Địa chỉ nhận sách"
                    try:
                        order = execute_direct_order(
                            db=db,
                            user=current_user,
                            book=book,
                            quantity=qty,
                            recipient_name=recipient_name,
                            phone=phone,
                            address=address,
                            payment_method=pm,
                        )
                        _ORDER_DRAFTS.pop(session_uuid, None)
                        success_text = format_order_success_message(order, book, qty)
                        payload = {
                            "order_success": {
                                "order_code": order.order_code,
                                "total_amount": float(order.total_amount),
                                "payment_method": pm,
                                "book_id": book.id,
                                "title": book.title,
                            }
                        }
                        return True, success_text, payload
                    except Exception as e:
                        return True, f"⚠️ Rất tiếc, có lỗi xảy ra khi tạo đơn hàng: {str(e)}. Quý khách vui lòng thử lại nhé!", None

                # Check if user updated phone or address
                new_phone = extract_phone(msg)
                new_name, new_addr = extract_address_and_name(msg, new_phone)
                if new_phone:
                    draft["phone"] = new_phone
                if new_addr:
                    draft["address"] = new_addr
                if new_name:
                    draft["full_name"] = sanitize_name(new_name, user_default_name)

                if new_phone or new_addr:
                    prompt_text = format_payment_method_prompt(
                        book, qty,
                        draft.get("full_name", user_default_name),
                        draft.get("phone", ""),
                        draft.get("address", ""),
                        is_update=True,
                    )
                    return True, prompt_text, None

                # Confirmation trigger without selecting payment method
                if any(re.search(pat, msg_lower, re.IGNORECASE) for pat in CONFIRM_TRIGGERS):
                    return True, (
                        f"📚 Cảm ơn Quý khách! Để hoàn tất đơn hàng **{qty} cuốn × {book.title}**, Quý khách vui lòng chọn hình thức thanh toán:\n\n"
                        f"[choice:Thanh toán khi nhận hàng (COD)|Trả tiền mặt cho shipper khi nhận sách|💵](COD)\n"
                        f"[choice:Chuyển khoản VietQR|Quét mã QR Napas 247 qua app ngân hàng|💳](Chuyển khoản VietQR)\n\n"
                        f"*(Quý khách chỉ cần bấm chọn một trong 2 hình thức ở trên hoặc nhắn tin nhé!)*"
                    ), None

                return True, (
                    f"📚 Quý khách vui lòng chọn hình thức thanh toán để em chốt đơn ngay nhé:\n\n"
                    f"[choice:Thanh toán khi nhận hàng (COD)|Trả tiền mặt cho shipper khi nhận sách|💵](COD)\n"
                    f"[choice:Chuyển khoản VietQR|Quét mã QR Napas 247 qua app ngân hàng|💳](Chuyển khoản VietQR)\n\n"
                    f"*(Hoặc nhắn 'Hủy' nếu Quý khách đổi ý không mua nữa ạ)*"
                ), None

            # Step B: Awaiting Contact & Address Info
            if step == "awaiting_info":
                phone = extract_phone(msg) or draft.get("phone")
                name, addr = extract_address_and_name(msg, phone)
                addr = addr or draft.get("address")
                name = sanitize_name(name or draft.get("full_name"), user_default_name)
                pm = extract_payment_method(msg) or draft.get("payment_method")

                if phone:
                    draft["phone"] = phone
                if addr:
                    draft["address"] = addr
                draft["full_name"] = name
                if pm:
                    draft["payment_method"] = pm

                if phone and addr:
                    if pm:
                        try:
                            order = execute_direct_order(
                                db=db,
                                user=current_user,
                                book=book,
                                quantity=qty,
                                recipient_name=name,
                                phone=phone,
                                address=addr,
                                payment_method=pm,
                            )
                            _ORDER_DRAFTS.pop(session_uuid, None)
                            success_text = format_order_success_message(order, book, qty)
                            payload = {
                                "order_success": {
                                    "order_code": order.order_code,
                                    "total_amount": float(order.total_amount),
                                    "payment_method": pm,
                                    "book_id": book.id,
                                    "title": book.title,
                                }
                            }
                            return True, success_text, payload
                        except Exception as e:
                            return True, f"⚠️ Có lỗi khi tạo đơn: {str(e)}. Quý khách vui lòng thử lại!", None
                    else:
                        draft["step"] = "awaiting_payment_method"
                        return True, format_payment_method_prompt(book, qty, name, phone, addr), None
                elif not phone:
                    return True, (
                        f"📖 Em đã ghi nhận địa chỉ nhận sách: **{addr}**.\n\n"
                        f"Quý khách vui lòng cung cấp thêm **Số điện thoại nhận hàng** để em tiến hành lên đơn ngay nhé!"
                    ), None
                else:
                    return True, (
                        f"📖 Em đã ghi nhận số điện thoại: **{phone}**.\n\n"
                        f"Quý khách vui lòng cung cấp thêm **Địa chỉ giao hàng chi tiết** (Số nhà, đường, phường/xã, quận/huyện, tỉnh/TP) để em chốt đơn nhé!"
                    ), None

        # 3. NEW ORDER INTENT DETECTION
        is_order_intent = any(re.search(pat, msg_lower, re.IGNORECASE) for pat in ORDER_TRIGGERS)
        if not is_order_intent:
            return False, "", None

        # Authenticated user requirement (Enterprise RBAC security rule)
        if not current_user:
            return True, (
                "📖 Để lên đơn hàng trực tiếp và nhận mã VietQR thanh toán, Quý khách vui lòng "
                "**Đăng nhập** hoặc **Đăng ký tài khoản** nhé!\n\n"
                "Sau khi đăng nhập, Quý khách chỉ cần nhắn tên cuốn sách và số lượng, em sẽ hỗ trợ tạo đơn ngay lập tức!"
            ), None

        # Book matching
        matched_books = find_matching_books(db, msg, limit=3)
        if not matched_books:
            return True, (
                "📖 Quý khách muốn đặt mua tác phẩm nào ạ? Hiện NOVELIA BOOKS có đầy đủ các đầu sách Văn học, Kinh tế, Kỹ năng sống, Công nghệ, Manga...\n\n"
                "Quý khách hãy nhắn: **'Mua [Số lượng] [Tên sách]'** (ví dụ: *Mua 1 cuốn Đắc Nhân Tâm* hoặc *Lên đơn 2 cuốn Nhà Giả Kim*) để em hỗ trợ lên đơn ngay nhé!"
            ), None

        book = matched_books[0]
        qty = extract_quantity(msg, book.title)

        # Inventory check
        stock = get_book_available_stock(db, book.id)
        if stock <= 0:
            return True, (
                f"📖 Rất tiếc, tác phẩm **{book.title}** hiện tại đang tạm hết hàng trong kho NOVELIA BOOKS.\n"
                f"Quý khách có muốn tham khảo các tác phẩm tương tự cùng thể loại {book.category.name if book.category else ''} không ạ?"
            ), None

        if qty > stock:
            return True, (
                f"📖 Tác phẩm **{book.title}** hiện chỉ còn **{stock} cuốn** khả dụng trong kho.\n"
                f"Quý khách có muốn đặt với số lượng **{stock} cuốn** không ạ?"
            ), None

        # Check for recipient info provided in the initial message
        phone = extract_phone(msg) or (current_user.phone if current_user and current_user.phone else None)
        name, addr = extract_address_and_name(msg, phone)
        user_name = sanitize_name(name or (current_user.full_name if current_user else None))
        pm = extract_payment_method(msg)

        # Initialize draft
        draft_state = {
            "book_id": book.id,
            "quantity": qty,
            "full_name": user_name,
            "phone": phone,
            "address": addr,
            "payment_method": pm,
            "step": "awaiting_info",
        }
        _ORDER_DRAFTS[session_uuid] = draft_state

        if phone and addr:
            if pm:
                try:
                    order = execute_direct_order(
                        db=db,
                        user=current_user,
                        book=book,
                        quantity=qty,
                        recipient_name=user_name,
                        phone=phone,
                        address=addr,
                        payment_method=pm,
                    )
                    _ORDER_DRAFTS.pop(session_uuid, None)
                    success_text = format_order_success_message(order, book, qty)
                    payload = {
                        "order_success": {
                            "order_code": order.order_code,
                            "total_amount": float(order.total_amount),
                            "payment_method": pm,
                            "book_id": book.id,
                            "title": book.title,
                        }
                    }
                    return True, success_text, payload
                except Exception as e:
                    return True, f"⚠️ Có lỗi khi tạo đơn: {str(e)}. Quý khách vui lòng thử lại!", None
            else:
                draft_state["step"] = "awaiting_payment_method"
                return True, format_payment_method_prompt(book, qty, user_name, phone, addr), None

        # Missing phone or address
        missing_prompts = []
        if not phone:
            missing_prompts.append("• **Số điện thoại nhận hàng**")
        if not addr:
            missing_prompts.append("• **Địa chỉ nhận sách chi tiết** (Số nhà, đường, phường, quận/huyện, tỉnh/TP)")

        subtotal = Decimal(str(book.price)) * Decimal(str(qty))
        return True, (
            f"📖 Em đã ghi nhận Quý khách muốn đặt **{qty} cuốn × {book.title}** ({format_currency(subtotal)}).\n\n"
            f"Để em hoàn tất lên đơn giao tận tay Quý khách, Quý khách vui lòng cung cấp thêm:\n"
            + "\n".join(missing_prompts) + "\n\n"
            f"*(Ví dụ: 0912345678, số 123 Cầu Giấy, Hà Nội)*"
        ), None
