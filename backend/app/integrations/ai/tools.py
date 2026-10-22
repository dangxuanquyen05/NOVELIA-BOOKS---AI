import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.integrations.ai.base import ToolDefinition
from app.integrations.ai.permissions import verify_tool_permission
from app.models.ai import AIActionLog
from app.models.catalog import Book
from app.models.commerce import Coupon, Order
from app.models.inventory import Inventory
from app.models.user import User
from app.repositories.admin_dashboard_repo import AdminDashboardRepository
from app.repositories.catalog_repo import BookRepository
from app.repositories.coupon_repo import CouponRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.recommendation_repo import RecommendationRepository
from app.repositories.shipment_repo import ShipmentRepository
from app.repositories.user_repo import UserRepository
from app.schemas.catalog import BookFilterParams, BookUpdate
from app.services.catalog_service import CatalogService, to_book_list_read
from app.services.commerce_service import CartService
from app.services.shipping_service import CARRIER_STATUS_LABELS

# ==============================================================================
# TOOL SCHEMAS PRESENTED TO THE LLM
# ==============================================================================

CUSTOMER_TOOL_DEFINITIONS: List[ToolDefinition] = [
    ToolDefinition(
        name="search_catalog_tool",
        description="Tìm kiếm sách trong danh mục theo từ khóa, tác giả, thể loại, hoặc khoảng giá tối đa/tối thiểu.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Từ khóa tìm kiếm theo tựa đề sách hoặc nội dung",
                },
                "category_slug": {
                    "type": "string",
                    "description": "Slug danh mục hoặc thể loại (ví dụ: 'van-hoc', 'kinh-te', 'ky-nang')",
                },
                "author_name": {
                    "type": "string",
                    "description": "Tên tác giả cần tìm",
                },
                "max_price": {
                    "type": "number",
                    "description": "Ngân sách tối đa tính bằng VNĐ (ví dụ: 150000)",
                },
                "min_price": {
                    "type": "number",
                    "description": "Giá tối thiểu tính bằng VNĐ",
                },
                "limit": {
                    "type": "integer",
                    "description": "Số lượng kết quả tối đa cần trả về (mặc định: 4, tối đa: 8)",
                },
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_book_details_tool",
        description="Lấy thông tin chi tiết đầy đủ của một cuốn sách theo mã ID hoặc URL slug (tác giả, NXB, số trang, tóm tắt, giá bán).",
        parameters={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "ID số (ví dụ: '1') hoặc URL slug của cuốn sách (ví dụ: 'dac-nhan-tam')",
                },
            },
            "required": ["identifier"],
        },
    ),
    ToolDefinition(
        name="check_book_stock_tool",
        description="Kiểm tra tồn kho thực tế và giá bán chính xác của một đầu sách dựa trên ID hoặc tên sách.",
        parameters={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Mã ID cuốn sách hoặc tên sách cần tra cứu tồn kho",
                },
            },
            "required": ["identifier"],
        },
    ),
    ToolDefinition(
        name="add_to_cart_tool",
        description="Thêm một cuốn sách vào giỏ hàng của khách hàng đang đăng nhập với số lượng xác định.",
        parameters={
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "integer",
                    "description": "Mã ID của cuốn sách muốn thêm vào giỏ",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Số lượng sách muốn mua (mặc định: 1)",
                },
            },
            "required": ["book_id"],
        },
    ),
    ToolDefinition(
        name="get_my_orders_tool",
        description="Tra cứu danh sách đơn hàng đã mua gần đây của chính tài khoản khách hàng đang đăng nhập.",
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Số lượng đơn hàng cần lấy (mặc định: 5)",
                },
                "status_filter": {
                    "type": "string",
                    "description": "Lọc theo trạng thái đơn (PENDING, CONFIRMED, PROCESSING, SHIPPING, COMPLETED, CANCELLED)",
                },
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="track_order_status_tool",
        description="Theo dõi chi tiết tiến trình giao hàng, đơn vị vận chuyển và mã vận đơn của đơn hàng.",
        parameters={
            "type": "object",
            "properties": {
                "order_code": {
                    "type": "string",
                    "description": "Mã đơn hàng cần theo dõi (ví dụ: 'NVL-20261020-ABC123')",
                },
            },
            "required": ["order_code"],
        },
    ),
    ToolDefinition(
        name="get_shipping_and_checkout_guide_tool",
        description="Xem chính sách phí giao hàng, điều kiện miễn phí ship, thời gian vận chuyển và các hình thức thanh toán.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_reading_recommendations_tool",
        description="Lấy danh sách các tác phẩm nổi bật, bán chạy nhất hoặc gợi ý theo thể loại từ Novelia Books.",
        parameters={
            "type": "object",
            "properties": {
                "category_slug": {
                    "type": "string",
                    "description": "Thể loại muốn nhận gợi ý (ví dụ: 'van-hoc', 'kinh-te')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Số lượng gợi ý (mặc định: 4)",
                },
            },
            "required": [],
        },
    ),
]


