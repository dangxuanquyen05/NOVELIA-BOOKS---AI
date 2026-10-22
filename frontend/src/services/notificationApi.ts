/**
 * API client for In-App Notifications and Alerts.
 */

import {
  MarkReadResponse,
  NotificationItem,
  NotificationListResponse,
  UnreadCountResponse,
} from '../types/notification';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export async function fetchNotifications(
  token: string | null,
  isRead?: boolean,
  notificationType?: string,
  page: number = 1,
  limit: number = 20
): Promise<NotificationListResponse> {
  const params = new URLSearchParams();
  if (isRead !== undefined) params.append('is_read', String(isRead));
  if (notificationType) params.append('notification_type', notificationType);
  params.append('page', String(page));
  params.append('limit', String(limit));

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/notifications?${params.toString()}`, {
    method: 'GET',
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Không thể tải danh sách thông báo.');
  }

  return res.json();
}

export async function fetchUnreadCount(
  token: string | null
): Promise<UnreadCountResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/notifications/unread-count`, {
    method: 'GET',
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Không thể lấy số thông báo chưa đọc.');
  }

  return res.json();
}

export async function markNotificationAsRead(
  token: string | null,
  notificationId: number
): Promise<NotificationItem> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/notifications/${notificationId}/read`, {
    method: 'PUT',
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Không thể đánh dấu thông báo đã đọc.');
  }

  return res.json();
}

export async function markAllNotificationsAsRead(
  token: string | null
): Promise<MarkReadResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/notifications/read-all`, {
    method: 'PUT',
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Không thể đánh dấu tất cả đã đọc.');
  }

  return res.json();
}
