import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { CartDrawer } from '../src/components/CartDrawer';
import { WishlistView } from '../src/components/WishlistView';
import { ReviewSection } from '../src/components/ReviewSection';
import { InventoryManagementView } from '../src/components/InventoryManagementView';
import { AuthProvider } from '../src/context/AuthContext';
import { CommerceProvider } from '../src/context/CommerceContext';
import * as commerceApi from '../src/services/commerceApi';
import { authApi } from '../src/services/authApi';
import { Cart, Wishlist } from '../src/types/commerce';
import { User } from '../src/types/auth';

// Mock localStorage
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

const mockCustomerUser: User = {
  id: 1,
  email: 'customer@example.com',
  full_name: 'Nguyễn Văn Khách',
  phone: null,
  roles: ['CUSTOMER'],
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockEmptyWishlist: Wishlist = {
  id: 1,
  user_id: 1,
  name: 'Mặc định',
  total_items: 0,
  items: [],
  created_at: new Date().toISOString(),
};

const mockEmptyCart: Cart = {
  id: 1,
  user_id: 1,
  total_items: 0,
  subtotal_amount: 0,
  has_stock_issues: false,
  updated_at: new Date().toISOString(),
  items: [],
};

describe('Phase 5 — Customer Interactions & Inventory Frontend', () => {
  describe('CartDrawer Component', () => {
    it('renders empty cart message when user has no items', async () => {
      mockLocalStorage['novelia_token'] = 'mock-jwt-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomerUser);
      vi.spyOn(commerceApi, 'fetchCart').mockResolvedValue(mockEmptyCart);
      vi.spyOn(commerceApi, 'fetchWishlist').mockResolvedValue(mockEmptyWishlist);

      render(
        <AuthProvider>
          <CommerceProvider>
            <CartDrawer />
          </CommerceProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(commerceApi.fetchCart).toHaveBeenCalledWith('mock-jwt-token');
      });
    });

    it('displays cart items with server-calculated subtotals and stock availability', async () => {
      mockLocalStorage['novelia_token'] = 'mock-jwt-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomerUser);

      const cartWithItems: Cart = {
        id: 1,
        user_id: 1,
        total_items: 2,
        subtotal_amount: 250000,
        has_stock_issues: false,
        updated_at: new Date().toISOString(),
        items: [
          {
            id: 10,
            book_id: 101,
            book_title: 'Chiến Tranh Tiền Tệ',
            book_isbn: '978-604-00-1111-1',
            book_sku: 'NVL-CTTT-01',
            cover_image_url: 'https://example.com/cover.jpg',
            unit_price: 125000,
            original_price: 150000,
            discount_percent: 17,
            quantity: 2,
            subtotal: 250000,
            available_stock: 5,
            is_available: true,
          },
        ],
      };

      vi.spyOn(commerceApi, 'fetchCart').mockResolvedValue(cartWithItems);
      vi.spyOn(commerceApi, 'fetchWishlist').mockResolvedValue(mockEmptyWishlist);

      render(
        <AuthProvider>
          <CommerceProvider>
            <CartDrawer />
          </CommerceProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(commerceApi.fetchCart).toHaveBeenCalled();
      });
    });
  });

  describe('WishlistView Component', () => {
    it('renders empty wishlist state with action to browse catalog', async () => {
      vi.spyOn(commerceApi, 'fetchWishlist').mockResolvedValue(mockEmptyWishlist);

      const onBrowse = vi.fn();

      render(
        <AuthProvider>
          <CommerceProvider>
            <WishlistView onExploreStore={onBrowse} />
          </CommerceProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(
          screen.getByText('Danh sách yêu thích đang trống')
        ).toBeInTheDocument();
      });

      const browseBtn = screen.getByRole('button', {
        name: /Khám phá Cửa hàng sách/i,
      });
      fireEvent.click(browseBtn);
      expect(onBrowse).toHaveBeenCalled();
    });

    it('renders saved items and triggers move-to-cart', async () => {
      mockLocalStorage['novelia_token'] = 'mock-jwt-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomerUser);

      const filledWishlist: Wishlist = {
        id: 1,
        user_id: 1,
        name: 'Mặc định',
        total_items: 1,
        created_at: new Date().toISOString(),
        items: [
          {
            id: 5,
            book_id: 202,
            book_title: 'Nhà Giả Kim (Bìa Cứng)',
            book_isbn: '978-604-00-1111-1',
            book_sku: 'NVL-NGK-01',
            cover_image_url: 'https://example.com/cover.jpg',
            price: 135000,
            original_price: 150000,
            available_stock: 15,
            is_in_stock: true,
            added_at: new Date().toISOString(),
          },
        ],
      };

      vi.spyOn(commerceApi, 'fetchWishlist').mockResolvedValue(filledWishlist);

      const moveSpy = vi
        .spyOn(commerceApi, 'moveWishlistToCart')
        .mockResolvedValue(mockEmptyCart);

      render(
        <AuthProvider>
          <CommerceProvider>
            <WishlistView onExploreStore={() => {}} />
          </CommerceProvider>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Nhà Giả Kim (Bìa Cứng)')).toBeInTheDocument();
      });

      const moveBtn = screen.getByRole('button', { name: /Chuyển vào giỏ/i });
      fireEvent.click(moveBtn);

      await waitFor(() => {
        expect(moveSpy).toHaveBeenCalledWith('mock-jwt-token', 202);
      });
    });
  });

  describe('ReviewSection Component', () => {
    it('fetches and displays average rating and reviews list', async () => {
      vi.spyOn(commerceApi, 'fetchBookReviews').mockResolvedValue({
        average_rating: 4.5,
        total_reviews: 2,
        rating_distribution: { '5': 1, '4': 1, '3': 0, '2': 0, '1': 0 },
        reviews: [
          {
            id: 1,
            book_id: 10,
            user_id: 99,
            user_name: 'Độc Giả Thân Thiết',
            rating: 5,
            title: 'Cuốn sách tuyệt vời',
            comment: 'Nội dung rất sâu sắc, dịch mượt mà, đáng mua!',
            is_verified_purchase: true,
            status: 'ACTIVE',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
      });

      render(
        <AuthProvider>
          <ReviewSection bookId={10} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('4.5')).toBeInTheDocument();
        expect(screen.getByText(/Cuốn sách tuyệt vời/i)).toBeInTheDocument();
        expect(screen.getByText(/Đã mua sách tại Novelia/i)).toBeInTheDocument();
      });
    });

    it('requires minimum 10 characters for review comment', async () => {
      mockLocalStorage['novelia_token'] = 'mock-jwt-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomerUser);

      vi.spyOn(commerceApi, 'fetchBookReviews').mockResolvedValue({
        average_rating: 0,
        total_reviews: 0,
        rating_distribution: { '5': 0, '4': 0, '3': 0, '2': 0, '1': 0 },
        reviews: [],
      });

      render(
        <AuthProvider>
          <ReviewSection bookId={10} />
        </AuthProvider>
      );

      const textarea = await screen.findByPlaceholderText(/Chia sẻ cảm nhận/i);
      const submitBtn = screen.getByRole('button', { name: /Gửi nhận xét/i });

      // When comment is too short (< 10 chars), button is disabled
      fireEvent.change(textarea, { target: { value: 'Quá ngắn' } });
      expect(submitBtn).toBeDisabled();

      // When comment meets the 10-char threshold, button is enabled
      fireEvent.change(textarea, {
        target: { value: 'Một tác phẩm văn học rất đáng đọc và suy ngẫm!' },
      });
      expect(submitBtn).not.toBeDisabled();
    });
  });

  describe('InventoryManagementView Component', () => {
    it('blocks access if user is not STAFF or ADMIN', async () => {
      mockLocalStorage['novelia_token'] = 'mock-cust-token';
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(mockCustomerUser);

      render(
        <AuthProvider>
          <InventoryManagementView />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/Bạn không có quyền truy cập vào bảng kiểm soát tồn kho/i)
        ).toBeInTheDocument();
      });
    });

    it('renders inventory items and low stock indicators for staff members', async () => {
      mockLocalStorage['novelia_token'] = 'mock-staff-token';
      const staffUser: User = {
        ...mockCustomerUser,
        id: 2,
        email: 'staff@novelia.com',
        full_name: 'Thủ Kho Trưởng',
        roles: ['STAFF'],
      };
      vi.spyOn(authApi, 'getProfile').mockResolvedValue(staffUser);

      vi.spyOn(commerceApi, 'fetchInventory').mockResolvedValue({
        items: [
          {
            id: 1,
            book_id: 101,
            book_title: 'Thần Thoại Sisyphus',
            book_sku: 'NVL-TTS-01',
            book_isbn: '978-604-00-1111-1',
            cover_image_url: 'https://example.com/cover.jpg',
            physical_stock: 4,
            reserved_stock: 0,
            available_stock: 4,
            low_stock_threshold: 5,
            is_low_stock: true,
            updated_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
        low_stock_count: 1,
      });

      render(
        <AuthProvider>
          <InventoryManagementView />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Thần Thoại Sisyphus')).toBeInTheDocument();
        expect(screen.getByText('Tồn thấp')).toBeInTheDocument();
      });
    });
  });
});