ADMIN_TOOL_DEFINITIONS: List[ToolDefinition] = [
    ToolDefinition(
        name="get_sales_summary",
        description="Xem báo cáo tổng hợp doanh thu bán hàng, doanh thu thực thu, tổng số đơn, số đơn hợp lệ, và giá trị trung bình đơn (AOV).",
        parameters={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Ngày bắt đầu lọc (định dạng YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "Ngày kết thúc lọc (định dạng YYYY-MM-DD)",
                },
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_inventory_summary",
        description="Xem tổng quan tình hình kho hàng toàn hệ thống: tổng đầu sách, tổng tồn kho vật lý, tồn kho giữ chỗ và số lượng sách cảnh báo sắp hết hàng.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolDefinition(
        name="find_low_stock_books",
        description="Tìm danh sách các đầu sách có lượng tồn kho khả dụng dưới hoặc bằng ngưỡng an toàn để kịp thời nhập bổ sung.",
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Số lượng sách cần liệt kê (mặc định: 10)",
                },
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="search_orders",
        description="Tra cứu danh sách đơn hàng toàn hệ thống theo từ khóa tìm kiếm (mã đơn, tên khách, số điện thoại) hoặc theo trạng thái đơn hàng.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Từ khóa tìm kiếm (mã đơn, tên người nhận hoặc số điện thoại)",
                },
                "status": {
                    "type": "string",
                    "description": "Trạng thái đơn (PENDING, CONFIRMED, PROCESSING, SHIPPING, COMPLETED, CANCELLED)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Số lượng đơn hàng tối đa cần lấy (mặc định: 5)",
                },
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="search_books",
        description="Tra cứu sách trong danh mục quản trị theo từ khóa, tác giả hoặc danh mục.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Từ khóa tìm kiếm tựa sách, ISBN hoặc tác giả",
                },
                "category_slug": {
                    "type": "string",
                    "description": "Slug danh mục sách cần lọc",
                },
                "limit": {
                    "type": "integer",
                    "description": "Số lượng kết quả cần lấy (mặc định: 5)",
                },
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="prepare_book_update",
        description="Chuẩn bị cập nhật thông tin sách (sửa giá bán, giá niêm yết, tựa đề, trạng thái). Tạo bản xem trước thay đổi và yêu cầu xác nhận trước khi thực thi vào cơ sở dữ liệu.",
        parameters={
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "integer",
                    "description": "Mã ID của cuốn sách cần cập nhật",
                },
                "new_price": {
                    "type": "number",
                    "description": "Giá bán mới bằng VNĐ (nếu có cập nhật giá)",
                },
                "new_original_price": {
                    "type": "number",
                    "description": "Giá bìa niêm yết gốc mới (nếu có)",
                },
                "new_title": {
                    "type": "string",
                    "description": "Tựa đề sách mới (nếu có)",
                },
                "status": {
                    "type": "string",
                    "description": "Trạng thái sách mới (ACTIVE, INACTIVE, DRAFT)",
                },
            },
            "required": ["book_id"],
        },
    ),
    ToolDefinition(
        name="draft_product_description",
        description="Soạn thảo bản nháp bài viết mô tả sản phẩm hấp dẫn, tóm tắt nội dung chính và các điểm nổi bật (selling points) cho sách.",
        parameters={
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "integer",
                    "description": "Mã ID của sách cần viết bài mô tả",
                },
                "custom_tone": {
                    "type": "string",
                    "description": "Tông giọng (truyền cảm hứng, học thuật, hấp dẫn, ngắn gọn)",
                },
            },
            "required": ["book_id"],
        },
    ),
    ToolDefinition(
        name="draft_promotion",
        description="Tạo bản nháp mã giảm giá/khuyến mãi (coupon) mới. Cần xác nhận trước khi kích hoạt mã vào hệ thống.",
        parameters={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Mã khuyến mãi (ví dụ: 'SALE2026', 'SUMMER20')",
                },
                "discount_percent": {
                    "type": "integer",
                    "description": "Phần trăm giảm giá (1 đến 100)",
                },
                "max_discount_amount": {
                    "type": "number",
                    "description": "Số tiền giảm tối đa bằng VNĐ (mặc định: 50000)",
                },
                "min_order_amount": {
                    "type": "number",
                    "description": "Giá trị đơn hàng tối thiểu áp dụng (mặc định: 100000)",
                },
                "usage_limit": {
                    "type": "integer",
                    "description": "Giới hạn số lượt sử dụng toàn hệ thống (mặc định: 100)",
                },
                "duration_days": {
                    "type": "integer",
                    "description": "Số ngày có hiệu lực của mã (mặc định: 30)",
                },
            },
            "required": ["code", "discount_percent"],
        },
    ),
    ToolDefinition(
        name="prepare_inventory_adjustment",
        description="Chuẩn bị điều chỉnh số lượng tồn kho vật lý của một đầu sách (+ tăng nhập kho hoặc - giảm hao hụt/hư hại). Cần xác nhận trước khi cập nhật số liệu kho thực tế.",
        parameters={
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "integer",
                    "description": "Mã ID cuốn sách cần điều chỉnh tồn kho",
                },
                "delta": {
                    "type": "integer",
                    "description": "Số lượng thay đổi (dương để tăng nhập kho, âm để giảm; ví dụ: 20 hoặc -5)",
                },
                "reason": {
                    "type": "string",
                    "description": "Lý do điều chỉnh (ví dụ: 'Nhập bổ sung từ NXB', 'Hao hụt rách sách')",
                },
            },
            "required": ["book_id", "delta", "reason"],
        },
    ),
]


# ==============================================================================
# TOOL EXECUTOR DISPATCHER
# ==============================================================================

