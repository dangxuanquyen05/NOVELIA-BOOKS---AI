import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { CheckoutModal } from '../src/components/CheckoutModal';
import { OrderHistoryView } from '../src/components/OrderHistoryView';
import { AdminOrdersView } from '../src/components/AdminOrdersView';
import { AuthProvider } from '../src/context/AuthContext';
import { CommerceProvider } from '../src/context/CommerceContext';
import * as commerceApi from '../src/services/commerceApi';
import { authApi } from '../src/services/authApi';
import { Cart, Order, PaginatedOrders, CouponValidationResult } from '../src/types/commerce';
import { User, Address } from '../src/types/auth';

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

const mockCustomer: User = {
  id: 10,
  email: 'reader@novelia.vn',
  full_name: 'Nguyễn Văn Đọc',
  phone: '0987654321',
  roles: ['CUSTOMER'],
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockAddress: Address = {
  id: 1,
  user_id: 10,
  recipient_name: 'Nguyễn Văn Đọc',
  phone: '0987654321',
  province_name: 'Hà Nội',
  province_code: '01',
  district_name: 'Cầu Giấy',
  district_code: '005',
  ward_name: 'Dịch Vọng Hậu',
  ward_code: '001',
  street_address: 'Số 10 Phạm Văn Đồng',
  is_default: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockCartWithItems: Cart = {
  id: 1,
  user_id: 10,
  total_items: 2,
  subtotal_amount: 240000,
  has_stock_issues: false,
  updated_at: new Date().toISOString(),
  items: [
    {
      id: 1,
      book_id: 101,
      book_title: 'Nhà Giả Kim',
      book_isbn: '978-604-00-1111-1',
      book_sku: 'NVL-NGK-01',
      cover_image_url: 'https://images.unsplash.com/photo-1',
      unit_price: 120000,
      original_price: 150000,
      discount_percent: 20,
      quantity: 2,
      subtotal: 240000,
      available_stock: 10,
      is_available: true,
    },
  ],
};

const mockCreatedOrder: Order = {
  id: 100,
  order_code: 'NVL-20261020-ABC123',
  user_id: 10,
  subtotal_amount: 240000,
  shipping_fee: 30000,
  discount_amount: 0,
  total_amount: 270000,
  status: 'CONFIRMED',
  recipient_name: 'Nguyễn Văn Đọc',
  recipient_phone: '0987654321',
  shipping_province: 'Hà Nội',
  shipping_district: 'Cầu Giấy',
  shipping_ward: 'Dịch Vọng Hậu',
  shipping_street_address: 'Số 10 Phạm Văn Đồng',
  customer_notes: 'Giao giờ hành chính',
  payment_method: 'COD',
  payment_status: 'PENDING',
  items: [
    {
      id: 1,
      book_id: 101,
      book_title_snapshot: 'Nhà Giả Kim',
      book_isbn_snapshot: '978-604-00-1111-1',
      book_sku_snapshot: 'NVL-NGK-01',
      price_at_purchase: 120000,
      quantity: 2,
      subtotal: 240000,
      created_at: new Date().toISOString(),
    },
  ],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe('Phase 6 — Checkout, Orders & Payment Abstraction', () => {
  describe('CheckoutModal Component', () => {
    it('renders checkout modal with delivery fields, payment methods, and summary', async () => {
      mockLocalStorage['novelia_token'] = 'test-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomer);
      vi.spyOn(authApi, 'listAddresses').mockResolvedValue([mockAddress]);
      vi.spyOn(commerceApi, 'fetchCart').mockResolvedValue(mockCartWithItems);

      render(
        <AuthProvider>
          <CommerceProvider>
            <CheckoutModal
              isOpen={true}
              onClose={vi.fn()}
              onOrderSuccess={vi.fn()}
            />
          </CommerceProvider>
        </AuthProvider>
      );

      expect(await screen.findByText('Hoàn Tất Đặt Hàng')).toBeInTheDocument();
      expect(screen.getByText('1. Thông tin giao hàng')).toBeInTheDocument();
      expect(screen.getByText('2. Phương thức thanh toán')).toBeInTheDocument();
      expect(screen.getByText('COD — Tiền mặt khi nhận hàng')).toBeInTheDocument();
      expect(screen.getByText('VNPAY Sandbox (Mô phỏng QR & Thẻ)')).toBeInTheDocument();
      expect(screen.getByText('MOCK Gateway (Ký số Sandbox)')).toBeInTheDocument();
      expect(screen.getByText('Xác nhận & Đặt hàng ngay')).toBeInTheDocument();
    });

    it('validates and applies coupon code successfully', async () => {
      mockLocalStorage['novelia_token'] = 'test-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomer);
      vi.spyOn(authApi, 'listAddresses').mockResolvedValue([mockAddress]);
      vi.spyOn(commerceApi, 'fetchCart').mockResolvedValue(mockCartWithItems);

      const couponRes: CouponValidationResult = {
        is_valid: true,
        code: 'GIAM20',
        discount_type: 'PERCENTAGE',
        discount_value: 20,
        discount_amount: 48000,
        min_order_value: 200000,
        message: 'Áp dụng mã giảm giá 20% thành công!',
      };
      vi.spyOn(commerceApi, 'validateCoupon').mockResolvedValue(couponRes);

      render(
        <AuthProvider>
          <CommerceProvider>
            <CheckoutModal
              isOpen={true}
              onClose={vi.fn()}
              onOrderSuccess={vi.fn()}
            />
          </CommerceProvider>
        </AuthProvider>
      );

      await screen.findByText('Hoàn Tất Đặt Hàng');
      expect(await screen.findByText('Nhà Giả Kim')).toBeInTheDocument();
      const couponInput = screen.getByPlaceholderText('VD: GIAM20, NOVELIA10');
      fireEvent.change(couponInput, { target: { value: 'GIAM20' } });

      const applyBtn = screen.getByText('Áp dụng');
      fireEvent.click(applyBtn);

      await waitFor(() => {
        expect(commerceApi.validateCoupon).toHaveBeenCalledWith('GIAM20', 240000, 'test-token');
      });

      expect(await screen.findByText(/Áp dụng thành công mã/)).toBeInTheDocument();
      expect(screen.getByText('Gỡ bỏ')).toBeInTheDocument();
    });

    it('submits checkout and displays order confirmation on success', async () => {
      mockLocalStorage['novelia_token'] = 'test-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomer);
      vi.spyOn(authApi, 'listAddresses').mockResolvedValue([mockAddress]);
      vi.spyOn(commerceApi, 'fetchCart').mockResolvedValue(mockCartWithItems);
      vi.spyOn(commerceApi, 'checkoutOrder').mockResolvedValue(mockCreatedOrder);

      const onOrderSuccess = vi.fn();

      render(
        <AuthProvider>
          <CommerceProvider>
            <CheckoutModal
              isOpen={true}
              onClose={vi.fn()}
              onOrderSuccess={onOrderSuccess}
            />
          </CommerceProvider>
        </AuthProvider>
      );

      await screen.findByText('Hoàn Tất Đặt Hàng');
      const submitBtn = screen.getByText('Xác nhận & Đặt hàng ngay');
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(commerceApi.checkoutOrder).toHaveBeenCalled();
      });

      expect(await screen.findByText('Đặt Hàng Thành Công!')).toBeInTheDocument();
      expect(screen.getByText('NVL-20261020-ABC123')).toBeInTheDocument();
      expect(onOrderSuccess).toHaveBeenCalledWith(mockCreatedOrder);
    });
  });

  describe('OrderHistoryView Component', () => {
    it('displays customer orders and line items', async () => {
      mockLocalStorage['novelia_token'] = 'test-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomer);
      const ordersResp: PaginatedOrders = {
        items: [
          {
            ...mockCreatedOrder,
            status: 'PENDING',
          },
        ],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };
      vi.spyOn(commerceApi, 'fetchMyOrders').mockResolvedValue(ordersResp);

      render(
        <AuthProvider>
          <OrderHistoryView />
        </AuthProvider>
      );

      expect(await screen.findByText('Đơn Hàng Của Tôi')).toBeInTheDocument();
      expect(await screen.findByText('NVL-20261020-ABC123')).toBeInTheDocument();
      expect(screen.getByText('Nhà Giả Kim')).toBeInTheDocument();
      expect(screen.getByText('Hủy đơn hàng')).toBeInTheDocument();
    });

    it('cancels pending order when customer submits cancellation reason', async () => {
      mockLocalStorage['novelia_token'] = 'test-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomer);
      const pendingOrder: Order = {
        ...mockCreatedOrder,
        status: 'PENDING',
      };
      vi.spyOn(commerceApi, 'fetchMyOrders').mockResolvedValue({
        items: [pendingOrder],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      });

      const cancelledOrder: Order = {
        ...pendingOrder,
        status: 'CANCELLED',
        cancelled_reason: 'Đặt nhầm địa chỉ',
      };
      vi.spyOn(commerceApi, 'cancelOrder').mockResolvedValue(cancelledOrder);

      render(
        <AuthProvider>
          <OrderHistoryView />
        </AuthProvider>
      );

      const cancelBtn = await screen.findByTestId('cancel-btn-NVL-20261020-ABC123');
      fireEvent.click(cancelBtn);

      expect(await screen.findByTestId('cancel-order-modal')).toBeInTheDocument();

      const reasonInput = screen.getByPlaceholderText(/Tôi muốn thay đổi địa chỉ/);
      fireEvent.change(reasonInput, { target: { value: 'Đặt nhầm địa chỉ nhận hàng' } });

      const confirmBtn = screen.getByTestId('confirm-cancel-btn');
      fireEvent.click(confirmBtn);

      await waitFor(() => {
        expect(commerceApi.cancelOrder).toHaveBeenCalledWith(
          'test-token',
          'NVL-20261020-ABC123',
          'Đặt nhầm địa chỉ nhận hàng'
        );
      });
    });
  });

  describe('AdminOrdersView Component', () => {
    it('renders admin orders table and updates order status', async () => {
      mockLocalStorage['novelia_token'] = 'test-token';
      const staffUser: User = {
        ...mockCustomer,
        roles: ['STAFF'],
      };
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(staffUser);
      vi.spyOn(commerceApi, 'fetchAdminOrders').mockResolvedValue({
        items: [mockCreatedOrder],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      });

      const shippedOrder: Order = {
        ...mockCreatedOrder,
        status: 'SHIPPING',
      };
      vi.spyOn(commerceApi, 'updateOrderStatus').mockResolvedValue(shippedOrder);

      render(
        <AuthProvider>
          <AdminOrdersView />
        </AuthProvider>
      );

      expect(await screen.findByText('Quản Trị Đơn Hàng & Điều Vận (Backoffice)')).toBeInTheDocument();
      expect(await screen.findByText('NVL-20261020-ABC123')).toBeInTheDocument();

      const manageBtn = screen.getByTestId('manage-btn-NVL-20261020-ABC123');
      fireEvent.click(manageBtn);

      expect(await screen.findByTestId('admin-status-modal')).toBeInTheDocument();

      const saveBtn = screen.getByTestId('save-status-btn');
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(commerceApi.updateOrderStatus).toHaveBeenCalled();
      });
    });
  });
});
