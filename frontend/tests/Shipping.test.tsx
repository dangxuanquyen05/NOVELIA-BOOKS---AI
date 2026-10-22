import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AdminOrdersView } from '../src/components/AdminOrdersView';
import { OrderHistoryView } from '../src/components/OrderHistoryView';
import { AuthProvider } from '../src/context/AuthContext';
import * as commerceApi from '../src/services/commerceApi';
import * as shippingApi from '../src/services/shippingApi';
import { authApi } from '../src/services/authApi';
import { Order, PaginatedOrders } from '../src/types/commerce';
import { ShipmentDetail, ShippingProviderStatus } from '../src/types/shipping';
import { User } from '../src/types/auth';

const mockLocalStorage: Record<string, string> = {};
beforeEach(() => {
  vi.restoreAllMocks();
  Object.keys(mockLocalStorage).forEach((key) => delete mockLocalStorage[key]);
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
  full_name: 'Nhân viên Điều vận',
  phone: '0901234567',
  roles: ['STAFF'],
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockCustomerUser: User = {
  id: 10,
  email: 'customer@novelia.vn',
  full_name: 'Nguyễn Văn Đọc',
  phone: '0987654321',
  roles: ['CUSTOMER'],
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockOrderPendingDispatch: Order = {
  id: 101,
  order_code: 'NVL-20261020-001',
  user_id: 10,
  subtotal_amount: 250000,
  shipping_fee: 30000,
  discount_amount: 0,
  total_amount: 280000,
  status: 'CONFIRMED',
  recipient_name: 'Trần Thị Mai',
  recipient_phone: '0912345678',
  shipping_province: 'TP. Hồ Chí Minh',
  shipping_district: 'Quận 1',
  shipping_ward: 'Phường Bến Nghé',
  shipping_street_address: '123 Lê Lợi',
  payment_method: 'COD',
  payment_status: 'PENDING',
  items: [
    {
      id: 1,
      book_id: 5,
      book_title_snapshot: 'Nhà Giả Kim',
      book_isbn_snapshot: '9786045623456',
      book_sku_snapshot: 'BK-NHK-01',
      price_at_purchase: 125000,
      quantity: 2,
      subtotal: 250000,
      created_at: new Date().toISOString(),
    },
  ],
  created_at: '2026-10-20T08:00:00Z',
  updated_at: '2026-10-20T08:00:00Z',
};

const mockOrderWithShipment: Order = {
  id: 102,
  order_code: 'NVL-20261020-002',
  user_id: 10,
  subtotal_amount: 300000,
  shipping_fee: 35000,
  discount_amount: 0,
  total_amount: 335000,
  status: 'SHIPPING',
  recipient_name: 'Nguyễn Văn Đọc',
  recipient_phone: '0987654321',
  shipping_province: 'Hà Nội',
  shipping_district: 'Cầu Giấy',
  shipping_ward: 'Dịch Vọng Hậu',
  shipping_street_address: '10 Phạm Văn Đồng',
  payment_method: 'COD',
  payment_status: 'PENDING',
  shipment_carrier: 'GHN',
  shipment_tracking_code: 'GHN_NVL20261020002',
  shipment_status: 'IN_TRANSIT',
  items: [
    {
      id: 2,
      book_id: 6,
      book_title_snapshot: 'Tội Ác Và Trừng Phạt',
      book_isbn_snapshot: '9786045623999',
      book_sku_snapshot: 'BK-TAVTP-01',
      price_at_purchase: 300000,
      quantity: 1,
      subtotal: 300000,
      created_at: new Date().toISOString(),
    },
  ],
  created_at: '2026-10-20T07:30:00Z',
  updated_at: '2026-10-20T07:30:00Z',
};

const mockShipmentDetail: ShipmentDetail = {
  id: 1,
  order_id: 102,
  order_code: 'NVL-20261020-002',
  carrier: 'GHN',
  tracking_code: 'GHN_NVL20261020002',
  status: 'IN_TRANSIT',
  status_label: 'Đang vận chuyển',
  shipping_fee: 35000,
  estimated_delivery_date: '2026-10-22',
  dispatched_at: '2026-10-20T08:15:00Z',
  recipient_name: 'Nguyễn Văn Đọc',
  recipient_phone: '0987654321',
  shipping_address: '10 Phạm Văn Đồng, Dịch Vọng Hậu, Cầu Giấy, Hà Nội',
  events: [
    {
      id: 1,
      status: 'READY_TO_PICK',
      description: 'Đã tiếp nhận yêu cầu điều vận từ Novelia Books',
      location: 'Kho Novelia Books - Cầu Giấy',
      occurred_at: '2026-10-20T08:15:00Z',
    },
    {
      id: 2,
      status: 'IN_TRANSIT',
      description: 'Bưu tá GHN đã lấy hàng và đang luân chuyển tại bưu cục',
      location: 'Bưu cục GHN Cầu Giấy',
      occurred_at: '2026-10-20T09:30:00Z',
    },
  ],
  created_at: '2026-10-20T08:15:00Z',
};

const mockProviderStatuses: ShippingProviderStatus[] = [
  {
    carrier: 'GHN',
    environment: 'mock',
    is_live_ready: true,
    status_text: 'GHN adapter configured and operational',
    api_url: 'https://dev-online-gateway.ghn.vn/shiip/public-api',
    notes: 'GHN adapter configured and operational',
  },
  {
    carrier: 'GHTK',
    environment: 'mock',
    is_live_ready: true,
    status_text: 'GHTK adapter configured and operational',
    api_url: 'https://services.giaohangtietkiem.vn/services/shipment',
    notes: 'GHTK adapter configured and operational',
  },
];

describe('Phase 8 — Logistics & Shipping Integration UI', () => {
  it('AdminOrdersView displays carrier pills, provider status, and allows order dispatching', async () => {
    mockLocalStorage['novelia_token'] = 'valid-staff-jwt';
    vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockStaffUser);
    vi.spyOn(shippingApi, 'fetchShippingProvidersStatus').mockResolvedValue(mockProviderStatuses);

    const paginatedOrders: PaginatedOrders = {
      items: [mockOrderPendingDispatch, mockOrderWithShipment],
      total: 2,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.spyOn(commerceApi, 'fetchAdminOrders').mockResolvedValue(paginatedOrders);

    const dispatchMock = vi.spyOn(shippingApi, 'dispatchOrder').mockResolvedValue({
      ...mockShipmentDetail,
      tracking_code: 'GHN_NVL_DISPATCHED_NEW',
      carrier: 'GHN',
    });

    render(
      <AuthProvider>
        <AdminOrdersView />
      </AuthProvider>
    );

    // Verify orders are loaded
    await waitFor(() => {
      expect(screen.getByText('NVL-20261020-001')).toBeInTheDocument();
      expect(screen.getByText('NVL-20261020-002')).toBeInTheDocument();
    });

    // Check provider chips
    expect(screen.getByText(/GHN: SẴN SÀNG/i)).toBeInTheDocument();

    // Check order with shipment displays tracking pill
    expect(screen.getByText('GHN_NVL20261020002')).toBeInTheDocument();

    // Pending dispatch order has "Điều vận" button
    const dispatchBtn = screen.getByTestId('dispatch-btn-NVL-20261020-001');
    expect(dispatchBtn).toBeInTheDocument();

    // Click "Điều vận" to open modal
    fireEvent.click(dispatchBtn);

    expect(screen.getByTestId('dispatch-order-modal')).toBeInTheDocument();
    expect(screen.getByText(/Điều Vận & Tạo Vận Đơn — NVL-20261020-001/i)).toBeInTheDocument();

    // Submit dispatch
    const submitDispatchBtn = screen.getByTestId('confirm-dispatch-btn');
    fireEvent.click(submitDispatchBtn);

    await waitFor(() => {
      expect(dispatchMock).toHaveBeenCalledWith(
        'valid-staff-jwt',
        'NVL-20261020-001',
        expect.objectContaining({
          carrier: 'GHN',
          weight: 500,
          required_note: 'CHOXEMHANGKHONGTHU',
        })
      );
    });
  });

  it('AdminOrdersView opens tracking timeline modal with checkpoint history', async () => {
    mockLocalStorage['novelia_token'] = 'valid-staff-jwt';
    vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockStaffUser);
    vi.spyOn(shippingApi, 'fetchShippingProvidersStatus').mockResolvedValue(mockProviderStatuses);

    const paginatedOrders: PaginatedOrders = {
      items: [mockOrderWithShipment],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.spyOn(commerceApi, 'fetchAdminOrders').mockResolvedValue(paginatedOrders);
    const trackingMock = vi.spyOn(shippingApi, 'fetchOrderTracking').mockResolvedValue(mockShipmentDetail);

    render(
      <AuthProvider>
        <AdminOrdersView />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('NVL-20261020-002')).toBeInTheDocument();
    });

    const trackingBtn = screen.getByTestId('tracking-btn-NVL-20261020-002');
    fireEvent.click(trackingBtn);

    await waitFor(() => {
      expect(trackingMock).toHaveBeenCalledWith('valid-staff-jwt', 'NVL-20261020-002');
      expect(screen.getByTestId('tracking-detail-modal')).toBeInTheDocument();
    });

    // Check tracking checkpoint description and location
    expect(screen.getByText('Đã tiếp nhận yêu cầu điều vận từ Novelia Books')).toBeInTheDocument();
    expect(screen.getByText('Kho Novelia Books - Cầu Giấy')).toBeInTheDocument();
    expect(screen.getByText('Bưu tá GHN đã lấy hàng và đang luân chuyển tại bưu cục')).toBeInTheDocument();
  });

  it('OrderHistoryView shows shipment badge and allows customer to view delivery timeline', async () => {
    mockLocalStorage['novelia_token'] = 'valid-customer-jwt';
    vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomerUser);

    const customerOrders: PaginatedOrders = {
      items: [mockOrderWithShipment],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };
    vi.spyOn(commerceApi, 'fetchMyOrders').mockResolvedValue(customerOrders);
    const trackingMock = vi.spyOn(shippingApi, 'fetchOrderTracking').mockResolvedValue(mockShipmentDetail);

    render(
      <AuthProvider>
        <OrderHistoryView />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('NVL-20261020-002')).toBeInTheDocument();
    });

    // Verify carrier tracking pill is visible in order header
    expect(screen.getByText(/GHN: GHN_NVL20261020002/i)).toBeInTheDocument();

    // Verify "Hành trình đơn" button
    const trackBtn = screen.getByTestId('track-btn-NVL-20261020-002');
    expect(trackBtn).toBeInTheDocument();

    fireEvent.click(trackBtn);

    await waitFor(() => {
      expect(trackingMock).toHaveBeenCalledWith('valid-customer-jwt', 'NVL-20261020-002');
      expect(screen.getByTestId('customer-tracking-modal')).toBeInTheDocument();
    });

    // Verify timeline checkpoint details
    expect(screen.getByText('Tiến Độ Chuyển Phát')).toBeInTheDocument();
    expect(screen.getByText('Bưu cục GHN Cầu Giấy')).toBeInTheDocument();
  });

  it('Handles carrier blocked error gracefully when live integration credentials are not configured', async () => {
    mockLocalStorage['novelia_token'] = 'valid-staff-jwt';
    vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockStaffUser);
    vi.spyOn(shippingApi, 'fetchShippingProvidersStatus').mockResolvedValue([
      {
        carrier: 'GHN',
        environment: 'live',
        is_live_ready: false,
        status_text: 'BLOCKED: Live credentials required',
        api_url: 'https://online-gateway.ghn.vn/shiip/public-api',
        notes: 'LIVE INTEGRATION is BLOCKED: Missing live credentials.',
      },
    ]);

    const paginatedOrders: PaginatedOrders = {
      items: [mockOrderPendingDispatch],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.spyOn(commerceApi, 'fetchAdminOrders').mockResolvedValue(paginatedOrders);

    vi.spyOn(shippingApi, 'dispatchOrder').mockRejectedValue(
      new Error('LIVE INTEGRATION is BLOCKED: Thiếu GHN_TOKEN hoặc GHN_SHOP_ID cho môi trường live.')
    );

    render(
      <AuthProvider>
        <AdminOrdersView />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('NVL-20261020-001')).toBeInTheDocument();
    });

    // Provider chip indicates blocked
    expect(screen.getByText(/GHN: BLOCKED/i)).toBeInTheDocument();

    // Open dispatch modal
    fireEvent.click(screen.getByTestId('dispatch-btn-NVL-20261020-001'));
    expect(screen.getByTestId('dispatch-order-modal')).toBeInTheDocument();

    // Submit and verify graceful error banner
    fireEvent.click(screen.getByTestId('confirm-dispatch-btn'));

    await waitFor(() => {
      expect(
        screen.getByText(/LIVE INTEGRATION is BLOCKED: Thiếu GHN_TOKEN hoặc GHN_SHOP_ID cho môi trường live./i)
      ).toBeInTheDocument();
    });
  });
});
