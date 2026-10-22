import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { NotificationCenter } from '../src/components/NotificationCenter';
import { AdminAuditView } from '../src/components/AdminAuditView';
import * as notifApi from '../src/services/notificationApi';
import * as auditApi from '../src/services/auditApi';
import * as authContext from '../src/context/AuthContext';
import { NotificationListResponse } from '../src/types/notification';
import {
  AuditLogListResponse,
  AIActionLogListResponse,
  EmailStatusResponse,
} from '../src/types/audit';

describe('Notifications & Audit Governance (Phase 12)', () => {
  const mockUser = {
    id: 42,
    email: 'reader@novelia.vn',
    full_name: 'Nguyễn Đọc Sách',
    roles: ['CUSTOMER'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const mockStaff = {
    id: 99,
    email: 'staff@novelia.vn',
    full_name: 'Quản Trị Viên',
    roles: ['STAFF', 'ADMIN'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const mockNotifications: NotificationListResponse = {
    items: [
      {
        id: 1,
        user_id: 42,
        title: 'Đơn hàng đã được xác nhận #NVL-001',
        message: 'Đơn hàng NVL-001 của bạn đã được xác nhận và chuẩn bị xuất kho.',
        notification_type: 'ORDER',
        reference_link: '/orders/NVL-001',
        is_read: false,
        read_at: null,
        created_at: new Date().toISOString(),
      },
      {
        id: 2,
        user_id: 42,
        title: 'Vận chuyển đơn hàng #NVL-001',
        message: 'Bưu kiện GHN12345 đang trên đường giao đến bạn.',
        notification_type: 'SHIPPING',
        reference_link: '/orders/NVL-001',
        is_read: false,
        read_at: null,
        created_at: new Date().toISOString(),
      },
      {
        id: 3,
        user_id: 42,
        title: 'Khuyến mãi mùa sách mới',
        message: 'Giảm giá 15% cho toàn bộ sách triết học.',
        notification_type: 'PROMOTION',
        reference_link: null,
        is_read: true,
        read_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      },
    ],
    total: 3,
    unread_count: 2,
    page: 1,
    limit: 20,
  };

  const mockAuditLogs: AuditLogListResponse = {
    items: [
      {
        id: 101,
        user_id: 99,
        user_email: 'staff@novelia.vn',
        user_role: 'ADMIN',
        action: 'ORDER_STATUS_UPDATE',
        entity_type: 'ORDER',
        entity_id: 'NVL-001',
        old_values: { status: 'CONFIRMED' },
        new_values: { status: 'SHIPPING', staff_notes: 'Xuất kho' },
        ip_address: '127.0.0.1',
        user_agent: 'Mozilla/5.0',
        created_at: new Date().toISOString(),
      },
      {
        id: 102,
        user_id: 99,
        user_email: 'staff@novelia.vn',
        user_role: 'ADMIN',
        action: 'USER_ROLE_CHANGE',
        entity_type: 'USER',
        entity_id: '42',
        old_values: { role: 'CUSTOMER', password_hash: '***REDACTED***' },
        new_values: { role: 'STAFF', token: '***REDACTED***' },
        ip_address: '127.0.0.1',
        user_agent: 'Mozilla/5.0',
        created_at: new Date().toISOString(),
      },
    ],
    total: 2,
    page: 1,
    limit: 15,
  };

  const mockAiLogs: AIActionLogListResponse = {
    items: [
      {
        id: 201,
        conversation_id: 1,
        user_id: 99,
        user_email: 'staff@novelia.vn',
        user_role: 'STAFF',
        tool_name: 'get_sales_summary',
        input_arguments: { period: '30days' },
        execution_status: 'SUCCESS',
        confirmation_token: null,
        is_confirmed: false,
        output_summary: 'Doanh thu gộp 25.000.000 đ',
        execution_duration_ms: 45,
        created_at: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    limit: 15,
  };

  const mockEmailStatus: EmailStatusResponse = {
    provider: 'MOCK',
    is_mock: true,
    status: 'HEALTHY',
    details: { total_sent: 5 },
  };

  const setupAuth = (user = mockUser) => {
    const authVal = {
      user,
      token: 'mock_jwt_token',
      isAuthenticated: true,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
      clearError: vi.fn(),
    };
    vi.spyOn(authContext, 'useAuth').mockReturnValue(authVal);
    vi.spyOn(authContext, 'useSafeAuth').mockReturnValue(authVal);
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders NotificationCenter bell button with unread badge counter', async () => {
    setupAuth(mockUser);
    vi.spyOn(notifApi, 'fetchUnreadCount').mockResolvedValue({ unread_count: 2 });

    render(<NotificationCenter />);

    const badge = await screen.findByTestId('unread-badge');
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toBe('2');
  });

  it('opens notification dropdown on bell click and renders items', async () => {
    setupAuth(mockUser);
    vi.spyOn(notifApi, 'fetchUnreadCount').mockResolvedValue({ unread_count: 2 });
    vi.spyOn(notifApi, 'fetchNotifications').mockResolvedValue(mockNotifications);

    render(<NotificationCenter />);

    const bellBtn = screen.getByLabelText('Thông báo');
    fireEvent.click(bellBtn);

    const dropdown = await screen.findByTestId('notification-dropdown');
    expect(dropdown).toBeInTheDocument();

    expect(await screen.findByText('Đơn hàng đã được xác nhận #NVL-001')).toBeInTheDocument();
    expect(screen.getByText('Vận chuyển đơn hàng #NVL-001')).toBeInTheDocument();
  });

  it('marks a notification as read and calls markAllNotificationsAsRead', async () => {
    setupAuth(mockUser);
    vi.spyOn(notifApi, 'fetchUnreadCount').mockResolvedValue({ unread_count: 2 });
    vi.spyOn(notifApi, 'fetchNotifications').mockResolvedValue(mockNotifications);
    const markOneSpy = vi.spyOn(notifApi, 'markNotificationAsRead').mockResolvedValue(mockNotifications.items[0]);
    const markAllSpy = vi.spyOn(notifApi, 'markAllNotificationsAsRead').mockResolvedValue({
      success: true,
      marked_count: 2,
      message: 'Đã đánh dấu 2 thông báo',
    });

    render(<NotificationCenter />);

    fireEvent.click(screen.getByLabelText('Thông báo'));

    // Click single notification
    const notifItem = await screen.findByText('Đơn hàng đã được xác nhận #NVL-001');
    fireEvent.click(notifItem);

    await waitFor(() => {
      expect(markOneSpy).toHaveBeenCalledWith('mock_jwt_token', 1);
    });

    // Click "Đã đọc hết"
    const markAllBtn = screen.getByTitle('Đánh dấu tất cả đã đọc');
    fireEvent.click(markAllBtn);

    await waitFor(() => {
      expect(markAllSpy).toHaveBeenCalledWith('mock_jwt_token');
    });
  });

  it('renders AdminAuditView with email provider status badge and audit logs table', async () => {
    setupAuth(mockStaff);
    vi.spyOn(auditApi, 'fetchEmailStatus').mockResolvedValue(mockEmailStatus);
    vi.spyOn(auditApi, 'fetchAuditLogs').mockResolvedValue(mockAuditLogs);
    vi.spyOn(auditApi, 'fetchAIActionLogs').mockResolvedValue(mockAiLogs);

    render(<AdminAuditView />);

    // Check email provider banner declares mock adapter
    const emailBadge = await screen.findByTestId('email-provider-badge');
    expect(emailBadge).toBeInTheDocument();
    expect(emailBadge.textContent).toContain('MOCK ADAPTER');

    // Check System Audit table rows (matches both filter option and table cell badge)
    const orderStatusBadges = await screen.findAllByText('ORDER_STATUS_UPDATE');
    expect(orderStatusBadges.length).toBeGreaterThanOrEqual(1);

    const userRoleBadges = screen.getAllByText('USER_ROLE_CHANGE');
    expect(userRoleBadges.length).toBeGreaterThanOrEqual(1);
  });

  it('switches between System Audit and AI Actions tabs in AdminAuditView', async () => {
    setupAuth(mockStaff);
    vi.spyOn(auditApi, 'fetchEmailStatus').mockResolvedValue(mockEmailStatus);
    vi.spyOn(auditApi, 'fetchAuditLogs').mockResolvedValue(mockAuditLogs);
    vi.spyOn(auditApi, 'fetchAIActionLogs').mockResolvedValue(mockAiLogs);

    render(<AdminAuditView />);

    // Switch to AI tab
    const aiTabBtn = screen.getByTestId('tab-ai-actions');
    fireEvent.click(aiTabBtn);

    // AI Action tool appears
    expect(await screen.findByText('get_sales_summary')).toBeInTheDocument();
  });
});