class AIToolExecutor:
    """Executes backend business services within current user security context."""

    @classmethod
    def execute(
        cls,
        db: Session,
        tool_name: str,
        arguments: Dict[str, Any],
        current_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Validate permissions and execute backend domain service."""
        user_roles = (
            UserRepository.get_user_role_names(current_user) if current_user else ["GUEST"]
        )

        is_allowed, reason = verify_tool_permission(tool_name, user_roles)
        if not is_allowed:
            return {
                "success": False,
                "error_code": "REJECTED_RBAC",
                "message": reason,
            }

        handler = getattr(cls, f"_tool_{tool_name}", None)
        if not handler:
            return {
                "success": False,
                "error_code": "TOOL_NOT_FOUND",
                "message": f"Không tìm thấy hàm xử lý nghiệp vụ cho công cụ '{tool_name}'.",
            }

        try:
            return handler(db, arguments, current_user)
        except Exception as exc:
            return {
                "success": False,
                "error_code": "EXECUTION_ERROR",
                "message": f"Lỗi trong quá trình xử lý: {str(exc)}",
            }

    # --------------------------------------------------------------------------
    # Individual Tool Handlers
    # --------------------------------------------------------------------------

    @classmethod
    def _tool_search_catalog_tool(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        query = args.get("query")
        category_slug = args.get("category_slug")
        limit = min(int(args.get("limit") or 4), 8)
        max_price = Decimal(str(args["max_price"])) if args.get("max_price") is not None else None
        min_price = Decimal(str(args["min_price"])) if args.get("min_price") is not None else None

        params = BookFilterParams(
            search=query,
            category_slug=category_slug,
            min_price=min_price,
            max_price=max_price,
            page=1,
            page_size=limit,
            sort_by="popular",
        )

        items, total = BookRepository.list_books(db, params)
        books = [to_book_list_read(b) for b in items]

        formatted = []
        for b in books:
            formatted.append(
                {
                    "id": b.id,
                    "title": b.title,
                    "slug": b.slug,
                    "price": float(b.price),
                    "original_price": float(b.original_price) if b.original_price else None,
                    "discount_percent": b.discount_percent,
                    "primary_author": b.primary_author,
                    "primary_category": b.categories[0].name if b.categories else None,
                    "cover_image_url": b.cover_image_url,
                    "available_stock": b.stock_available,
                    "is_in_stock": b.is_in_stock,
                }
            )

        return {
            "success": True,
            "total_matches": total,
            "returned_count": len(formatted),
            "books": formatted,
        }

    @classmethod
    def _tool_get_book_details_tool(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        identifier = str(args.get("identifier", "")).strip()
        if not identifier:
            return {"success": False, "message": "Vui lòng cung cấp mã ID hoặc slug của cuốn sách."}

        try:
            book_read = CatalogService.get_book_by_slug_or_id(db, identifier)
            return {
                "success": True,
                "book": {
                    "id": book_read.id,
                    "title": book_read.title,
                    "slug": book_read.slug,
                    "isbn": book_read.isbn,
                    "price": float(book_read.price),
                    "original_price": float(book_read.original_price) if book_read.original_price else None,
                    "description": book_read.description,
                    "publisher": book_read.publisher_name,
                    "publication_year": book_read.publication_year,
                    "page_count": book_read.page_count,
                    "format": book_read.format,
                    "available_stock": book_read.available_stock,
                    "cover_image_url": book_read.cover_image_url,
                    "authors": [a.name for a in book_read.authors],
                    "categories": [c.name for c in book_read.categories],
                },
            }
        except Exception as e:
            return {"success": False, "message": f"Không tìm thấy sách: {str(e)}"}

    @classmethod
    def _tool_check_book_stock_tool(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        identifier = str(args.get("identifier", "")).strip()
        if not identifier:
            return {"success": False, "message": "Vui lòng cung cấp mã sách hoặc tên sách."}

        book = None
        if identifier.isdigit():
            book = BookRepository.get_by_id(db, int(identifier))
        if not book:
            book = BookRepository.get_by_slug(db, identifier)
        if not book:
            # Try fuzzy search by title
            items, _ = BookRepository.list_books(db, BookFilterParams(search=identifier, page_size=1))
            if items:
                book = items[0]

        if not book:
            return {
                "success": False,
                "message": f"Không tìm thấy tác phẩm '{identifier}' trong kho của Novelia Books.",
            }

        inv = book.inventory
        physical = inv.physical_stock if inv else 0
        reserved = inv.reserved_stock if inv else 0
        available = inv.available_stock if inv else 0

        return {
            "success": True,
            "book_id": book.id,
            "title": book.title,
            "price": float(book.price),
            "physical_stock": physical,
            "reserved_stock": reserved,
            "available_stock": available,
            "is_available": available > 0 and book.status == "ACTIVE",
            "status_message": (
                f"Tác phẩm '{book.title}' hiện còn {available} cuốn sẵn sàng giao ngay."
                if available > 0
                else f"Tác phẩm '{book.title}' hiện đã tạm hết hàng trong kho."
            ),
        }

    @classmethod
    def _tool_add_to_cart_tool(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        if not current_user:
            return {
                "success": False,
                "requires_auth": True,
                "message": "Quý khách vui lòng đăng nhập tài khoản để thêm sách vào giỏ hàng cá nhân.",
            }

        book_id = args.get("book_id")
        quantity = int(args.get("quantity") or 1)

        try:
            cart = CartService.add_item(
                db=db, user_id=current_user.id, book_id=int(book_id), quantity=quantity
            )
            # Find the added book details for nice display
            book = db.query(Book).filter(Book.id == book_id).first()
            return {
                "success": True,
                "book_id": book_id,
                "book_title": book.title if book else "Sách",
                "quantity_added": quantity,
                "cart_total_items": cart.total_items,
                "cart_subtotal": float(cart.subtotal_amount),
                "message": f"Đã thêm thành công {quantity} cuốn '{book.title if book else 'sách'}' vào giỏ hàng!",
            }
        except Exception as exc:
            return {"success": False, "message": str(getattr(exc, "detail", str(exc)))}

    @classmethod
    def _tool_get_my_orders_tool(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        if not current_user:
            return {
                "success": False,
                "requires_auth": True,
                "message": "Quý khách vui lòng đăng nhập tài khoản để tra cứu lịch sử đơn hàng.",
            }

        limit = min(int(args.get("limit") or 5), 10)
        status_filter = args.get("status_filter")

        items, total = OrderRepository.list_user_orders(
            db, user_id=current_user.id, page=1, page_size=limit, status=status_filter
        )

        orders = []
        for o in items:
            orders.append(
                {
                    "order_code": o.order_code,
                    "status": o.status,
                    "total_amount": float(o.total_amount),
                    "created_at": o.created_at.strftime("%d/%m/%Y %H:%M"),
                    "item_count": sum(it.quantity for it in o.items),
                    "payment_method": o.payment.payment_method if o.payment else "COD",
                    "payment_status": o.payment.payment_status if o.payment else "PENDING",
                    "carrier": o.shipment.carrier if getattr(o, "shipment", None) else None,
                    "tracking_code": o.shipment.tracking_code if getattr(o, "shipment", None) else None,
                    "shipment_status": (
                        CARRIER_STATUS_LABELS.get(o.shipment.status, o.shipment.status)
                        if getattr(o, "shipment", None)
                        else "Chưa xuất kho"
                    ),
                }
            )

        return {
            "success": True,
            "total_orders": total,
            "orders": orders,
        }

    @classmethod
    def _tool_track_order_status_tool(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        if not current_user:
            return {
                "success": False,
                "requires_auth": True,
                "message": "Quý khách vui lòng đăng nhập để theo dõi tiến trình đơn hàng.",
            }

        order_code = str(args.get("order_code", "")).strip()
        if not order_code:
            return {"success": False, "message": "Vui lòng cung cấp mã đơn hàng cần kiểm tra."}

        # Multi-tenant isolation: check ownership
        user_roles = UserRepository.get_user_role_names(current_user)
        is_staff = any(r in ["STAFF", "ADMIN"] for r in user_roles)
        user_id = None if is_staff else current_user.id

        order = OrderRepository.get_by_code(db, order_code, user_id=user_id)
        if not order:
            return {
                "success": False,
                "message": f"Không tìm thấy đơn hàng mã '{order_code}' trong tài khoản của bạn.",
            }

        shipment = order.shipment
        events = []
        if shipment:
            shipment_events = ShipmentRepository.list_events(db, shipment.id)
            for ev in shipment_events:
                events.append(
                    {
                        "status": CARRIER_STATUS_LABELS.get(ev.status, ev.status),
                        "description": ev.description,
                        "location": ev.location,
                        "time": ev.created_at.strftime("%d/%m/%Y %H:%M"),
                    }
                )

        return {
            "success": True,
            "order_code": order.order_code,
            "order_status": order.status,
            "total_amount": float(order.total_amount),
            "carrier": shipment.carrier if shipment else "Chưa phân bổ",
            "tracking_code": shipment.tracking_code if shipment else None,
            "shipment_status": (
                CARRIER_STATUS_LABELS.get(shipment.status, shipment.status)
                if shipment
                else "Đang chuẩn bị hàng tại kho"
            ),
            "timeline": events,
        }

    @classmethod
    def _tool_get_shipping_and_checkout_guide_tool(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "policies": {
                "free_shipping_threshold": 500000,
                "standard_shipping_fee": 30000,
                "shipping_rule_description": "Miễn phí vận chuyển cho tất cả đơn hàng từ 500.000 VNĐ. Đơn hàng dưới 500.000 VNĐ áp dụng phí giao hàng cố định 30.000 VNĐ toàn quốc.",
                "delivery_time": "Từ 2 đến 4 ngày làm việc thông qua đối tác vận chuyển GHN (Giao Hàng Nhanh) hoặc GHTK (Giao Hàng Tiết Kiệm).",
                "payment_methods": [
                    {"code": "COD", "name": "Thanh toán tiền mặt khi nhận hàng (COD)"},
                    {"code": "VNPAY", "name": "Thanh toán trực tuyến qua Cổng VNPay (Thẻ ATM/QR/Visa)"},
                ],
                "checkout_steps": [
                    "Bước 1: Chọn sách vào Giỏ hàng",
                    "Bước 2: Mở giỏ hàng và bấm Tiến hành Đặt hàng (Checkout)",
                    "Bước 3: Chọn địa chỉ giao hàng và phương thức thanh toán (COD hoặc VNPay)",
                    "Bước 4: Nhập mã giảm giá (nếu có) và nhấn Xác nhận đặt hàng",
                ],
            },
        }

    @classmethod
    def _tool_get_reading_recommendations_tool(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        limit = min(int(args.get("limit") or 4), 8)
        category_slug = args.get("category_slug")

        repo = RecommendationRepository(db)
        if current_user:
            signals = repo.get_user_signals(current_user.id)
            exclude_ids = signals.get("purchased_book_ids", set())
            candidates = repo.get_candidate_books(exclude_book_ids=exclude_ids, category_slug=category_slug, limit=limit)
            if not candidates:
                candidates = repo.get_popularity_baseline(limit=limit)
        else:
            candidates = repo.get_popularity_baseline(limit=limit)

        formatted = []
        for b in candidates:
            if b.authors:
                first_ba = b.authors[0]
                if hasattr(first_ba, "author") and first_ba.author and hasattr(first_ba.author, "name"):
                    primary_author = first_ba.author.name
                elif hasattr(first_ba, "name"):
                    primary_author = first_ba.name
                else:
                    primary_author = "Nhiều tác giả"
            else:
                primary_author = "Nhiều tác giả"
            available_stock = (b.inventory.physical_stock - b.inventory.reserved_stock) if b.inventory else 0
            cover_img = b.images[0].image_url if b.images else None
            formatted.append(
                {
                    "id": b.id,
                    "title": b.title,
                    "slug": b.slug,
                    "price": float(b.price),
                    "primary_author": primary_author,
                    "cover_image_url": cover_img,
                    "available_stock": available_stock,
                }
            )

        return {
            "success": True,
            "recommendations": formatted,
            "message": "Các tác phẩm tiêu biểu được gợi ý từ BookMatch AI tại Novelia Books.",
        }

    # --------------------------------------------------------------------------
    # Phase 10: Admin Copilot Tools
    # --------------------------------------------------------------------------

    @classmethod
    def _tool_get_sales_summary(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        """Aggregate sales revenue and order metrics via AdminDashboardRepository."""
        start_date_str = args.get("start_date")
        end_date_str = args.get("end_date")
        start_dt = None
        end_dt = None

        if start_date_str:
            try:
                start_dt = datetime.fromisoformat(str(start_date_str).replace("Z", "+00:00"))
            except Exception:
                pass
        if end_date_str:
            try:
                end_dt = datetime.fromisoformat(str(end_date_str).replace("Z", "+00:00"))
            except Exception:
                pass

        kpi = AdminDashboardRepository.get_kpi_summary(db, start_date=start_dt, end_date=end_dt)

        return {
            "success": True,
            "total_revenue": float(kpi.total_revenue),
            "collected_revenue": float(kpi.collected_revenue),
            "total_orders": kpi.total_orders,
            "valid_orders_count": kpi.valid_orders_count,
            "average_order_value": float(kpi.average_order_value),
            "total_customers": kpi.total_customers,
            "total_staff": kpi.total_staff,
            "active_coupons_count": kpi.active_coupons_count,
            "profit_note": kpi.profit_note,
        }

    @classmethod
    def _tool_get_inventory_summary(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        """Authoritative catalog and warehouse inventory metrics."""
        total_books = db.query(func.count(Book.id)).scalar() or 0
        total_physical = db.query(func.coalesce(func.sum(Inventory.physical_stock), 0)).scalar() or 0
        total_reserved = db.query(func.coalesce(func.sum(Inventory.reserved_stock), 0)).scalar() or 0

        low_stock_count = (
            db.query(func.count(Inventory.id))
            .filter(
                (Inventory.physical_stock - Inventory.reserved_stock)
                <= Inventory.low_stock_threshold
            )
            .scalar()
            or 0
        )
        out_of_stock_count = (
            db.query(func.count(Inventory.id))
            .filter((Inventory.physical_stock - Inventory.reserved_stock) <= 0)
            .scalar()
            or 0
        )

        return {
            "success": True,
            "total_books": total_books,
            "total_physical_stock": int(total_physical),
            "total_reserved_stock": int(total_reserved),
            "total_available_stock": int(total_physical - total_reserved),
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
        }

    @classmethod
    def _tool_find_low_stock_books(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        """List books running low or below safety threshold."""
        limit = min(int(args.get("limit") or 10), 50)
        alerts = AdminDashboardRepository.get_low_stock_alerts(db, limit=limit)

        return {
            "success": True,
            "count": len(alerts),
            "low_stock_books": [
                {
                    "book_id": item.book_id,
                    "title": item.title,
                    "isbn": item.isbn,
                    "sku": item.sku,
                    "physical_stock": item.physical_stock,
                    "reserved_stock": item.reserved_stock,
                    "available_stock": item.available_stock,
                    "low_stock_threshold": item.low_stock_threshold,
                }
                for item in alerts
            ],
        }

    @classmethod
    def _tool_search_orders(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        """Search store orders across all customers."""
        query = args.get("query")
        status_filter = args.get("status")
        limit = min(int(args.get("limit") or 5), 20)

        orders, total = OrderRepository.list_all_orders(
            db, page=1, page_size=limit, status=status_filter, query=query
        )

        formatted = []
        for o in orders:
            formatted.append(
                {
                    "order_code": o.order_code,
                    "customer_name": o.recipient_name,
                    "phone": o.recipient_phone,
                    "status": o.status,
                    "total_amount": float(o.total_amount),
                    "created_at": o.created_at.strftime("%d/%m/%Y %H:%M"),
                    "item_count": sum(it.quantity for it in o.items),
                    "carrier": o.shipment.carrier if getattr(o, "shipment", None) else None,
                }
            )

        return {
            "success": True,
            "total_matches": total,
            "returned_count": len(formatted),
            "orders": formatted,
        }

    @classmethod
    def _tool_search_books(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        """Search books in admin catalog."""
        query = args.get("query")
        category_slug = args.get("category_slug")
        limit = min(int(args.get("limit") or 5), 20)

        params = BookFilterParams(
            search=query,
            category_slug=category_slug,
            page=1,
            page_size=limit,
            sort_by="newest",
        )
        items, total = BookRepository.list_books(db, params)
        books = [to_book_list_read(b) for b in items]

        formatted = []
        for b in books:
            formatted.append(
                {
                    "id": b.id,
                    "title": b.title,
                    "slug": b.slug,
                    "isbn": b.isbn,
                    "sku": b.sku,
                    "price": float(b.price),
                    "original_price": float(b.original_price) if b.original_price else None,
                    "available_stock": b.stock_available,
                    "primary_author": b.primary_author,
                }
            )

        return {
            "success": True,
            "total_matches": total,
            "returned_count": len(formatted),
            "books": formatted,
        }

    @classmethod
    def _tool_prepare_book_update(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        """Stage a book price or metadata change with Two-Phase Confirmation preview."""
        book_id = args.get("book_id")
        if not book_id:
            return {"success": False, "message": "Vui lòng cung cấp mã ID của cuốn sách cần cập nhật."}

        book = BookRepository.get_by_id(db, int(book_id))
        if not book:
            return {"success": False, "message": f"Không tìm thấy sách với mã ID {book_id}."}

        new_price = args.get("new_price")
        if new_price is not None and float(new_price) <= 0:
            return {"success": False, "message": "Giá bán mới phải lớn hơn 0 VNĐ."}

        new_original_price = args.get("new_original_price")
        new_title = args.get("new_title")
        new_status = args.get("status")

        token = f"confirm_bk_{uuid.uuid4().hex[:12]}"
        preview = {
            "book_id": book.id,
            "current_title": book.title,
            "proposed_title": new_title if new_title else book.title,
            "current_price": float(book.price),
            "proposed_price": float(new_price) if new_price is not None else float(book.price),
            "current_original_price": float(book.original_price) if book.original_price else None,
            "proposed_original_price": (
                float(new_original_price)
                if new_original_price is not None
                else (float(book.original_price) if book.original_price else None)
            ),
            "current_status": book.status,
            "proposed_status": new_status if new_status else book.status,
        }

        # Persist pending audit log record
        user_roles = (
            UserRepository.get_user_role_names(current_user) if current_user else ["STAFF"]
        )
        action_log = AIActionLog(
            conversation_id=None,
            user_id=current_user.id if current_user else None,
            user_role=user_roles[0],
            tool_name="prepare_book_update",
            input_arguments=args,
            execution_status="CONFIRMATION_REQUIRED",
            confirmation_token=token,
            is_confirmed=False,
            output_summary=f"Staged book update preview: {preview}",
            created_at=datetime.now(timezone.utc),
        )
        db.add(action_log)
        db.commit()

        return {
            "success": True,
            "confirmation_required": True,
            "confirmation_token": token,
            "action_type": "UPDATE_BOOK",
            "book_id": book.id,
            "preview": preview,
            "message": (
                f"Đã lập bản xem trước cập nhật sách '{book.title}'. "
                f"Vui lòng nhấn Xác nhận để áp dụng lưu chính thức vào cơ sở dữ liệu."
            ),
        }

    @classmethod
    def _tool_draft_product_description(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        """Draft engaging marketing synopsis and selling points for a book."""
        book_id = args.get("book_id")
        if not book_id:
            return {"success": False, "message": "Vui lòng cung cấp mã ID của cuốn sách cần viết mô tả."}

        book = BookRepository.get_by_id(db, int(book_id))
        if not book:
            return {"success": False, "message": f"Không tìm thấy sách với mã ID {book_id}."}

        author_names = []
        for ba in (book.authors or []):
            if hasattr(ba, "author") and ba.author and hasattr(ba.author, "name"):
                author_names.append(ba.author.name)
            elif hasattr(ba, "name"):
                author_names.append(ba.name)
        authors = ", ".join(author_names) if author_names else "Tác giả Novelia"

        cat_names = []
        for bc in (book.categories or []):
            if hasattr(bc, "category") and bc.category and hasattr(bc.category, "name"):
                cat_names.append(bc.category.name)
            elif hasattr(bc, "name"):
                cat_names.append(bc.name)
        categories = ", ".join(cat_names) if cat_names else "Sách hay"

        draft = {
            "headline": f"Khám Phá Kiệt Tác '{book.title}' - Trải Nghiệm Văn Học Đỉnh Cao",
            "synopsis": (
                f"'{book.title}' của tác giả {authors} thuộc thể loại {categories}, "
                f"mang đến cho độc giả những góc nhìn sâu sắc và lôi cuốn qua từng trang sách. "
                + (f"Nội dung sách: {book.description[:200]}..." if book.description else "")
            ),
            "key_selling_points": [
                f"Tác phẩm xuất sắc của {authors} được đông đảo bạn đọc đánh giá cao.",
                f"Ấn bản cao cấp, định dạng {book.cover_type or 'bìa mềm'}, chuẩn {book.page_count or 300} trang.",
                f"Giá ưu đãi hấp dẫn chỉ {float(book.price):,.0f} đ tại Novelia Books.",
            ],
            "target_audience": f"Độc giả yêu thích thể loại {categories} và các tác phẩm của {authors}.",
            "call_to_action": f"Đặt mua ngay '{book.title}' hôm nay để nhận ưu đãi giao hàng nhanh toàn quốc!",
        }

        return {
            "success": True,
            "book_id": book.id,
            "book_title": book.title,
            "draft": draft,
            "message": f"Đã soạn thảo bản nháp mô tả sản phẩm cho cuốn sách '{book.title}'.",
        }

    @classmethod
    def _tool_draft_promotion(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        """Stage a promotional discount coupon with Two-Phase Confirmation preview."""
        code = str(args.get("code", "")).strip().upper()
        if not code:
            return {"success": False, "message": "Vui lòng cung cấp mã khuyến mãi (code)."}

        existing = CouponRepository.get_by_code(db, code)
        if existing:
            return {"success": False, "message": f"Mã khuyến mãi '{code}' đã tồn tại trong hệ thống."}

        discount_percent = int(args.get("discount_percent") or 10)
        if not (1 <= discount_percent <= 100):
            return {"success": False, "message": "Phần trăm giảm giá phải từ 1% đến 100%."}

        max_discount = float(args.get("max_discount_amount") or 50000)
        min_order = float(args.get("min_order_amount") or 100000)
        usage_limit = int(args.get("usage_limit") or 100)
        duration_days = int(args.get("duration_days") or 30)

        token = f"confirm_promo_{uuid.uuid4().hex[:12]}"
        preview = {
            "code": code,
            "discount_percent": discount_percent,
            "max_discount_amount": max_discount,
            "min_order_amount": min_order,
            "usage_limit": usage_limit,
            "duration_days": duration_days,
        }

        user_roles = (
            UserRepository.get_user_role_names(current_user) if current_user else ["STAFF"]
        )
        action_log = AIActionLog(
            conversation_id=None,
            user_id=current_user.id if current_user else None,
            user_role=user_roles[0],
            tool_name="draft_promotion",
            input_arguments=args,
            execution_status="CONFIRMATION_REQUIRED",
            confirmation_token=token,
            is_confirmed=False,
            output_summary=f"Staged promotion preview: {preview}",
            created_at=datetime.now(timezone.utc),
        )
        db.add(action_log)
        db.commit()

        return {
            "success": True,
            "confirmation_required": True,
            "confirmation_token": token,
            "action_type": "CREATE_COUPON",
            "preview": preview,
            "message": (
                f"Đã lập bản xem trước mã khuyến mãi '{code}' (Giảm {discount_percent}%, tối đa {max_discount:,.0f} đ). "
                f"Vui lòng nhấn Xác nhận để kích hoạt mã chính thức."
            ),
        }

    @classmethod
    def _tool_prepare_inventory_adjustment(
        cls, db: Session, args: Dict[str, Any], current_user: Optional[User]
    ) -> Dict[str, Any]:
        """Stage physical warehouse stock adjustment with Two-Phase Confirmation preview."""
        book_id = args.get("book_id")
        delta = int(args.get("delta") or 0)
        reason = str(args.get("reason", "")).strip()

        if not book_id:
            return {"success": False, "message": "Vui lòng cung cấp mã ID cuốn sách cần điều chỉnh tồn kho."}
        if delta == 0:
            return {"success": False, "message": "Số lượng điều chỉnh (delta) phải khác 0."}
        if not reason:
            return {"success": False, "message": "Vui lòng cung cấp lý do điều chỉnh tồn kho."}

        inventory = InventoryRepository.get_by_book_id(db, int(book_id))
        if not inventory:
            return {"success": False, "message": f"Không tìm thấy bản ghi tồn kho cho sách ID {book_id}."}

        book = inventory.book
        physical = inventory.physical_stock
        reserved = inventory.reserved_stock
        proposed_physical = physical + delta

        if proposed_physical < 0:
            return {
                "success": False,
                "message": f"Số lượng tồn kho vật lý sau điều chỉnh ({proposed_physical}) không thể âm.",
            }
        if proposed_physical < reserved:
            return {
                "success": False,
                "message": (
                    f"Tồn kho sau điều chỉnh ({proposed_physical}) không thể nhỏ hơn "
                    f"tồn kho đang giữ chỗ cho các đơn hàng ({reserved})."
                ),
            }

        token = f"confirm_inv_{uuid.uuid4().hex[:12]}"
        preview = {
            "book_id": inventory.book_id,
            "book_title": book.title if book else f"Book #{inventory.book_id}",
            "current_physical_stock": physical,
            "delta": delta,
            "proposed_physical_stock": proposed_physical,
            "reserved_stock": reserved,
            "current_available_stock": physical - reserved,
            "proposed_available_stock": proposed_physical - reserved,
            "reason": reason,
        }

        user_roles = (
            UserRepository.get_user_role_names(current_user) if current_user else ["STAFF"]
        )
        action_log = AIActionLog(
            conversation_id=None,
            user_id=current_user.id if current_user else None,
            user_role=user_roles[0],
            tool_name="prepare_inventory_adjustment",
            input_arguments=args,
            execution_status="CONFIRMATION_REQUIRED",
            confirmation_token=token,
            is_confirmed=False,
            output_summary=f"Staged inventory adjustment preview: {preview}",
            created_at=datetime.now(timezone.utc),
        )
        db.add(action_log)
        db.commit()

        return {
            "success": True,
            "confirmation_required": True,
            "confirmation_token": token,
            "action_type": "ADJUST_INVENTORY",
            "book_id": inventory.book_id,
            "preview": preview,
            "message": (
                f"Đã lập bản xem trước điều chỉnh tồn kho sách '{book.title if book else ''}' "
                f"({delta:+d} cuốn). Vui lòng nhấn Xác nhận để lưu cập nhật số liệu kho thực tế."
            ),
        }

    # --------------------------------------------------------------------------
    # Backward compatibility aliases
    # --------------------------------------------------------------------------
    _tool_draft_book_metadata_tool = _tool_draft_product_description
    _tool_draft_promotion_campaign_tool = _tool_draft_promotion
    _tool_query_business_metrics_tool = _tool_get_sales_summary

    # --------------------------------------------------------------------------
    # Two-Phase Confirmation Executor with Precondition Re-Verification
    # --------------------------------------------------------------------------

    @classmethod
    def execute_confirmation(
        cls,
        db: Session,
        confirmation_token: str,
        staff_user: User,
    ) -> Dict[str, Any]:
        """Execute confirmed mutating AI action after re-validating preconditions right before commit."""
        action_log = (
            db.query(AIActionLog)
            .filter(AIActionLog.confirmation_token == confirmation_token)
            .first()
        )
        if not action_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mã xác nhận không tồn tại hoặc đã hết hạn.",
            )

        if action_log.is_confirmed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thao tác này đã được xác nhận và thực thi trước đó.",
            )

        tool_name = action_log.tool_name
        raw_args = action_log.input_arguments or {}

        # 1. Adjust Inventory Confirmation
        if tool_name == "prepare_inventory_adjustment":
            book_id = raw_args.get("book_id")
            delta = int(raw_args.get("delta", 0))
            reason = str(raw_args.get("reason", "Điều chỉnh qua AI Admin Copilot"))

            # Re-check inventory conditions immediately prior to commit
            inv = InventoryRepository.get_by_book_id(db, int(book_id))
            if not inv:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sách ID {book_id} không còn tồn tại trong kho.",
                )
            if inv.physical_stock + delta < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tồn kho vật lý sau điều chỉnh không thể âm.",
                )
            if inv.physical_stock + delta < inv.reserved_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Tồn kho sau điều chỉnh ({inv.physical_stock + delta}) nhỏ hơn "
                        f"tồn kho giữ chỗ hiện tại ({inv.reserved_stock})."
                    ),
                )

            updated_inv = InventoryRepository.adjust_stock(
                db=db,
                book_id=int(book_id),
                delta=delta,
                reference_code=f"AI-CONFIRM-{confirmation_token[:8]}",
                reason=reason,
                staff_user_id=staff_user.id,
            )

            action_log.is_confirmed = True
            action_log.execution_status = "SUCCESS"
            action_log.output_summary = (
                f"Đã điều chỉnh tồn kho sách ID {book_id}: {delta:+d} cuốn. "
                f"Tồn kho mới: {updated_inv.physical_stock}"
            )
            db.commit()

            return {
                "success": True,
                "action_type": "ADJUST_INVENTORY",
                "message": f"Đã thực thi điều chỉnh tồn kho thành công ({delta:+d} cuốn).",
                "details": {
                    "book_id": updated_inv.book_id,
                    "physical_stock": updated_inv.physical_stock,
                    "reserved_stock": updated_inv.reserved_stock,
                    "available_stock": updated_inv.available_stock,
                },
                "executed_at": datetime.now(timezone.utc),
            }

        # 2. Book Update Confirmation
        elif tool_name == "prepare_book_update":
            book_id = raw_args.get("book_id")
            book = BookRepository.get_by_id(db, int(book_id))
            if not book:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Không tìm thấy sách với ID {book_id} để cập nhật.",
                )

            new_price = raw_args.get("new_price")
            new_original_price = raw_args.get("new_original_price")
            new_title = raw_args.get("new_title")
            new_status = raw_args.get("status")

            update_payload = {}
            if new_price is not None:
                if float(new_price) <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Giá bán mới phải lớn hơn 0 VNĐ.",
                    )
                update_payload["price"] = Decimal(str(new_price))
            if new_original_price is not None:
                update_payload["original_price"] = Decimal(str(new_original_price))
            if new_title:
                update_payload["title"] = new_title
            if new_status:
                update_payload["status"] = new_status

            updated_book = BookRepository.update_book(
                db=db,
                book=book,
                data=BookUpdate(**update_payload),
            )

            action_log.is_confirmed = True
            action_log.execution_status = "SUCCESS"
            action_log.output_summary = f"Đã cập nhật sách ID {book_id}: {update_payload}"
            db.commit()

            return {
                "success": True,
                "action_type": "UPDATE_BOOK",
                "message": f"Đã cập nhật thông tin sách '{updated_book.title}' thành công.",
                "details": {
                    "book_id": updated_book.id,
                    "title": updated_book.title,
                    "price": float(updated_book.price),
                    "original_price": float(updated_book.original_price) if updated_book.original_price else None,
                    "status": updated_book.status,
                },
                "executed_at": datetime.now(timezone.utc),
            }

        # 3. Create Promotion Confirmation
        elif tool_name in ["draft_promotion", "draft_promotion_campaign_tool"]:
            code = str(raw_args.get("code", "")).strip().upper()
            existing = CouponRepository.get_by_code(db, code)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mã khuyến mãi '{code}' đã tồn tại trong hệ thống.",
                )

            discount_percent = int(raw_args.get("discount_percent", 10))
            max_discount = Decimal(str(raw_args.get("max_discount_amount", 50000)))
            min_order = Decimal(str(raw_args.get("min_order_amount", 100000)))
            usage_limit = int(raw_args.get("usage_limit", 100))
            duration_days = int(raw_args.get("duration_days", 30))

            start_date = datetime.now(timezone.utc)
            end_date = start_date + timedelta(days=duration_days)

            coupon = Coupon(
                code=code,
                description=f"Khuyến mãi {discount_percent}% tạo qua AI Admin Copilot",
                discount_type="PERCENTAGE",
                discount_value=Decimal(str(discount_percent)),
                max_discount_amount=max_discount,
                min_order_amount=min_order,
                usage_limit=usage_limit,
                used_count=0,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )
            db.add(coupon)
            db.commit()
            db.refresh(coupon)

            action_log.is_confirmed = True
            action_log.execution_status = "SUCCESS"
            action_log.output_summary = f"Đã tạo và kích hoạt coupon {code} (Giảm {discount_percent}%)"
            db.commit()

            return {
                "success": True,
                "action_type": "CREATE_COUPON",
                "message": f"Đã tạo và kích hoạt mã khuyến mãi '{code}' thành công.",
                "details": {
                    "coupon_id": coupon.id,
                    "code": coupon.code,
                    "discount_percent": discount_percent,
                    "max_discount_amount": float(max_discount),
                    "min_order_amount": float(min_order),
                    "is_active": coupon.is_active,
                },
                "executed_at": datetime.now(timezone.utc),
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không hỗ trợ xác nhận cho công cụ '{tool_name}'.",
            )

