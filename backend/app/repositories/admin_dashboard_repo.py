"""Data access repository for Phase 7 Admin Dashboard, KPIs, and Governance."""

from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func, distinct, desc, asc, or_, and_, case
from sqlalchemy.orm import Session, selectinload

from app.models.catalog import Book, Category, Author, Publisher, BookAuthor, BookCategory
from app.models.inventory import Inventory, InventoryTransaction
from app.models.commerce import Order, OrderItem, Coupon, CouponUsage
from app.models.payment_shipping import Payment
from app.models.user import User, Role, UserRole
from app.schemas.admin_dashboard import (
    DashboardKpiSummary,
    RevenueTimelinePoint,
    OrderStatusCount,
    TopSellingBook,
    LowStockAlertItem,
    RecentActivityItem,
)


class AdminDashboardRepository:
    """SQLAlchemy query layer executing real MySQL aggregations for the Admin Dashboard."""

    @classmethod
    def get_kpi_summary(
        cls,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> DashboardKpiSummary:
        """Calculate authoritative KPIs directly from MySQL transactions."""
        # 1. Base query for orders
        order_q = db.query(Order)
        if start_date:
            order_q = order_q.filter(Order.created_at >= start_date)
        if end_date:
            order_q = order_q.filter(Order.created_at <= end_date)

        all_orders = order_q.all()
        total_orders = len(all_orders)

        # 2. Total Gross Revenue (from non-cancelled orders)
        valid_orders = [o for o in all_orders if o.status != "CANCELLED"]
        valid_orders_count = len(valid_orders)
        total_revenue = sum((Decimal(str(o.total_amount)) for o in valid_orders), Decimal("0.00"))

        # 3. Collected Revenue (Cash Inflow from PAID payments)
        payment_q = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.payment_status == "PAID"
        )
        if start_date:
            payment_q = payment_q.filter(Payment.updated_at >= start_date)
        if end_date:
            payment_q = payment_q.filter(Payment.updated_at <= end_date)

        collected_raw = payment_q.scalar()
        collected_revenue = Decimal(str(collected_raw)).quantize(Decimal("0.01"))

        # 4. Average Order Value (AOV)
        if valid_orders_count > 0:
            average_order_value = (total_revenue / Decimal(str(valid_orders_count))).quantize(
                Decimal("0.01")
            )
        else:
            average_order_value = Decimal("0.00")

        # 5. Catalog & Inventory Metrics
        total_books = db.query(func.count(Book.id)).scalar() or 0

        low_stock_count = (
            db.query(func.count(Inventory.id))
            .filter(
                (Inventory.physical_stock - Inventory.reserved_stock)
                <= Inventory.low_stock_threshold
            )
            .scalar()
            or 0
        )

        # 6. User Metrics
        # Distinct customer count
        total_customers = (
            db.query(func.count(distinct(UserRole.user_id)))
            .join(Role, Role.id == UserRole.role_id)
            .filter(Role.name == "CUSTOMER")
            .scalar()
            or 0
        )

        # Staff & Admin count
        total_staff = (
            db.query(func.count(distinct(UserRole.user_id)))
            .join(Role, Role.id == UserRole.role_id)
            .filter(Role.name.in_(["STAFF", "ADMIN"]))
            .scalar()
            or 0
        )

        # Active Coupons Count
        now_utc = datetime.now(timezone.utc)
        active_coupons_count = (
            db.query(func.count(Coupon.id))
            .filter(
                Coupon.is_active == True,
                Coupon.end_date >= now_utc,
            )
            .scalar()
            or 0
        )

        return DashboardKpiSummary(
            total_revenue=total_revenue.quantize(Decimal("0.01")),
            collected_revenue=collected_revenue,
            has_cost_data=False,
            profit_note="Chưa có dữ liệu giá vốn nhập kho (COGS) để tính toán lợi nhuận ròng thực tế.",
            total_orders=total_orders,
            valid_orders_count=valid_orders_count,
            average_order_value=average_order_value,
            total_books=total_books,
            low_stock_count=low_stock_count,
            total_customers=total_customers,
            total_staff=total_staff,
            active_coupons_count=active_coupons_count,
        )

    @classmethod
    def get_revenue_timeline(
        cls,
        db: Session,
        period: str = "30days",
    ) -> List[RevenueTimelinePoint]:
        """Aggregate revenue and collected cash by day or month."""
        now = datetime.now(timezone.utc)

        if period == "7days":
            days = 7
            start_date = now - timedelta(days=6)
            is_monthly = False
        elif period == "90days":
            days = 90
            start_date = now - timedelta(days=89)
            is_monthly = False
        elif period == "12months":
            days = 365
            start_date = now - timedelta(days=365)
            is_monthly = True
        else:  # default 30days
            days = 30
            start_date = now - timedelta(days=29)
            is_monthly = False

        # Query all relevant orders in window
        orders = (
            db.query(Order)
            .filter(Order.created_at >= start_date)
            .options(selectinload(Order.payment))
            .order_by(Order.created_at.asc())
            .all()
        )

        # Bucket map
        buckets: Dict[str, Dict[str, Any]] = {}

        if is_monthly:
            # 12 monthly buckets
            curr = start_date
            while curr <= now:
                label = curr.strftime("%Y-%m")
                buckets[label] = {"revenue": Decimal("0.00"), "collected_cash": Decimal("0.00"), "order_count": 0}
                # Advance 1 month
                year = curr.year + (1 if curr.month == 12 else 0)
                month = 1 if curr.month == 12 else curr.month + 1
                curr = curr.replace(year=year, month=month, day=1)
        else:
            # Daily buckets
            curr = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            target_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            while curr <= target_end:
                label = curr.strftime("%Y-%m-%d")
                buckets[label] = {"revenue": Decimal("0.00"), "collected_cash": Decimal("0.00"), "order_count": 0}
                curr += timedelta(days=1)

        for o in orders:
            if is_monthly:
                label = o.created_at.strftime("%Y-%m")
            else:
                label = o.created_at.strftime("%Y-%m-%d")

            if label in buckets:
                buckets[label]["order_count"] += 1
                if o.status != "CANCELLED":
                    buckets[label]["revenue"] += Decimal(str(o.total_amount))
                if o.payment and o.payment.payment_status == "PAID":
                    buckets[label]["collected_cash"] += Decimal(str(o.payment.amount))

        result = [
            RevenueTimelinePoint(
                date_label=lbl,
                revenue=data["revenue"].quantize(Decimal("0.01")),
                collected_cash=data["collected_cash"].quantize(Decimal("0.01")),
                order_count=data["order_count"],
            )
            for lbl, data in buckets.items()
        ]
        return result

    @classmethod
    def get_orders_by_status(
        cls,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[OrderStatusCount]:
        """Distribution of orders across status lifecycle."""
        q = db.query(Order.status, func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0))
        if start_date:
            q = q.filter(Order.created_at >= start_date)
        if end_date:
            q = q.filter(Order.created_at <= end_date)

        rows = q.group_by(Order.status).all()

        status_labels = {
            "PENDING": "Chờ xử lý",
            "CONFIRMED": "Đã xác nhận",
            "PROCESSING": "Đang đóng gói",
            "SHIPPING": "Đang vận chuyển",
            "COMPLETED": "Giao thành công",
            "CANCELLED": "Đã hủy",
        }

        total_orders = sum((r[1] for r in rows), 0)

        # Standard lifecycle order list
        lifecycle_order = ["PENDING", "CONFIRMED", "PROCESSING", "SHIPPING", "COMPLETED", "CANCELLED"]
        row_dict = {r[0]: (r[1], Decimal(str(r[2]))) for r in rows}

        results = []
        for st in lifecycle_order:
            count, amount = row_dict.get(st, (0, Decimal("0.00")))
            percentage = round((count / total_orders * 100), 1) if total_orders > 0 else 0.0
            results.append(
                OrderStatusCount(
                    status=st,
                    label=status_labels.get(st, st),
                    count=count,
                    percentage=percentage,
                    total_amount=amount.quantize(Decimal("0.01")),
                )
            )

        return results

    @classmethod
    def get_top_selling_books(
        cls,
        db: Session,
        limit: int = 5,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TopSellingBook]:
        """Identify best-selling books aggregated by purchase quantities in valid orders."""
        q = (
            db.query(
                OrderItem.book_id,
                OrderItem.book_title_snapshot,
                OrderItem.book_isbn_snapshot,
                func.sum(OrderItem.quantity).label("total_sold"),
                func.sum(OrderItem.subtotal).label("total_rev"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status != "CANCELLED")
        )

        if start_date:
            q = q.filter(Order.created_at >= start_date)
        if end_date:
            q = q.filter(Order.created_at <= end_date)

        rows = (
            q.group_by(OrderItem.book_id, OrderItem.book_title_snapshot, OrderItem.book_isbn_snapshot)
            .order_by(desc("total_sold"))
            .limit(limit)
            .all()
        )

        results = []
        for r in rows:
            book_id = r[0]
            title = r[1]
            isbn = r[2]
            total_sold = int(r[3] or 0)
            total_rev = Decimal(str(r[4] or 0)).quantize(Decimal("0.01"))

            # Fetch cover image url, sku, current stock if book exists
            cover_url = None
            book_sku = None
            current_stock = 0
            if book_id:
                book_obj = (
                    db.query(Book)
                    .options(selectinload(Book.inventory))
                    .filter(Book.id == book_id)
                    .first()
                )
                if book_obj:
                    cover_url = book_obj.cover_image_url
                    book_sku = book_obj.sku or f"NOV-BK-{book_id:04d}"
                    if book_obj.inventory:
                        current_stock = book_obj.inventory.available_stock

            results.append(
                TopSellingBook(
                    book_id=book_id or 0,
                    title=title,
                    isbn=isbn,
                    sku=book_sku,
                    cover_image_url=cover_url,
                    total_quantity_sold=total_sold,
                    units_sold=total_sold,
                    total_revenue=total_rev,
                    total_sales=total_rev,
                    current_stock=current_stock,
                )
            )

        return results

    @classmethod
    def get_low_stock_alerts(
        cls,
        db: Session,
        limit: int = 10,
    ) -> List[LowStockAlertItem]:
        """Retrieve titles that have reached or dropped below low stock thresholds."""
        inventories = (
            db.query(Inventory)
            .join(Book, Book.id == Inventory.book_id)
            .options(selectinload(Inventory.book))
            .filter(
                (Inventory.physical_stock - Inventory.reserved_stock)
                <= Inventory.low_stock_threshold
            )
            .order_by(asc(Inventory.physical_stock - Inventory.reserved_stock))
            .limit(limit)
            .all()
        )

        results = []
        for inv in inventories:
            b = inv.book
            avail = inv.physical_stock - inv.reserved_stock
            results.append(
                LowStockAlertItem(
                    book_id=inv.book_id,
                    title=b.title if b else f"Book #{inv.book_id}",
                    isbn=b.isbn if b else "",
                    sku=b.sku if b else "",
                    physical_stock=inv.physical_stock,
                    reserved_stock=inv.reserved_stock,
                    available_stock=avail,
                    low_stock_threshold=inv.low_stock_threshold,
                )
            )

        return results

    @classmethod
    def get_recent_activities(
        cls,
        db: Session,
        limit: int = 15,
    ) -> List[RecentActivityItem]:
        """Aggregate chronological feed of orders and inventory transactions."""
        activities: List[RecentActivityItem] = []

        # 1. Recent Orders
        recent_orders = (
            db.query(Order)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .all()
        )
        for o in recent_orders:
            severity = (
                "success" if o.status == "COMPLETED"
                else ("danger" if o.status == "CANCELLED" else "info")
            )
            activities.append(
                RecentActivityItem(
                    id=f"order-{o.id}",
                    activity_type="ORDER",
                    title=f"Đơn hàng mới {o.order_code}",
                    description=f"{o.recipient_name} đặt mua đơn trị giá {o.total_amount:,.0f} VND ({o.status})",
                    created_at=o.created_at,
                    timestamp=o.created_at,
                    badge_type="order",
                    severity=severity,
                )
            )

        # 2. Recent Inventory Transactions
        recent_inv_tx = (
            db.query(InventoryTransaction)
            .options(selectinload(InventoryTransaction.inventory).selectinload(Inventory.book))
            .order_by(InventoryTransaction.created_at.desc())
            .limit(limit)
            .all()
        )
        for tx in recent_inv_tx:
            b_title = ""
            if tx.inventory and tx.inventory.book:
                b_title = tx.inventory.book.title
            activities.append(
                RecentActivityItem(
                    id=f"inv-{tx.id}",
                    activity_type="INVENTORY",
                    title=f"Biến động kho: {tx.transaction_type}",
                    description=f"Sách: '{b_title}' thay đổi {tx.quantity_change:+d} cuốn ({tx.notes or ''})",
                    created_at=tx.created_at,
                    timestamp=tx.created_at,
                    badge_type="inventory",
                    severity="warning" if tx.quantity_change < 0 else "info",
                )
            )

        # Sort combined feed descending by timestamp
        activities.sort(key=lambda a: a.created_at, reverse=True)
        return activities[:limit]


    # =========================================================================
    # ENTITY MANAGEMENT: CATEGORIES, AUTHORS, PUBLISHERS
    # =========================================================================

    @staticmethod
    def list_categories_with_count(db: Session) -> List[Category]:
        return (
            db.query(Category)
            .options(selectinload(Category.book_categories))
            .order_by(Category.display_order.asc(), Category.name.asc())
            .all()
        )

    @staticmethod
    def list_authors_with_count(db: Session) -> List[Author]:
        return (
            db.query(Author)
            .options(selectinload(Author.book_authors))
            .order_by(Author.name.asc())
            .all()
        )

    @staticmethod
    def list_publishers_with_count(db: Session) -> List[Publisher]:
        return (
            db.query(Publisher)
            .options(selectinload(Publisher.books))
            .order_by(Publisher.name.asc())
            .all()
        )

    # =========================================================================
    # USER MANAGEMENT: CUSTOMERS & STAFF (ADMIN ROLE REQUIRED)
    # =========================================================================

    @staticmethod
    def list_users(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Tuple[List[User], int]:
        q = (
            db.query(User)
            .options(
                selectinload(User.roles).selectinload(UserRole.role),
            )
        )

        if role and role.strip() and role.strip().upper() != "ALL":
            target_role = role.strip().upper()
            q = q.join(User.roles).join(UserRole.role).filter(Role.name == target_role)

        if query and query.strip():
            term = f"%{query.strip()}%"
            q = q.filter(
                or_(
                    User.email.ilike(term),
                    User.full_name.ilike(term),
                    User.phone.ilike(term),
                )
            )

        total = q.count()
        offset = (page - 1) * page_size
        users = q.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
        return users, total

    @staticmethod
    def update_user_status(db: Session, user_id: int, is_active: bool) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        user.is_active = is_active
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user_roles(db: Session, user_id: int, role_names: List[str]) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Clean existing roles
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()

        # Add new roles
        for r_name in role_names:
            role = db.query(Role).filter(Role.name == r_name.strip().upper()).first()
            if role:
                ur = UserRole(user_id=user.id, role_id=role.id)
                db.add(ur)

        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    # =========================================================================
    # COUPONS / PROMOTIONS MANAGEMENT
    # =========================================================================

    @staticmethod
    def list_all_coupons(db: Session) -> List[Coupon]:
        return (
            db.query(Coupon)
            .options(selectinload(Coupon.usages))
            .order_by(Coupon.created_at.desc())
            .all()
        )

    @staticmethod
    def toggle_coupon(db: Session, coupon_id: int) -> Optional[Coupon]:
        c = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not c:
            return None
        c.is_active = not c.is_active
        db.commit()
        db.refresh(c)
        return c
