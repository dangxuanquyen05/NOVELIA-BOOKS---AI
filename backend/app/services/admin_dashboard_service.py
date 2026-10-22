"""Business logic service for Phase 7 Admin Dashboard, KPIs, and Governance."""

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.catalog import Book, Category, Author, Publisher, BookCategory
from app.models.commerce import Coupon, CouponUsage, Order
from app.models.user import User, Role, UserRole
from app.repositories.admin_dashboard_repo import AdminDashboardRepository
from app.repositories.user_repo import UserRepository
from app.schemas.admin_dashboard import (
    AdminAuthorCreateRequest,
    AdminAuthorResponse,
    AdminCategoryCreateRequest,
    AdminCategoryResponse,
    AdminCategoryUpdateRequest,
    AdminCouponCreateRequest,
    AdminCouponItem,
    AdminDashboardSummaryResponse,
    AdminPublisherCreateRequest,
    AdminPublisherResponse,
    AdminUserItem,
    AdminUserListResponse,
)


def slugify(text: str) -> str:
    """Generate clean URL slug from Vietnamese or Unicode string."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


class AdminDashboardService:
    """Service orchestrating analytics aggregation and administrative entity mutations."""

    @classmethod
    def get_dashboard_summary(
        cls,
        db: Session,
        period: str = "30days",
    ) -> AdminDashboardSummaryResponse:
        """Aggregate executive KPIs, trends, order distributions, and recent activities."""
        now = datetime.now(timezone.utc)
        clean_period = period.strip().lower()

        if clean_period == "7days":
            start_date = now - timedelta(days=7)
        elif clean_period == "30days":
            start_date = now - timedelta(days=30)
        elif clean_period == "90days":
            start_date = now - timedelta(days=90)
        elif clean_period == "12months":
            start_date = now - timedelta(days=365)
        else:
            clean_period = "all"
            start_date = None

        # Fetch KPIs
        kpis = AdminDashboardRepository.get_kpi_summary(db, start_date=start_date, end_date=now)

        # Fetch Timeline series
        timeline = AdminDashboardRepository.get_revenue_timeline(db, period=clean_period)

        # Status breakdown
        status_breakdown = AdminDashboardRepository.get_orders_by_status(
            db, start_date=start_date, end_date=now
        )

        # Top selling books
        top_selling = AdminDashboardRepository.get_top_selling_books(
            db, limit=5, start_date=start_date, end_date=now
        )

        # Low stock warnings
        low_stock = AdminDashboardRepository.get_low_stock_alerts(db, limit=10)

        # Recent activities
        recent_activities = AdminDashboardRepository.get_recent_activities(db, limit=15)

        return AdminDashboardSummaryResponse(
            kpis=kpis,
            timeline=timeline,
            status_breakdown=status_breakdown,
            top_selling_books=top_selling,
            low_stock_alerts=low_stock,
            recent_activities=recent_activities,
            filter_period=clean_period,
        )

    # =========================================================================
    # CATEGORIES MANAGEMENT
    # =========================================================================

    @classmethod
    def list_categories(cls, db: Session) -> List[AdminCategoryResponse]:
        categories = AdminDashboardRepository.list_categories_with_count(db)
        results = []
        for c in categories:
            results.append(
                AdminCategoryResponse(
                    id=c.id,
                    name=c.name,
                    slug=c.slug,
                    description=c.description,
                    parent_id=c.parent_id,
                    display_order=c.display_order,
                    books_count=len(c.book_categories) if c.book_categories else 0,
                    created_at=c.created_at,
                )
            )
        return results

    @classmethod
    def create_category(cls, db: Session, data: AdminCategoryCreateRequest) -> AdminCategoryResponse:
        slug = data.slug.strip().lower() if data.slug else slugify(data.name)
        existing = db.query(Category).filter((Category.name == data.name) | (Category.slug == slug)).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Danh mục có tên '{data.name}' hoặc slug '{slug}' đã tồn tại.",
            )

        if data.parent_id:
            parent = db.query(Category).filter(Category.id == data.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Danh mục cha ID {data.parent_id} không tồn tại.",
                )

        cat = Category(
            name=data.name.strip(),
            slug=slug,
            description=data.description.strip() if data.description else None,
            parent_id=data.parent_id,
            display_order=data.display_order,
            created_at=datetime.now(timezone.utc),
        )
        db.add(cat)
        db.commit()
        cat_id = cat.id if cat.id is not None else 1
        return AdminCategoryResponse(
            id=cat_id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            parent_id=cat.parent_id,
            display_order=cat.display_order,
            books_count=0,
            created_at=cat.created_at,
        )

    @classmethod
    def update_category(cls, db: Session, cat_id: int, data: AdminCategoryUpdateRequest) -> AdminCategoryResponse:
        cat = db.query(Category).filter(Category.id == cat_id).first()
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy danh mục ID {cat_id}.")

        if data.name is not None:
            cat.name = data.name.strip()
        if data.slug is not None:
            cat.slug = data.slug.strip().lower()
        if data.description is not None:
            cat.description = data.description.strip()
        if data.parent_id is not None:
            if data.parent_id == cat.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Danh mục không thể làm cha của chính nó.")
            cat.parent_id = data.parent_id
        if data.display_order is not None:
            cat.display_order = data.display_order

        db.commit()
        db.refresh(cat)
        return AdminCategoryResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            parent_id=cat.parent_id,
            display_order=cat.display_order,
            books_count=len(cat.book_categories) if cat.book_categories else 0,
            created_at=cat.created_at,
        )

    @classmethod
    def delete_category(cls, db: Session, cat_id: int) -> dict:
        cat = db.query(Category).filter(Category.id == cat_id).first()
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy danh mục ID {cat_id}.")

        # Check if books are attached
        books_count = db.query(BookCategory).filter(BookCategory.category_id == cat.id).count()
        if books_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể xóa danh mục '{cat.name}' vì đang liên kết với {books_count} đầu sách.",
            )

        db.delete(cat)
        db.commit()
        return {"message": f"Đã xóa thành công danh mục '{cat.name}'."}

    # =========================================================================
    # AUTHORS & PUBLISHERS MANAGEMENT
    # =========================================================================

    @classmethod
    def list_authors(cls, db: Session) -> List[AdminAuthorResponse]:
        authors = AdminDashboardRepository.list_authors_with_count(db)
        return [
            AdminAuthorResponse(
                id=a.id,
                name=a.name,
                slug=a.slug,
                bio=a.bio,
                avatar_url=a.avatar_url,
                birth_year=a.birth_year,
                nationality=a.nationality,
                books_count=len(a.book_authors) if a.book_authors else 0,
                created_at=a.created_at,
            )
            for a in authors
        ]

    @classmethod
    def create_author(cls, db: Session, data: AdminAuthorCreateRequest) -> AdminAuthorResponse:
        slug = data.slug.strip().lower() if data.slug else slugify(data.name)
        existing = db.query(Author).filter(Author.slug == slug).first()
        if existing:
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"

        author = Author(
            name=data.name.strip(),
            slug=slug,
            bio=data.bio.strip() if data.bio else None,
            avatar_url=data.avatar_url.strip() if data.avatar_url else None,
            birth_year=data.birth_year,
            nationality=data.nationality.strip() if data.nationality else None,
            created_at=datetime.now(timezone.utc),
        )
        db.add(author)
        db.commit()
        author_id = author.id if author.id is not None else 1
        return AdminAuthorResponse(
            id=author_id,
            name=author.name,
            slug=author.slug,
            bio=author.bio,
            avatar_url=author.avatar_url,
            birth_year=author.birth_year,
            nationality=author.nationality,
            books_count=0,
            created_at=author.created_at,
        )

    @classmethod
    def list_publishers(cls, db: Session) -> List[AdminPublisherResponse]:
        publishers = AdminDashboardRepository.list_publishers_with_count(db)
        return [
            AdminPublisherResponse(
                id=p.id,
                name=p.name,
                slug=p.slug,
                contact_info=p.contact_info,
                address=p.address,
                website=p.website,
                books_count=len(p.books) if p.books else 0,
                created_at=p.created_at,
            )
            for p in publishers
        ]

    @classmethod
    def create_publisher(cls, db: Session, data: AdminPublisherCreateRequest) -> AdminPublisherResponse:
        slug = data.slug.strip().lower() if data.slug else slugify(data.name)
        existing = db.query(Publisher).filter(Publisher.name == data.name.strip()).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Nhà xuất bản '{data.name}' đã tồn tại.")

        pub = Publisher(
            name=data.name.strip(),
            slug=slug,
            contact_info=data.contact_info.strip() if data.contact_info else None,
            address=data.address.strip() if data.address else None,
            website=data.website.strip() if data.website else None,
            created_at=datetime.now(timezone.utc),
        )
        db.add(pub)
        db.commit()
        pub_id = pub.id if pub.id is not None else 1
        return AdminPublisherResponse(
            id=pub_id,
            name=pub.name,
            slug=pub.slug,
            contact_info=pub.contact_info,
            address=pub.address,
            website=pub.website,
            books_count=0,
            created_at=pub.created_at,
        )

    # =========================================================================
    # USERS GOVERNANCE: CUSTOMERS & STAFF (ADMIN ROLE REQUIRED)
    # =========================================================================

    @classmethod
    def list_users(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        query: Optional[str] = None,
    ) -> AdminUserListResponse:
        users, total = AdminDashboardRepository.list_users(
            db, page=page, page_size=page_size, role=role, query=query
        )

        items = []
        for u in users:
            roles = [ur.role.name for ur in u.roles if ur.role]

            # Compute orders count and total spent
            order_stats = (
                db.query(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0))
                .filter(Order.user_id == u.id, Order.status != "CANCELLED")
                .first()
            )
            ord_count = order_stats[0] if order_stats else 0
            total_spent = Decimal(str(order_stats[1] if order_stats else 0)).quantize(Decimal("0.01"))

            items.append(
                AdminUserItem(
                    id=u.id,
                    email=u.email,
                    full_name=u.full_name,
                    phone=u.phone,
                    is_active=u.is_active,
                    roles=roles,
                    orders_count=ord_count,
                    total_spent=total_spent,
                    created_at=u.created_at,
                )
            )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return AdminUserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    def set_user_status(cls, db: Session, current_admin: User, user_id: int, is_active: bool) -> AdminUserItem:
        if current_admin.id == user_id and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản Quản trị viên không thể tự vô hiệu hóa chính mình.",
            )

        user = AdminDashboardRepository.update_user_status(db, user_id, is_active)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy người dùng ID {user_id}.")

        # Audit log for user active status change
        try:
            from app.repositories.audit_repo import AuditRepository
            AuditRepository.record_audit(
                db=db,
                action="USER_STATUS_CHANGE",
                entity_type="USER",
                entity_id=str(user.id),
                user_id=current_admin.id,
                new_values={"is_active": is_active, "email": user.email},
            )
        except Exception:
            pass

        roles = [ur.role.name for ur in user.roles if ur.role]
        return AdminUserItem(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            roles=roles,
            orders_count=0,
            total_spent=Decimal("0.00"),
            created_at=user.created_at,
        )

    @classmethod
    def set_user_roles(cls, db: Session, current_admin: User, user_id: int, roles: List[str]) -> AdminUserItem:
        valid_roles = ["CUSTOMER", "STAFF", "ADMIN"]
        for r in roles:
            if r.upper() not in valid_roles:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vai trò '{r}' không hợp lệ.")

        if current_admin.id == user_id and "ADMIN" not in [r.upper() for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quản trị viên không thể tự xóa quyền ADMIN của chính mình.",
            )

        user = AdminDashboardRepository.update_user_roles(db, user_id, roles)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy người dùng ID {user_id}.")

        # Audit log for user role change
        try:
            from app.repositories.audit_repo import AuditRepository
            AuditRepository.record_audit(
                db=db,
                action="USER_ROLE_CHANGE",
                entity_type="USER",
                entity_id=str(user.id),
                user_id=current_admin.id,
                new_values={"roles": roles, "email": user.email},
            )
        except Exception:
            pass

        user_roles = [ur.role.name for ur in user.roles if ur.role]
        return AdminUserItem(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            roles=user_roles,
            orders_count=0,
            total_spent=Decimal("0.00"),
            created_at=user.created_at,
        )

    # =========================================================================
    # COUPONS / PROMOTIONS MANAGEMENT
    # =========================================================================

    @classmethod
    def list_coupons(cls, db: Session) -> List[AdminCouponItem]:
        coupons = AdminDashboardRepository.list_all_coupons(db)
        results = []
        for c in coupons:
            total_discount = sum(
                (Decimal(str(u.discount_amount)) for u in c.usages), Decimal("0.00")
            )
            results.append(
                AdminCouponItem(
                    id=c.id,
                    code=c.code,
                    description=c.description,
                    discount_type=c.discount_type,
                    discount_value=Decimal(str(c.discount_value)),
                    min_order_value=Decimal(str(c.min_order_value)),
                    max_discount_value=(
                        Decimal(str(c.max_discount_value)) if c.max_discount_value else None
                    ),
                    usage_limit=c.usage_limit,
                    used_count=c.used_count,
                    start_date=c.start_date,
                    end_date=c.end_date,
                    is_active=c.is_active,
                    total_discount_given=total_discount.quantize(Decimal("0.01")),
                    created_at=c.created_at,
                )
            )
        return results

    @classmethod
    def create_coupon(cls, db: Session, data: AdminCouponCreateRequest) -> AdminCouponItem:
        code = data.code.strip().upper()
        existing = db.query(Coupon).filter(Coupon.code == code).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Mã giảm giá '{code}' đã tồn tại.")

        if data.start_date >= data.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ngày bắt đầu phải trước ngày kết thúc hiệu lực.",
            )

        coupon = Coupon(
            code=code,
            description=data.description.strip() if data.description else None,
            discount_type=data.discount_type.upper(),
            discount_value=data.discount_value,
            min_order_value=data.min_order_value,
            max_discount_value=data.max_discount_value,
            usage_limit=data.usage_limit,
            used_count=0,
            start_date=data.start_date,
            end_date=data.end_date,
            is_active=data.is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(coupon)
        db.commit()
        coupon_id = coupon.id if coupon.id is not None else 1

        # Audit log for coupon creation
        try:
            from app.repositories.audit_repo import AuditRepository
            AuditRepository.record_audit(
                db=db,
                action="COUPON_CREATE",
                entity_type="COUPON",
                entity_id=coupon.code,
                new_values={
                    "code": coupon.code,
                    "discount_type": coupon.discount_type,
                    "discount_value": str(coupon.discount_value),
                },
            )
        except Exception:
            pass

        return AdminCouponItem(
            id=coupon_id,
            code=coupon.code,
            description=coupon.description,
            discount_type=coupon.discount_type,
            discount_value=Decimal(str(coupon.discount_value)),
            min_order_value=Decimal(str(coupon.min_order_value)),
            max_discount_value=(
                Decimal(str(coupon.max_discount_value)) if coupon.max_discount_value else None
            ),
            usage_limit=coupon.usage_limit,
            used_count=0,
            start_date=coupon.start_date,
            end_date=coupon.end_date,
            is_active=coupon.is_active,
            total_discount_given=Decimal("0.00"),
            created_at=coupon.created_at,
        )

    @classmethod
    def toggle_coupon_status(cls, db: Session, coupon_id: int) -> AdminCouponItem:
        coupon = AdminDashboardRepository.toggle_coupon(db, coupon_id)
        if not coupon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy mã giảm giá ID {coupon_id}.")

        # Audit log for coupon toggle
        try:
            from app.repositories.audit_repo import AuditRepository
            AuditRepository.record_audit(
                db=db,
                action="COUPON_TOGGLE",
                entity_type="COUPON",
                entity_id=coupon.code,
                new_values={"is_active": coupon.is_active},
            )
        except Exception:
            pass

        total_discount = sum(
            (Decimal(str(u.discount_amount)) for u in coupon.usages), Decimal("0.00")
        )
        return AdminCouponItem(
            id=coupon.id,
            code=coupon.code,
            description=coupon.description,
            discount_type=coupon.discount_type,
            discount_value=Decimal(str(coupon.discount_value)),
            min_order_value=Decimal(str(coupon.min_order_value)),
            max_discount_value=(
                Decimal(str(coupon.max_discount_value)) if coupon.max_discount_value else None
            ),
            usage_limit=coupon.usage_limit,
            used_count=coupon.used_count,
            start_date=coupon.start_date,
            end_date=coupon.end_date,
            is_active=coupon.is_active,
            total_discount_given=total_discount.quantize(Decimal("0.01")),
            created_at=coupon.created_at,
        )
