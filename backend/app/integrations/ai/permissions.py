"""RBAC and Security Permission verification for AI tool calling."""

from typing import Dict, List, Optional, Tuple

TOOL_PERMISSIONS: Dict[str, List[str]] = {
    # Customer-Facing Read Tools (Available to all visitors including GUEST)
    "search_catalog_tool": ["GUEST", "CUSTOMER", "STAFF", "ADMIN"],
    "get_book_details_tool": ["GUEST", "CUSTOMER", "STAFF", "ADMIN"],
    "check_book_stock_tool": ["GUEST", "CUSTOMER", "STAFF", "ADMIN"],
    "get_shipping_and_checkout_guide_tool": ["GUEST", "CUSTOMER", "STAFF", "ADMIN"],
    "get_reading_recommendations_tool": ["GUEST", "CUSTOMER", "STAFF", "ADMIN"],

    # Customer Authenticated Tools (Requires logged in account)
    "add_to_cart_tool": ["CUSTOMER", "STAFF", "ADMIN"],
    "get_my_orders_tool": ["CUSTOMER", "STAFF", "ADMIN"],
    "track_order_status_tool": ["CUSTOMER", "STAFF", "ADMIN"],

    # Staff & Admin Only Tools (Phase 10 AI Admin Copilot)
    "get_sales_summary": ["STAFF", "ADMIN"],
    "get_inventory_summary": ["STAFF", "ADMIN"],
    "find_low_stock_books": ["STAFF", "ADMIN"],
    "search_orders": ["STAFF", "ADMIN"],
    "search_books": ["STAFF", "ADMIN"],
    "prepare_book_update": ["STAFF", "ADMIN"],
    "draft_product_description": ["STAFF", "ADMIN"],
    "draft_promotion": ["STAFF", "ADMIN"],
    "prepare_inventory_adjustment": ["STAFF", "ADMIN"],
    "draft_book_metadata_tool": ["STAFF", "ADMIN"],
    "draft_promotion_campaign_tool": ["STAFF", "ADMIN"],
    "query_business_metrics_tool": ["ADMIN"],
}


def verify_tool_permission(
    tool_name: str,
    user_roles: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """Verify if the caller's role is authorized to execute the requested tool.
    
    Returns:
        (is_allowed: bool, explanation_or_error_message: str)
    """
    if tool_name not in TOOL_PERMISSIONS:
        return False, f"Công cụ '{tool_name}' không được phép thực thi hoặc chưa được đăng ký trong hệ thống."

    allowed_roles = TOOL_PERMISSIONS[tool_name]
    effective_roles = user_roles if user_roles else ["GUEST"]

    # Check intersection of user roles and allowed roles
    if any(role in allowed_roles for role in effective_roles):
        return True, "Authorized"

    # Specific feedback for unauthenticated visitors
    if "GUEST" in effective_roles and "GUEST" not in allowed_roles:
        return False, "Thao tác này yêu cầu quý khách phải đăng nhập tài khoản để thực hiện."

    return False, f"Tài khoản của bạn không có quyền thực hiện công cụ '{tool_name}' (Yêu cầu quyền: {', '.join(allowed_roles)})."
