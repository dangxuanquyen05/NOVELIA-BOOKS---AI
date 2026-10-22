/**
 * API client for Phase 7 Admin Dashboard, Store Operations, and Governance.
 */

import { getApiBaseUrl } from './api';
import {
  AdminAuthorCreatePayload,
  AdminAuthorItem,
  AdminCategoryCreatePayload,
  AdminCategoryItem,
  AdminCategoryUpdatePayload,
  AdminCouponCreatePayload,
  AdminCouponItem,
  AdminDashboardSummaryResponse,
  AdminPublisherCreatePayload,
  AdminPublisherItem,
  AdminUserItem,
  AdminUserListResponse,
} from '../types/adminDashboard';

function authHeaders(token: string): HeadersInit {
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

// ============================================================================
// EXECUTIVE DASHBOARD & KPIS
// ============================================================================

export async function fetchDashboardSummary(
  token: string,
  period: string = '30days'
): Promise<AdminDashboardSummaryResponse> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/v1/admin/dashboard/summary?period=${encodeURIComponent(period)}`;
  const res = await fetch(url, { headers: authHeaders(token) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tải dữ liệu dashboard: ${res.status}`);
  }
  return res.json();
}

// ============================================================================
// CATEGORIES TAXONOMY API
// ============================================================================

export async function fetchAdminCategories(token: string): Promise<AdminCategoryItem[]> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/categories`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tải danh mục: ${res.status}`);
  }
  return res.json();
}

export async function createAdminCategory(
  token: string,
  payload: AdminCategoryCreatePayload
): Promise<AdminCategoryItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/categories`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tạo danh mục: ${res.status}`);
  }
  return res.json();
}

export async function updateAdminCategory(
  token: string,
  id: number,
  payload: AdminCategoryUpdatePayload
): Promise<AdminCategoryItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/categories/${id}`, {
    method: 'PUT',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi cập nhật danh mục: ${res.status}`);
  }
  return res.json();
}

export async function deleteAdminCategory(
  token: string,
  id: number
): Promise<{ message: string }> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/categories/${id}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi xóa danh mục: ${res.status}`);
  }
  return res.json();
}

// ============================================================================
// AUTHORS & PUBLISHERS API
// ============================================================================

export async function fetchAdminAuthors(token: string): Promise<AdminAuthorItem[]> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/authors`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tải tác giả: ${res.status}`);
  }
  return res.json();
}

export async function createAdminAuthor(
  token: string,
  payload: AdminAuthorCreatePayload
): Promise<AdminAuthorItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/authors`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tạo tác giả: ${res.status}`);
  }
  return res.json();
}

export async function fetchAdminPublishers(token: string): Promise<AdminPublisherItem[]> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/publishers`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tải nhà xuất bản: ${res.status}`);
  }
  return res.json();
}

export async function createAdminPublisher(
  token: string,
  payload: AdminPublisherCreatePayload
): Promise<AdminPublisherItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/publishers`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tạo nhà xuất bản: ${res.status}`);
  }
  return res.json();
}

// ============================================================================
// USER GOVERNANCE API (ADMIN ONLY)
// ============================================================================

export async function fetchAdminUsers(
  token: string,
  page: number = 1,
  pageSize: number = 20,
  role?: string,
  query?: string
): Promise<AdminUserListResponse> {
  const baseUrl = getApiBaseUrl();
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (role) params.append('role', role);
  if (query) params.append('query', query);

  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/users?${params.toString()}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tải danh sách người dùng: ${res.status}`);
  }
  return res.json();
}

export async function updateAdminUserStatus(
  token: string,
  userId: number,
  isActive: boolean
): Promise<AdminUserItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/users/${userId}/status`, {
    method: 'PUT',
    headers: authHeaders(token),
    body: JSON.stringify({ is_active: isActive }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi cập nhật trạng thái người dùng: ${res.status}`);
  }
  return res.json();
}

export async function updateAdminUserRoles(
  token: string,
  userId: number,
  roles: string[]
): Promise<AdminUserItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/users/${userId}/role`, {
    method: 'PUT',
    headers: authHeaders(token),
    body: JSON.stringify({ roles }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi cập nhật vai trò người dùng: ${res.status}`);
  }
  return res.json();
}

// ============================================================================
// PROMOTIONS & COUPONS API
// ============================================================================

export async function fetchAdminCoupons(token: string): Promise<AdminCouponItem[]> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/coupons`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tải khuyến mãi: ${res.status}`);
  }
  return res.json();
}

export async function createAdminCoupon(
  token: string,
  payload: AdminCouponCreatePayload
): Promise<AdminCouponItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/coupons`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi tạo mã giảm giá: ${res.status}`);
  }
  return res.json();
}

export async function toggleAdminCouponStatus(
  token: string,
  couponId: number
): Promise<AdminCouponItem> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/admin/dashboard/coupons/${couponId}/toggle`, {
    method: 'PUT',
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi đổi trạng thái mã giảm giá: ${res.status}`);
  }
  return res.json();
}
