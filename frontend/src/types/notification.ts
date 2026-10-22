/**
 * Notification types for Novelia Books In-App Alerts.
 */

export type NotificationType = 'ORDER' | 'SHIPPING' | 'PROMOTION' | 'SYSTEM' | 'INVENTORY';

export interface NotificationItem {
  id: number;
  user_id: number;
  title: string;
  message: string;
  notification_type: NotificationType;
  reference_link?: string | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  unread_count: number;
  page: number;
  limit: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface MarkReadResponse {
  success: boolean;
  marked_count: number;
  message: string;
}
