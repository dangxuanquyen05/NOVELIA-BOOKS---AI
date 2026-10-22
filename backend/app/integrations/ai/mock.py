"""Deterministic Mock AI Provider for offline testing and development."""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from app.integrations.ai.base import (
    AIMessagePayload,
    AIProvider,
    AIProviderHealth,
    AIProviderResponse,
    ToolCall,
    ToolDefinition,
)


class MockAIProvider(AIProvider):
    """Smart mock provider with intent recognition and tool call emulation."""

    def __init__(
        self,
        simulate_timeout: bool = False,
        simulate_error: bool = False,
        simulate_missing_key: bool = False,
    ):
        self.simulate_timeout = simulate_timeout
        self.simulate_error = simulate_error
        self.simulate_missing_key = simulate_missing_key

    def check_health(self) -> AIProviderHealth:
        """Inspect mock health state."""
        if self.simulate_missing_key:
            return AIProviderHealth(
                status="MISSING_API_KEY",
                provider_name="mock",
                model="mock-gpt",
                is_configured=False,
                details="Mock configured to simulate missing credentials.",
            )

        return AIProviderHealth(
            status="MOCK_READY",
            provider_name="mock",
            model="mock-intelligent-assistant-v1",
            is_configured=True,
            details="Mock AI Provider đang hoạt động bình thường (Chế độ mô phỏng kiểm thử).",
        )

    async def generate_response(
        self,
        messages: List[AIMessagePayload],
        tools: Optional[List[ToolDefinition]] = None,
        system_prompt: Optional[str] = None,
    ) -> AIProviderResponse:
        """Emulate conversational flow and tool invocation based on user prompt semantics."""
        if self.simulate_timeout:
            await asyncio.sleep(0.01)
            return AIProviderResponse(
                is_error=True,
                error_message="Mô hình AI bị quá thời gian chờ (Timeout test simulation).",
            )

        if self.simulate_error:
            return AIProviderResponse(
                is_error=True,
                error_message="Lỗi kết nối từ mô phỏng nhà cung cấp AI.",
            )

        # 1. Check if the latest message is a tool execution result
        latest_msg = messages[-1] if messages else None

        if latest_msg and latest_msg.role == "tool":
            return self._format_tool_result_summary(latest_msg)

        # 2. Extract last user text prompt
        user_text = ""
        for m in reversed(messages):
            if m.role == "user" and m.content:
                user_text = m.content.strip()
                break

        lowered = user_text.lower()

        # (BookMatch AI Explanation intent)
        if "bookmatch ai" in lowered or "gợi ý cho độc giả này" in lowered:
            return AIProviderResponse(
                content="Tác phẩm xuất sắc phù hợp hoàn hảo với sở thích đọc và phong cách văn chương yêu thích của bạn.",
                tool_calls=None,
                tokens_used=35,
            )

        # 3. Intent Detection & Tool Emulation

        # (Admin 1) Sales summary: "doanh thu", "báo cáo bán hàng", "kpi", "sales summary"
        if any(w in lowered for w in ["doanh thu", "báo cáo bán hàng", "kpi", "sales summary"]):
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_sales_1",
                        name="get_sales_summary",
                        arguments={},
                    )
                ],
                tokens_used=40,
            )

        # (Admin 2) Inventory summary: "tồn kho toàn hệ thống", "tổng tồn kho", "báo cáo kho", "kho hàng toàn bộ"
        if any(w in lowered for w in ["tồn kho toàn hệ thống", "tổng tồn kho", "báo cáo kho", "kho hàng toàn bộ", "inventory summary"]):
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_inv_summary_1",
                        name="get_inventory_summary",
                        arguments={},
                    )
                ],
                tokens_used=40,
            )

        # (Admin 3) Low stock books: "sắp hết hàng", "cảnh báo kho", "low stock", "sách tồn ít"
        if any(w in lowered for w in ["sắp hết hàng", "cảnh báo kho", "low stock", "tồn ít", "sắp hết"]):
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_low_stock_1",
                        name="find_low_stock_books",
                        arguments={"limit": 10},
                    )
                ],
                tokens_used=40,
            )

        # (Admin 4) Prepare inventory adjustment: "điều chỉnh kho", "nhập thêm", "tăng tồn kho", "giảm tồn kho"
        if any(w in lowered for w in ["điều chỉnh kho", "nhập thêm", "tăng tồn kho", "giảm tồn kho", "adjust inventory"]):
            id_match = re.search(r"(?:sách|id|cuốn)\s*#?(\d+)", lowered)
            book_id = int(id_match.group(1)) if id_match else 1
            delta_match = re.search(r"([+-]?\d+)\s*(?:cuốn|bản)", lowered)
            delta = int(delta_match.group(1)) if delta_match else 10
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_adj_inv_1",
                        name="prepare_inventory_adjustment",
                        arguments={
                            "book_id": book_id,
                            "delta": delta,
                            "reason": "Điều chỉnh kho qua Novelia AI Admin Copilot",
                        },
                    )
                ],
                tokens_used=45,
            )

        # (Admin 5) Prepare book update: "sửa giá", "cập nhật giá", "đổi giá"
        if any(w in lowered for w in ["sửa giá", "cập nhật giá", "đổi giá", "update giá"]):
            id_match = re.search(r"(?:sách|id|cuốn)\s*#?(\d+)", lowered)
            book_id = int(id_match.group(1)) if id_match else 1
            price_match = re.search(r"(?:thành|lên|xuống|giá)\s*(\d{4,9})", lowered)
            new_price = float(price_match.group(1)) if price_match else 125000.0
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_update_book_1",
                        name="prepare_book_update",
                        arguments={
                            "book_id": book_id,
                            "new_price": new_price,
                        },
                    )
                ],
                tokens_used=45,
            )

        # (Admin 6) Draft promotion: "tạo mã giảm giá", "tạo coupon", "tạo voucher", "khuyến mãi mới"
        if any(w in lowered for w in ["tạo mã giảm giá", "tạo coupon", "tạo voucher", "khuyến mãi mới"]):
            code_match = re.search(r"(?:mã|code)\s*([A-Za-z0-9_-]+)", user_text)
            code = code_match.group(1).upper() if code_match else "SALE2026"
            percent_match = re.search(r"(\d{1,2})%", lowered)
            percent = int(percent_match.group(1)) if percent_match else 15
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_promo_1",
                        name="draft_promotion",
                        arguments={
                            "code": code,
                            "discount_percent": percent,
                            "max_discount_amount": 50000,
                            "min_order_amount": 100000,
                        },
                    )
                ],
                tokens_used=45,
            )

        # (Admin 7) Draft product description: "soạn mô tả", "viết mô tả", "draft description"
        if any(w in lowered for w in ["soạn mô tả", "viết mô tả", "mô tả sách"]):
            id_match = re.search(r"(?:sách|id|cuốn)\s*#?(\d+)", lowered)
            book_id = int(id_match.group(1)) if id_match else 1
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_desc_1",
                        name="draft_product_description",
                        arguments={"book_id": book_id},
                    )
                ],
                tokens_used=45,
            )

        # (Admin 8) Search orders (admin scope): "tìm đơn", "tra cứu đơn hàng hệ thống", "danh sách đơn"
        if any(w in lowered for w in ["tìm đơn", "tra cứu đơn hàng hệ thống", "danh sách đơn toàn hệ thống"]):
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_search_orders_1",
                        name="search_orders",
                        arguments={"limit": 5},
                    )
                ],
                tokens_used=40,
            )

        # (Admin 9) Search books (admin scope): "tra cứu sách admin", "tìm sách admin"
        if any(w in lowered for w in ["tra cứu sách admin", "tìm sách admin"]):
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_search_books_admin_1",
                        name="search_books",
                        arguments={"limit": 5},
                    )
                ],
                tokens_used=40,
            )

        # (Customer a) Add to cart intent: "thêm vào giỏ", "cho vào giỏ", "mua cuốn"
        if ("thêm" in lowered or "cho vào" in lowered) and ("giỏ" in lowered or "mua" in lowered):
            # Try to extract book_id if mentioned (e.g., "id 1", "sách 1")
            match = re.search(r"(?:sách|id|cuốn)\s*#?(\d+)", lowered)
            book_id = int(match.group(1)) if match else 1
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_cart_1",
                        name="add_to_cart_tool",
                        arguments={"book_id": book_id, "quantity": 1},
                    )
                ],
                tokens_used=45,
            )

        # (b) Tracking specific order intent: "NVL-" or "theo dõi đơn"
        order_match = re.search(r"(NVL-\d{8}-[A-Za-z0-9]+)", user_text)
        if order_match or ("theo dõi" in lowered and "đơn" in lowered):
            code = order_match.group(1) if order_match else "NVL-SAMPLE"
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_track_1",
                        name="track_order_status_tool",
                        arguments={"order_code": code},
                    )
                ],
                tokens_used=40,
            )

        # (c) List my orders: "đơn hàng của tôi", "lịch sử đơn", "tra cứu đơn"
        if ("đơn hàng" in lowered or "lịch sử" in lowered) and ("tôi" in lowered or "của" in lowered or "tra cứu" in lowered):
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_orders_1",
                        name="get_my_orders_tool",
                        arguments={"limit": 5},
                    )
                ],
                tokens_used=35,
            )

        # (d) Check stock: "tồn kho", "còn hàng không", "kiểm tra kho", "còn bao nhiêu"
        if "tồn kho" in lowered or "còn hàng" in lowered or "kiểm tra kho" in lowered or "còn cuốn" in lowered:
            id_match = re.search(r"(?:sách|id|cuốn)\s*#?(\d+)", lowered)
            identifier = id_match.group(1) if id_match else user_text
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_stock_1",
                        name="check_book_stock_tool",
                        arguments={"identifier": identifier},
                    )
                ],
                tokens_used=40,
            )

        # (e) Shipping policies / Checkout guidance: "phí ship", "phí vận chuyển", "giao hàng", "checkout", "thanh toán"
        if any(w in lowered for w in ["phí ship", "vận chuyển", "giao hàng", "thanh toán", "chính sách ship", "hướng dẫn mua"]):
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_guide_1",
                        name="get_shipping_and_checkout_guide_tool",
                        arguments={},
                    )
                ],
                tokens_used=30,
            )

        # (f) Book recommendations: "gợi ý", "sách hay", "bán chạy", "tiêu biểu"
        if "gợi ý" in lowered or "bán chạy" in lowered or "tiêu biểu" in lowered:
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_rec_1",
                        name="get_reading_recommendations_tool",
                        arguments={"limit": 4},
                    )
                ],
                tokens_used=38,
            )

        # (g) Search catalog intent: "tìm sách", "trinh thám", "kinh tế", "văn học", or budget "dưới 150k"
        if any(w in lowered for w in ["tìm", "sách", "thể loại", "tác giả", "dưới", "ngân sách", "khoảng"]):
            max_price = None
            if "dưới 150k" in lowered or "dưới 150000" in lowered:
                max_price = 150000.0
            elif "dưới 200k" in lowered or "dưới 200000" in lowered:
                max_price = 200000.0
            elif "dưới 100k" in lowered or "dưới 100000" in lowered:
                max_price = 100000.0

            clean_q = re.sub(r"(tìm|sách|về|thể loại|cuốn|dưới \d+k?)", "", lowered).strip()
            return AIProviderResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_mock_search_1",
                        name="search_catalog_tool",
                        arguments={
                            "query": clean_q if clean_q else None,
                            "max_price": max_price,
                            "limit": 4,
                        },
                    )
                ],
                tokens_used=42,
            )

        # Default conversational greeting / assistance
        return AIProviderResponse(
            content=(
                "Dạ chào Quý khách! Em là Novelia AI — Trợ lý tư vấn sách của NOVELIA BOOKS.\n\n"
                "Em có thể hỗ trợ Quý khách:\n"
                "• 🔍 **Tìm sách** theo thể loại, tác giả và mức giá ngân sách.\n"
                "• 📦 **Kiểm tra tồn kho thực tế** & giá bán chuẩn xác tại kho.\n"
                "• 🛒 **Thêm sách vào giỏ hàng** trực tiếp qua cuộc trò chuyện.\n"
                "• 📋 **Tra cứu đơn hàng** & hành trình vận chuyển chi tiết.\n"
                "• 🚚 **Chính sách miễn phí vận chuyển** & phương thức thanh toán.\n\n"
                "Quý khách đang tìm kiếm tác phẩm nào hôm nay ạ?"
            ),
            tokens_used=120,
        )

    def _format_tool_result_summary(self, tool_msg: AIMessagePayload) -> AIProviderResponse:
        """Synthesize a natural language summary after a tool returns data."""
        try:
            data = json.loads(tool_msg.content or "{}")
        except Exception:
            data = {"output": tool_msg.content}

        tool_name = tool_msg.name or ""

        # Handle permission rejection or tool execution error
        if not data.get("success", True) and "message" in data:
            if data.get("error_code") == "REJECTED_RBAC" or data.get("requires_auth"):
                return AIProviderResponse(content=f"🔒 {data.get('message')}", tokens_used=30)
            return AIProviderResponse(content=f"Dạ, {data.get('message')}", tokens_used=30)

        if tool_name == "search_catalog_tool":
            books = data.get("books", [])
            total = data.get("total_matches", len(books))
            if not books:
                return AIProviderResponse(
                    content="Dạ, hiện tại Novelia Books chưa có đầu sách nào phù hợp chính xác với yêu cầu của Quý khách. Quý khách có muốn em gợi ý thêm những tác phẩm nổi bật khác không ạ?",
                    tokens_used=50,
                )
            names = [f"• **{b['title']}** - {b.get('primary_author', 'Tác giả')} (Giá: {b['price']:,.0f} đ)" for b in books]
            return AIProviderResponse(
                content=f"Dạ, Novelia Books tìm thấy {total} tác phẩm phù hợp với yêu cầu của Quý khách:\n\n" + "\n".join(names) + "\n\nQuý khách muốn em kiểm tra thêm chi tiết cuốn nào hoặc thêm vào giỏ hàng không ạ?",
                tokens_used=140,
            )

        elif tool_name == "check_book_stock_tool":
            if not data.get("success"):
                return AIProviderResponse(content=f"Dạ, {data.get('message', 'Không tìm thấy thông tin sách.')}", tokens_used=30)
            avail = data.get("available_stock", 0)
            title = data.get("title", "Tác phẩm")
            price = data.get("price", 0)
            if avail > 0:
                return AIProviderResponse(
                    content=f"Dạ vâng! Tác phẩm **{title}** hiện đang có giá **{price:,.0f} đ** và còn **{avail} cuốn** sẵn sàng xuất kho giao ngay ạ.",
                    tokens_used=50,
                )
            return AIProviderResponse(
                content=f"Dạ tiếc là tác phẩm **{title}** hiện đang tạm hết hàng trong kho rồi ạ. Quý khách có thể bấm 'Thêm vào Wishlist' để nhận thông báo ngay khi có sách mới về nhé!",
                tokens_used=55,
            )

        elif tool_name == "add_to_cart_tool":
            if data.get("requires_auth"):
                return AIProviderResponse(content=f"⚠️ {data.get('message')}", tokens_used=30)
            if data.get("success"):
                return AIProviderResponse(
                    content=f"🎉 {data.get('message')}\nHiện giỏ hàng của Quý khách đang có tổng cộng **{data.get('cart_total_items', 1)} sản phẩm** (Tạm tính: **{data.get('cart_subtotal', 0):,.0f} đ**). Quý khách có thể mở giỏ hàng để tiến hành thanh toán bất cứ lúc nào ạ!",
                    tokens_used=70,
                )
            return AIProviderResponse(content=f"❌ {data.get('message', 'Không thể thêm vào giỏ.')}", tokens_used=30)

        elif tool_name == "get_my_orders_tool":
            if data.get("requires_auth"):
                return AIProviderResponse(content=f"🔒 {data.get('message')}", tokens_used=30)
            orders = data.get("orders", [])
            if not orders:
                return AIProviderResponse(content="Dạ, Quý khách hiện chưa có đơn hàng nào tại Novelia Books. Quý khách hãy dạo xem danh mục sách và chọn cho mình tác phẩm ưng ý nhé!", tokens_used=45)
            lines = [f"• Mã **{o['order_code']}** - Trạng thái: **{o['status']}** - Tổng tiền: **{o['total_amount']:,.0f} đ** (Đặt ngày {o['created_at']})" for o in orders]
            return AIProviderResponse(
                content="Dạ, đây là danh sách các đơn hàng gần đây của Quý khách tại Novelia Books:\n\n" + "\n".join(lines) + "\n\nQuý khách có thể yêu cầu em theo dõi chi tiết mã đơn cụ thể bất cứ lúc nào ạ!",
                tokens_used=130,
            )

        elif tool_name == "track_order_status_tool":
            if data.get("requires_auth"):
                return AIProviderResponse(content=f"🔒 {data.get('message')}", tokens_used=30)
            if not data.get("success"):
                return AIProviderResponse(content=f"Dạ, {data.get('message')}", tokens_used=30)
            code = data.get("order_code")
            carrier = data.get("carrier")
            tracking = data.get("tracking_code") or "Đang cấp mã"
            status_text = data.get("shipment_status")
            return AIProviderResponse(
                content=f"📦 Thông tin vận chuyển đơn hàng **{code}**:\n• Đơn vị vận chuyển: **{carrier}**\n• Mã vận đơn: `{tracking}`\n• Trạng thái: **{status_text}**\nĐơn hàng đang được xử lý giao đến địa chỉ của Quý khách theo đúng lịch hẹn.",
                tokens_used=80,
            )

        elif tool_name == "get_shipping_and_checkout_guide_tool":
            policies = data.get("policies", {})
            return AIProviderResponse(
                content=(
                    "🚚 **Chính sách Vận chuyển & Thanh toán tại NOVELIA BOOKS**:\n\n"
                    f"• {policies.get('shipping_rule_description')}\n"
                    f"• Thời gian giao hàng: {policies.get('delivery_time')}\n"
                    "• Phương thức thanh toán: Hỗ trợ tiền mặt khi nhận hàng (COD) và cổng thanh toán trực tuyến an toàn VNPay.\n\n"
                    "Quý khách cần em tư vấn thêm bước nào không ạ?"
                ),
                tokens_used=110,
            )

        elif tool_name == "get_reading_recommendations_tool":
            recs = data.get("recommendations", [])
            lines = [f"• **{r['title']}** - {r.get('primary_author', '')} ({r['price']:,.0f} đ)" for r in recs]
            return AIProviderResponse(
                content="Dạ, gửi Quý khách những tác phẩm đang được đông đảo độc giả Novelia yêu thích nhất:\n\n" + "\n".join(lines) + "\n\nQuý khách muốn em gửi trích dẫn hoặc thêm tựa nào vào giỏ hàng không ạ?",
                tokens_used=120,
            )

        # ----------------------------------------------------------------------
        # Admin Copilot Tools
        # ----------------------------------------------------------------------
        elif tool_name == "get_sales_summary":
            rev = data.get("total_revenue", 0)
            coll = data.get("collected_revenue", 0)
            orders = data.get("valid_orders_count", 0)
            aov = data.get("average_order_value", 0)
            return AIProviderResponse(
                content=(
                    f"📊 **Báo cáo Doanh thu & Vận hành (Authoritative MySQL KPI)**:\n\n"
                    f"• Tổng doanh thu phát sinh: **{rev:,.0f} đ**\n"
                    f"• Thực thu thanh toán (Đã PAID): **{coll:,.0f} đ**\n"
                    f"• Số đơn hàng hợp lệ: **{orders} đơn**\n"
                    f"• Giá trị trung bình mỗi đơn (AOV): **{aov:,.0f} đ**\n"
                    f"• Ghi chú: {data.get('profit_note', '')}"
                ),
                tokens_used=120,
            )

        elif tool_name == "get_inventory_summary":
            books = data.get("total_books", 0)
            phys = data.get("total_physical_stock", 0)
            res = data.get("total_reserved_stock", 0)
            avail = data.get("total_available_stock", 0)
            low = data.get("low_stock_count", 0)
            return AIProviderResponse(
                content=(
                    f"📦 **Tổng quan Tồn kho Toàn hệ thống**:\n\n"
                    f"• Tổng số đầu sách đang quản lý: **{books} đầu sách**\n"
                    f"• Tổng tồn kho vật lý: **{phys:,} cuốn**\n"
                    f"• Tồn kho đang giữ chỗ (Đơn đang xử lý): **{res:,} cuốn**\n"
                    f"• Tồn kho khả dụng thực tế: **{avail:,} cuốn**\n"
                    f"• Số đầu sách chạm ngưỡng cảnh báo sắp hết: **{low} đầu sách**"
                ),
                tokens_used=110,
            )

        elif tool_name == "find_low_stock_books":
            alerts = data.get("low_stock_books", [])
            if not alerts:
                return AIProviderResponse(
                    content="✅ Hiện tại tất cả đầu sách trong kho đều đạt mức tồn kho an toàn, không có sách nào dưới ngưỡng cảnh báo.",
                    tokens_used=40,
                )
            lines = [
                f"• **{item['title']}** (ID #{item['book_id']}) — Khả dụng: **{item['available_stock']}** (Vật lý: {item['physical_stock']}, Giữ chỗ: {item['reserved_stock']}, Ngưỡng: {item['low_stock_threshold']})"
                for item in alerts
            ]
            return AIProviderResponse(
                content=f"⚠️ **Danh sách {len(alerts)} đầu sách sắp hết hàng cần nhập bổ sung**:\n\n" + "\n".join(lines),
                tokens_used=140,
            )

        elif tool_name == "search_orders":
            orders = data.get("orders", [])
            total = data.get("total_matches", len(orders))
            if not orders:
                return AIProviderResponse(content="Dạ, không tìm thấy đơn hàng nào khớp với tiêu chí tìm kiếm.", tokens_used=30)
            lines = [
                f"• Mã **{o['order_code']}** — Khách: **{o['customer_name']}** ({o['phone']}) — {o['total_amount']:,.0f} đ — Trạng thái: **{o['status']}**"
                for o in orders
            ]
            return AIProviderResponse(
                content=f"📋 Tìm thấy {total} đơn hàng phù hợp:\n\n" + "\n".join(lines),
                tokens_used=130,
            )

        elif tool_name == "search_books":
            books = data.get("books", [])
            if not books:
                return AIProviderResponse(content="Dạ, không tìm thấy đầu sách nào trong danh mục quản trị.", tokens_used=30)
            lines = [
                f"• ID #{b['id']} **{b['title']}** — Giá: {b['price']:,.0f} đ — Tồn khả dụng: {b['available_stock']} cuốn"
                for b in books
            ]
            return AIProviderResponse(
                content=f"📚 Danh mục quản trị tìm thấy {len(books)} sách:\n\n" + "\n".join(lines),
                tokens_used=120,
            )

        elif tool_name == "prepare_book_update":
            preview = data.get("preview", {})
            token = data.get("confirmation_token", "")
            return AIProviderResponse(
                content=(
                    f"⚠️ **BẢN XEM TRƯỚC CẬP NHẬT SÁCH (Yêu cầu xác nhận Two-Phase)**:\n\n"
                    f"• Tựa đề: **{preview.get('proposed_title')}** (Hiện tại: {preview.get('current_title')})\n"
                    f"• Giá bán mới đề xuất: **{preview.get('proposed_price', 0):,.0f} đ** (Giá cũ: {preview.get('current_price', 0):,.0f} đ)\n"
                    f"• Trạng thái: **{preview.get('proposed_status')}**\n"
                    f"• Mã xác nhận (Token): `{token}`\n\n"
                    f"*(Dữ liệu trong MySQL chưa thay đổi. Vui lòng nhấn nút Xác nhận trên giao diện hoặc gửi mã token để hoàn tất)*"
                ),
                tokens_used=130,
            )

        elif tool_name == "draft_product_description":
            draft = data.get("draft", {})
            title = data.get("book_title", "")
            points = "\n".join([f"  - {p}" for p in draft.get("key_selling_points", [])])
            return AIProviderResponse(
                content=(
                    f"📝 **Bản nháp mô tả sản phẩm cho '{title}'**:\n\n"
                    f"**Tiêu đề nổi bật:** {draft.get('headline')}\n\n"
                    f"**Tóm tắt nội dung:**\n{draft.get('synopsis')}\n\n"
                    f"**Điểm bán hàng nổi bật (Selling Points):**\n{points}\n\n"
                    f"**Đối tượng độc giả:** {draft.get('target_audience')}\n\n"
                    f"**Lời kêu gọi hành động:** {draft.get('call_to_action')}"
                ),
                tokens_used=180,
            )

        elif tool_name == "draft_promotion":
            preview = data.get("preview", {})
            token = data.get("confirmation_token", "")
            return AIProviderResponse(
                content=(
                    f"🎟️ **BẢN XEM TRƯỚC MÃ KHUYẾN MÃI MỚI (Yêu cầu xác nhận Two-Phase)**:\n\n"
                    f"• Mã giảm giá: `{preview.get('code')}`\n"
                    f"• Mức giảm: **{preview.get('discount_percent')}%** (Tối đa: {preview.get('max_discount_amount', 0):,.0f} đ)\n"
                    f"• Đơn hàng tối thiểu: **{preview.get('min_order_amount', 0):,.0f} đ**\n"
                    f"• Giới hạn lượt dùng: **{preview.get('usage_limit')} lượt**\n"
                    f"• Thời hạn hiệu lực: **{preview.get('duration_days')} ngày**\n"
                    f"• Mã xác nhận (Token): `{token}`\n\n"
                    f"*(Mã khuyến mãi chưa được kích hoạt. Quản trị viên vui lòng nhấn nút Xác nhận để đưa mã vào hoạt động)*"
                ),
                tokens_used=140,
            )

        elif tool_name == "prepare_inventory_adjustment":
            preview = data.get("preview", {})
            token = data.get("confirmation_token", "")
            delta = preview.get("delta", 0)
            return AIProviderResponse(
                content=(
                    f"📦 **BẢN XEM TRƯỚC ĐIỀU CHỈNH TỒN KHO (Yêu cầu xác nhận Two-Phase)**:\n\n"
                    f"• Sách: **{preview.get('book_title')}** (ID #{preview.get('book_id')})\n"
                    f"• Biến động đề xuất: **{delta:+d} cuốn**\n"
                    f"• Tồn kho vật lý: {preview.get('current_physical_stock')} ➔ **{preview.get('proposed_physical_stock')} cuốn**\n"
                    f"• Tồn kho khả dụng: {preview.get('current_available_stock')} ➔ **{preview.get('proposed_available_stock')} cuốn**\n"
                    f"• Tồn kho giữ chỗ: {preview.get('reserved_stock')} cuốn (An toàn: Tồn mới ≥ Giữ chỗ)\n"
                    f"• Lý do: {preview.get('reason')}\n"
                    f"• Mã xác nhận (Token): `{token}`\n\n"
                    f"*(Số liệu tồn kho chưa được ghi nhận vào kho. Vui lòng bấm Xác nhận để hoàn tất điều chỉnh)*"
                ),
                tokens_used=150,
            )

        return AIProviderResponse(
            content=f"Dạ, Novelia AI đã tiếp nhận kết quả: {str(data)[:200]}",
            tokens_used=50,
        )
