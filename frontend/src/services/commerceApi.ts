/**
 * Commerce & Customer API service handling Cart, Wishlist, Reviews, and Inventory.
 */

import { getApiBaseUrl } from './api';
import {
  BookReviewSummary,
  Cart,
  InventoryItem,
  InventoryTransaction,
  PaginatedInventory,
  Review,
  Wishlist,
} from '../types/commerce';

function authHeaders(token: string): HeadersInit {
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

// ============================================================================
// CART API
// ============================================================================

export async function fetchCart(token: string): Promise<Cart> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/cart`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi tải giỏ hàng: ${res.status}`);
  return res.json();
}

export async function addToCart(
  token: string,
  bookId: number,
  quantity: number = 1
): Promise<Cart> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/cart/items`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ book_id: bookId, quantity }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi thêm vào giỏ: ${res.status}`);
  }
  return res.json();
}

export async function updateCartItemQuantity(
  token: string,
  bookId: number,
  quantity: number
): Promise<Cart> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/cart/items/${bookId}`, {
    method: 'PUT',
    headers: authHeaders(token),
    body: JSON.stringify({ quantity }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi cập nhật số lượng: ${res.status}`);
  }
  return res.json();
}

export async function removeFromCart(token: string, bookId: number): Promise<Cart> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/cart/items/${bookId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi xóa khỏi giỏ: ${res.status}`);
  return res.json();
}

export async function clearCart(token: string): Promise<Cart> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/cart`, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi làm trống giỏ hàng: ${res.status}`);
  return res.json();
}

// ============================================================================
// WISHLIST API
// ============================================================================

export async function fetchWishlist(token: string): Promise<Wishlist> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/wishlist`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi tải danh sách yêu thích: ${res.status}`);
  return res.json();
}

export async function addToWishlist(token: string, bookId: number): Promise<Wishlist> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/wishlist/${bookId}`, {
    method: 'POST',
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi lưu vào yêu thích: ${res.status}`);
  return res.json();
}

export async function removeFromWishlist(
  token: string,
  bookId: number
): Promise<Wishlist> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/wishlist/${bookId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi xóa khỏi yêu thích: ${res.status}`);
  return res.json();
}

export async function moveWishlistToCart(
  token: string,
  bookId: number
): Promise<Cart> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/wishlist/${bookId}/move-to-cart`, {
    method: 'POST',
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi chuyển vào giỏ: ${res.status}`);
  }
  return res.json();
}

// ============================================================================
// REVIEWS API
// ============================================================================

export async function fetchBookReviews(bookId: number): Promise<BookReviewSummary> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/catalog/books/${bookId}/reviews`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) throw new Error(`Lỗi tải đánh giá: ${res.status}`);
  return res.json();
}

export async function createBookReview(
  token: string,
  bookId: number,
  data: { rating: number; title?: string; comment: string }
): Promise<Review> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/catalog/books/${bookId}/reviews`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi gửi đánh giá: ${res.status}`);
  }
  return res.json();
}

export async function deleteBookReview(token: string, reviewId: number): Promise<void> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/catalog/reviews/${reviewId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi xóa đánh giá: ${res.status}`);
}

// ============================================================================
// INVENTORY API (STAFF & ADMIN)
// ============================================================================

export async function fetchInventory(
  token: string,
  page: number = 1,
  lowStockOnly: boolean = false,
  query?: string
): Promise<PaginatedInventory> {
  const baseUrl = getApiBaseUrl();
  const params = new URLSearchParams({
    page: String(page),
    page_size: '20',
    low_stock_only: String(lowStockOnly),
  });
  if (query?.trim()) params.append('query', query.trim());

  const res = await fetch(`${baseUrl}/api/v1/inventory?${params.toString()}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi tải danh mục kho: ${res.status}`);
  return res.json();
}

export async function inboundRestock(
  token: string,
  data: {
    book_id: number;
    quantity: number;
    reference_code: string;
    reason?: string;
  }
): Promise<InventoryItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/inventory/inbound`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi nhập kho: ${res.status}`);
  }
  return res.json();
}

export async function adjustStock(
  token: string,
  data: {
    book_id: number;
    quantity_change: number;
    reference_code: string;
    reason: string;
  }
): Promise<InventoryItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/inventory/adjust`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi điều chỉnh kho: ${res.status}`);
  }
  return res.json();
}

export async function fetchInventoryHistory(
  token: string,
  bookId: number
): Promise<InventoryTransaction[]> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/inventory/${bookId}/history`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi tải lịch sử kho: ${res.status}`);
  return res.json();
}

// ============================================================================
// COUPONS & CHECKOUT & ORDERS API (PHASE 6)
// ============================================================================

export async function validateCoupon(
  code: string,
  subtotal: number,
  token?: string
): Promise<import('../types/commerce').CouponValidationResult> {
  const baseUrl = getApiBaseUrl();
  const headers: HeadersInit = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${baseUrl}/api/v1/coupons/validate`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ code, subtotal }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi kiểm tra mã giảm giá: ${res.status}`);
  }
  return res.json();
}

export async function checkoutOrder(
  token: string,
  payload: import('../types/commerce').CheckoutPayload
): Promise<import('../types/commerce').Order> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/orders/checkout`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi đặt hàng: ${res.status}`);
  }
  return res.json();
}

export async function fetchMyOrders(
  token: string,
  page: number = 1,
  pageSize: number = 10,
  status?: string
): Promise<import('../types/commerce').PaginatedOrders> {
  const baseUrl = getApiBaseUrl();
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (status && status !== 'ALL') params.append('status', status);

  const res = await fetch(`${baseUrl}/api/v1/orders?${params.toString()}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi tải danh sách đơn hàng: ${res.status}`);
  return res.json();
}

export async function fetchOrderDetail(
  token: string,
  orderCode: string
): Promise<import('../types/commerce').Order> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/orders/${encodeURIComponent(orderCode)}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tải chi tiết đơn hàng: ${res.status}`);
  }
  return res.json();
}

export async function cancelOrder(
  token: string,
  orderCode: string,
  reason: string
): Promise<import('../types/commerce').Order> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/orders/${encodeURIComponent(orderCode)}/cancel`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi hủy đơn hàng: ${res.status}`);
  }
  return res.json();
}

export async function fetchAdminOrders(
  token: string,
  page: number = 1,
  pageSize: number = 20,
  status?: string,
  query?: string
): Promise<import('../types/commerce').PaginatedOrders> {
  const baseUrl = getApiBaseUrl();
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (status && status !== 'ALL') params.append('status', status);
  if (query && query.trim()) params.append('query', query.trim());

  const res = await fetch(`${baseUrl}/api/v1/admin/orders?${params.toString()}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`Lỗi tải danh sách quản trị đơn: ${res.status}`);
  return res.json();
}

export async function updateOrderStatus(
  token: string,
  orderCode: string,
  status: string,
  staffNotes?: string,
  cancellationReason?: string
): Promise<import('../types/commerce').Order> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/orders/${encodeURIComponent(orderCode)}/status`, {
    method: 'PUT',
    headers: authHeaders(token),
    body: JSON.stringify({
      status,
      staff_notes: staffNotes,
      cancellation_reason: cancellationReason,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi cập nhật trạng thái đơn: ${res.status}`);
  }
  return res.json();
}
