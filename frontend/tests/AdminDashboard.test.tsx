import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AdminDashboardView } from '../src/components/AdminDashboardView';
import { AuthProvider } from '../src/context/AuthContext';
import * as adminApi from '../src/services/adminDashboardApi';
import { authApi } from '../src/services/authApi';
import { AdminDashboardSummaryResponse } from '../src/types/adminDashboard';
import { User } from '../src/types/auth';

const mockLocalStorage: Record<string, string> = {};
beforeEach(() => {
  vi.restoreAllMocks();
  Object.keys(mockLocalStorage).forEach((k) => delete mockLocalStorage[k]);
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => mockLocalStorage[key] || null);
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation((key, val) => {
    mockLocalStorage[key] = val;
  });
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation((key) => {
    delete mockLocalStorage[key];
  });
});

const mockStaffUser: User = {
  id: 2,
  email: 'staff@novelia.vn',
  full_name: 'Trần Nhân Sự',
  phone: '0912345678',
  roles: ['STAFF'],
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockAdminUser: User = {
  id: 1,
  email: 'admin@novelia.vn',
  full_name: 'Nguyễn Quản Trị',
  phone: '0988776655',
  roles: ['ADMIN'],
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockSummaryResponse: AdminDashboardSummaryResponse = {
  kpis: {
    total_revenue: '4500000.00',
    collected_revenue: '3800000.00',
    has_cost_data: false,
    profit_note: 'Chưa có dữ liệu giá vốn nhập kho (COGS) để tính toán lợi nhuận ròng thực tế.',
    total_orders: 18,
    valid_orders_count: 15,
    average_order_value: '300000.00',
    total_books: 85,
    low_stock_count: 2,
    total_customers: 60,
    total_staff: 3,
    active_coupons_count: 3,
  },
  timeline: [
    { date_label: '2026-10-18', revenue: '1500000.00', collected_cash: '1200000.00', order_count: 5 },
    { date_label: '2026-10-19', revenue: '3000000.00', collected_cash: '2600000.00', order_count: 10 },
  ],
  status_breakdown: [
    { status: 'COMPLETED', label: 'Giao thành công', count: 12, percentage: 66.7, total_amount: '3200000.00' },
    { status: 'CANCELLED', label: 'Đã hủy', count: 3, percentage: 16.7, total_amount: '800000.00' },
  ],
  top_selling_books: [
    {
      book_id: 101,
      title: 'Nhà Giả Kim',
      isbn: '978-604-00-1111-1',
      sku: 'NVL-NGK-01',
      units_sold: 25,
      total_sales: '2500000.00',
      current_stock: 45,
    },
  ],
  low_stock_alerts: [
    {
      book_id: 202,
      title: 'Tuổi Trẻ Đáng Giá Bao Nhiêu',
      isbn: '978-604-00-2222-2',
      sku: 'NVL-TTDGBN-02',
      available_stock: 2,
      physical_stock: 5,
      reserved_stock: 3,
      low_stock_threshold: 5,
      is_out_of_stock: false,
    },
  ],
  recent_activities: [
    {
      id: 'act-1',
      activity_type: 'ORDER',
      title: 'Đơn hàng mới #ORD-999',
      description: 'Khách hàng vừa đặt đơn trị giá 350.000₫',
      severity: 'success',
      timestamp: new Date().toISOString(),
      reference_id: 'ORD-999',
    },
  ],
  filter_period: '30days',
};

describe('AdminDashboardView Component', () => {
  it('renders executive KPIs and enforces financial truthfulness (no fake profit)', async () => {
    mockLocalStorage['novelia_token'] = 'admin-token';
    vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockAdminUser);
    vi.spyOn(adminApi, 'fetchDashboardSummary').mockResolvedValue(mockSummaryResponse);

    render(
      <AuthProvider>
        <AdminDashboardView />
      </AuthProvider>
    );

    expect(await screen.findByText('Bảng Điều Hành Trung Tâm NOVELIA')).toBeInTheDocument();
    expect(await screen.findByText('Tổng Doanh thu Gộp')).toBeInTheDocument();
    expect(await screen.findByText('Tiền Thực thu (Dòng tiền)')).toBeInTheDocument();

    // Financial truth rule verification:
    expect(await screen.findByText('Chưa có dữ liệu COGS')).toBeInTheDocument();
    expect(
      screen.getByText(/Chưa có dữ liệu giá vốn nhập kho \(COGS\)/)
    ).toBeInTheDocument();

    // Best seller & low stock alert rendering
    expect(await screen.findByText('Nhà Giả Kim')).toBeInTheDocument();
    expect(await screen.findByText('Tuổi Trẻ Đáng Giá Bao Nhiêu')).toBeInTheDocument();
    expect(await screen.findByText('Tồn thấp')).toBeInTheDocument();
  });

  it('changes period filter and requests updated metrics', async () => {
    mockLocalStorage['novelia_token'] = 'admin-token';
    vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockAdminUser);
    const summarySpy = vi
      .spyOn(adminApi, 'fetchDashboardSummary')
      .mockResolvedValue(mockSummaryResponse);

    render(
      <AuthProvider>
        <AdminDashboardView />
      </AuthProvider>
    );

    expect(await screen.findByText('Bảng Điều Hành Trung Tâm NOVELIA')).toBeInTheDocument();

    // Click '7 ngày'
    const btn7Days = screen.getByRole('button', { name: '7 ngày' });
    fireEvent.click(btn7Days);

    await waitFor(() => {
      expect(summarySpy).toHaveBeenCalledWith('admin-token', '7days');
    });
  });

  it('restricts user governance tab for STAFF role with security banner', async () => {
    mockLocalStorage['novelia_token'] = 'staff-token';
    vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockStaffUser);
    vi.spyOn(adminApi, 'fetchDashboardSummary').mockResolvedValue(mockSummaryResponse);

    render(
      <AuthProvider>
        <AdminDashboardView />
      </AuthProvider>
    );

    expect(await screen.findByText('Bảng Điều Hành Trung Tâm NOVELIA')).toBeInTheDocument();

    // Click 'Khách hàng & Nhân sự' tab
    const usersTab = screen.getByRole('button', { name: /Khách hàng & Nhân sự/i });
    fireEvent.click(usersTab);

    // Enforce ADMIN only barrier
    expect(
      await screen.findByText('Yêu Cầu Quyền Quản Trị Viên (ADMIN)')
    ).toBeInTheDocument();
  });

  it('allows ADMIN to manage user governance, change roles and toggle status', async () => {
    mockLocalStorage['novelia_token'] = 'admin-token';
    vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockAdminUser);
    vi.spyOn(adminApi, 'fetchDashboardSummary').mockResolvedValue(mockSummaryResponse);
    vi.spyOn(adminApi, 'fetchAdminUsers').mockResolvedValue({
      items: [
        {
          id: 10,
          email: 'customer@gmail.com',
          full_name: 'Lê Khách Hàng',
          phone: '0909090909',
          is_active: true,
          roles: ['CUSTOMER'],
          orders_count: 4,
          total_spent: '850000.00',
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
      page: 1,
      page_size: 15,
      total_pages: 1,
    });
    vi.spyOn(adminApi, 'updateAdminUserStatus').mockResolvedValue({
      id: 10,
      email: 'customer@gmail.com',
      full_name: 'Lê Khách Hàng',
      is_active: false,
      roles: ['CUSTOMER'],
      orders_count: 4,
      total_spent: '850000.00',
      created_at: new Date().toISOString(),
    });

    // Mock confirm dialog
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <AuthProvider>
        <AdminDashboardView />
      </AuthProvider>
    );

    // Switch to Users tab
    const usersTab = await screen.findByRole('button', { name: /Khách hàng & Nhân sự/i });
    fireEvent.click(usersTab);

    expect(await screen.findByText('Tài Khoản Thành Viên (1)')).toBeInTheDocument();
    expect(screen.getByText('Lê Khách Hàng')).toBeInTheDocument();

    // Toggle user status
    const lockBtn = screen.getByRole('button', { name: /Khóa/i });
    fireEvent.click(lockBtn);

    await waitFor(() => {
      expect(adminApi.updateAdminUserStatus).toHaveBeenCalledWith('admin-token', 10, false);
    });
  });

  it('allows managing categories in Taxonomies tab', async () => {
    mockLocalStorage['novelia_token'] = 'staff-token';
    vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockStaffUser);
    vi.spyOn(adminApi, 'fetchDashboardSummary').mockResolvedValue(mockSummaryResponse);
    vi.spyOn(adminApi, 'fetchAdminCategories').mockResolvedValue([
      {
        id: 1,
        name: 'Văn Học Cổ Điển',
        slug: 'van-hoc-co-dien',
        books_count: 8,
        display_order: 1,
        created_at: new Date().toISOString(),
      },
    ]);
    vi.spyOn(adminApi, 'createAdminCategory').mockResolvedValue({
      id: 2,
      name: 'Kinh Tế & Đầu Tư',
      slug: 'kinh-te-dau-tu',
      books_count: 0,
      display_order: 2,
      created_at: new Date().toISOString(),
    });

    render(
      <AuthProvider>
        <AdminDashboardView />
      </AuthProvider>
    );

    const taxTab = await screen.findByRole('button', { name: /Danh mục & Phân loại/i });
    fireEvent.click(taxTab);

    expect(await screen.findByText('Danh Sách Danh Mục (1)')).toBeInTheDocument();
    expect(screen.getByText('Văn Học Cổ Điển')).toBeInTheDocument();

    // Fill form to add new category
    const nameInput = screen.getByPlaceholderText(/Ví dụ: Tiểu Thuyết Trinh Thám/);
    fireEvent.change(nameInput, { target: { value: 'Kinh Tế & Đầu Tư' } });

    const submitBtn = screen.getByRole('button', { name: /Lưu Danh Mục/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(adminApi.createAdminCategory).toHaveBeenCalled();
    });
  });
});
