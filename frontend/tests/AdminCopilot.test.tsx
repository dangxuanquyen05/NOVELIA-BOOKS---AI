import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { NoveliaAIAssistant } from '../src/components/NoveliaAIAssistant';
import * as aiApi from '../src/services/aiApi';
import * as authContext from '../src/context/AuthContext';
import * as commerceContext from '../src/context/CommerceContext';
import { AIChatResponse, AIHealthStatus } from '../src/types/ai';

const mockLocalStorage: Record<string, string> = {};

beforeEach(() => {
  vi.restoreAllMocks();
  Object.keys(mockLocalStorage).forEach((k) => delete mockLocalStorage[k]);
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation((k) => mockLocalStorage[k] || null);
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation((k, v) => {
    mockLocalStorage[k] = v;
  });
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation((k) => {
    delete mockLocalStorage[k];
  });
  Element.prototype.scrollIntoView = vi.fn();
});

const mockHealth: AIHealthStatus = {
  status: 'MOCK_READY',
  provider: 'mock',
  model: 'mock-gpt-v1',
  is_configured: true,
  details: 'Mock AI Provider đang sẵn sàng phục vụ.',
};

describe('Novelia AI Admin Copilot (Phase 10)', () => {
  const mockStaffUser = {
    id: 10,
    email: 'staff@novelia.vn',
    full_name: 'Nguyễn Quản Trị',
    roles: ['STAFF'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const setupMocks = (isStaff = true) => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: isStaff ? mockStaffUser : null,
      token: isStaff ? 'mock_staff_token' : null,
      isAuthenticated: isStaff,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
      clearError: vi.fn(),
    });

    vi.spyOn(commerceContext, 'useCommerce').mockReturnValue({
      cart: null,
      wishlist: null,
      cartCount: 0,
      wishlistCount: 0,
      cartLoading: false,
      cartError: null,
      isCartOpen: false,
      openCart: vi.fn(),
      closeCart: vi.fn(),
      isCheckoutOpen: false,
      openCheckout: vi.fn(),
      closeCheckout: vi.fn(),
      addToCart: vi.fn(),
      updateCartQuantity: vi.fn(),
      removeFromCart: vi.fn(),
      clearCart: vi.fn(),
      addToWishlist: vi.fn(),
      removeFromWishlist: vi.fn(),
      isInWishlist: vi.fn(),
      moveWishlistToCart: vi.fn(),
      refreshCart: vi.fn(),
      refreshWishlist: vi.fn(),
    });

    vi.spyOn(aiApi, 'fetchAIHealth').mockResolvedValue(mockHealth);
  };

  it('renders Admin Copilot badge and administrative greetings for STAFF user', async () => {
    setupMocks(true);

    render(<NoveliaAIAssistant />);

    const triggerBtn = screen.getByLabelText('Mở Trợ lý Novelia AI');
    fireEvent.click(triggerBtn);

    expect(screen.getByText('Admin Copilot')).toBeInTheDocument();
    expect(screen.getByText(/Novelia AI Admin Copilot/i)).toBeInTheDocument();
    expect(screen.getByText('📊 Báo cáo doanh thu & KPI')).toBeInTheDocument();
  });

  it('renders Two-Phase Confirmation preview card when mutating action is staged', async () => {
    setupMocks(true);

    const mockResponse: AIChatResponse = {
      session_uuid: 'nvl_sess_admin',
      message: 'Đã lập bản xem trước điều chỉnh tồn kho sách Nhà Giả Kim (+20 cuốn).',
      suggested_prompts: ['Xác nhận điều chỉnh'],
      structured_payload: {
        confirmation: {
          confirmation_token: 'confirm_inv_abc123',
          action_type: 'ADJUST_INVENTORY',
          message: 'Đã lập bản xem trước điều chỉnh tồn kho sách Nhà Giả Kim (+20 cuốn).',
          preview: {
            book_id: 1,
            book_title: 'Nhà Giả Kim',
            current_physical_stock: 50,
            delta: 20,
            proposed_physical_stock: 70,
            current_available_stock: 40,
            proposed_available_stock: 60,
            reason: 'Nhập bổ sung từ NXB',
          },
        },
      },
      created_at: new Date().toISOString(),
    };

    const sendSpy = vi.spyOn(aiApi, 'sendAIChat').mockResolvedValueOnce(mockResponse);

    render(<NoveliaAIAssistant />);
    fireEvent.click(screen.getByLabelText('Mở Trợ lý Novelia AI'));

    const input = screen.getByPlaceholderText(/Hỏi về sách, tồn kho, đơn hàng, ship.../i);
    fireEvent.change(input, { target: { value: 'Nhập thêm 20 cuốn Nhà Giả Kim' } });
    fireEvent.submit(input.closest('form')!);

    await waitFor(() => {
      expect(sendSpy).toHaveBeenCalled();
      expect(screen.getByText('Xác nhận thao tác Quản trị viên (Two-Phase Gate)')).toBeInTheDocument();
      expect(screen.getByText('Xác nhận thực thi thay đổi ngay')).toBeInTheDocument();
      expect(screen.getByText(/Biến động:/i)).toBeInTheDocument();
      expect(screen.getAllByText(/\+20 cuốn/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/70 cuốn/i)).toBeInTheDocument();
    });
  });

  it('invokes confirmAIAction when staff clicks confirmation button', async () => {
    setupMocks(true);

    const mockResponse: AIChatResponse = {
      session_uuid: 'nvl_sess_admin',
      message: 'Yêu cầu cập nhật giá sách.',
      suggested_prompts: [],
      structured_payload: {
        confirmation: {
          confirmation_token: 'confirm_bk_xyz789',
          action_type: 'UPDATE_BOOK',
          message: 'Đã lập bản xem trước cập nhật giá sách.',
          preview: {
            book_id: 2,
            current_title: 'Đắc Nhân Tâm',
            proposed_title: 'Đắc Nhân Tâm (Tái Bản)',
            current_price: 110000,
            proposed_price: 135000,
            proposed_status: 'ACTIVE',
          },
        },
      },
      created_at: new Date().toISOString(),
    };

    vi.spyOn(aiApi, 'sendAIChat').mockResolvedValueOnce(mockResponse);
    const confirmSpy = vi.spyOn(aiApi, 'confirmAIAction').mockResolvedValueOnce({
      success: true,
      action_type: 'UPDATE_BOOK',
      message: "Đã cập nhật thông tin sách 'Đắc Nhân Tâm' thành công.",
      details: { book_id: 2, price: 135000 },
      executed_at: new Date().toISOString(),
    });

    render(<NoveliaAIAssistant />);
    fireEvent.click(screen.getByLabelText('Mở Trợ lý Novelia AI'));

    const input = screen.getByPlaceholderText(/Hỏi về sách, tồn kho, đơn hàng, ship.../i);
    fireEvent.change(input, { target: { value: 'Sửa giá sách 2' } });
    fireEvent.submit(input.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText('Xác nhận thực thi thay đổi ngay')).toBeInTheDocument();
    });

    const confirmBtn = screen.getByText('Xác nhận thực thi thay đổi ngay');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalledWith('mock_staff_token', 'confirm_bk_xyz789');
      expect(screen.getByText(/Đã xác nhận & lưu chính thức vào cơ sở dữ liệu/i)).toBeInTheDocument();
    });
  });

  it('renders Sales Summary KPI widget accurately', async () => {
    setupMocks(true);

    const mockResponse: AIChatResponse = {
      session_uuid: 'nvl_sess_admin',
      message: 'Báo cáo doanh thu hôm nay.',
      suggested_prompts: [],
      structured_payload: {
        sales_summary: {
          total_revenue: 12500000,
          collected_revenue: 10000000,
          total_orders: 35,
          valid_orders_count: 30,
          average_order_value: 416667,
          total_customers: 90,
        },
      },
      created_at: new Date().toISOString(),
    };

    vi.spyOn(aiApi, 'sendAIChat').mockResolvedValueOnce(mockResponse);

    render(<NoveliaAIAssistant />);
    fireEvent.click(screen.getByLabelText('Mở Trợ lý Novelia AI'));

    const input = screen.getByPlaceholderText(/Hỏi về sách, tồn kho, đơn hàng, ship.../i);
    fireEvent.change(input, { target: { value: 'Báo cáo doanh thu' } });
    fireEvent.submit(input.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/Báo cáo Doanh thu & KPI \(MySQL\)/i)).toBeInTheDocument();
      expect(screen.getByText(/12\.500\.000 đ/i)).toBeInTheDocument();
      expect(screen.getByText(/10\.000\.000 đ/i)).toBeInTheDocument();
      expect(screen.getByText('30 đơn')).toBeInTheDocument();
    });
  });

  it('renders Low Stock Alerts widget', async () => {
    setupMocks(true);

    const mockResponse: AIChatResponse = {
      session_uuid: 'nvl_sess_admin',
      message: 'Danh sách sách sắp hết hàng.',
      suggested_prompts: [],
      structured_payload: {
        low_stock: {
          count: 1,
          low_stock_books: [
            {
              book_id: 3,
              title: 'Lập Trình Không Khó',
              isbn: '9780001112223',
              sku: 'SKU-003',
              physical_stock: 4,
              reserved_stock: 2,
              available_stock: 2,
              low_stock_threshold: 10,
            },
          ],
        },
      },
      created_at: new Date().toISOString(),
    };

    vi.spyOn(aiApi, 'sendAIChat').mockResolvedValueOnce(mockResponse);

    render(<NoveliaAIAssistant />);
    fireEvent.click(screen.getByLabelText('Mở Trợ lý Novelia AI'));

    const input = screen.getByPlaceholderText(/Hỏi về sách, tồn kho, đơn hàng, ship.../i);
    fireEvent.change(input, { target: { value: 'Sách sắp hết' } });
    fireEvent.submit(input.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/Sách chạm ngưỡng cảnh báo \(1\)/i)).toBeInTheDocument();
      expect(screen.getByText('Lập Trình Không Khó')).toBeInTheDocument();
      expect(screen.getByText(/Khả dụng: 2 \(Kho: 4\)/i)).toBeInTheDocument();
    });
  });
});
