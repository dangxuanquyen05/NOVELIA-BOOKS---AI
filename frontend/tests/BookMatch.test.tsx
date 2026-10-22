import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BookMatchSection } from '../src/components/BookMatchSection';
import * as recApi from '../src/services/recommendationApi';
import * as authContext from '../src/context/AuthContext';
import * as commerceContext from '../src/context/CommerceContext';
import { BookMatchResponse } from '../src/types/recommendation';

describe('BookMatch AI Personalized Recommendations (Phase 11)', () => {
  const mockUser = {
    id: 42,
    email: 'reader@novelia.vn',
    full_name: 'Nguyễn Đọc Sách',
    roles: ['CUSTOMER'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const mockPersonalizedResponse: BookMatchResponse = {
    user_id: 42,
    is_cold_start: false,
    algorithm: 'BOOKMATCH_HYBRID',
    total_candidates_analyzed: 15,
    recommendations: [
      {
        book_id: 1,
        title: 'Tư Duy Nhanh Và Chậm',
        slug: 'tu-duy-nhanh-va-cham',
        price: 189000,
        original_price: 220000,
        primary_author: 'Daniel Kahneman',
        cover_image_url: 'https://images.unsplash.com/thinking.jpg',
        category_id: 1,
        category_name: 'Tâm Lý Học',
        available_stock: 35,
        match_score: 0.952,
        algorithm_type: 'BOOKMATCH_AI',
        explanation: 'Phù hợp với sở thích đọc thể loại Tâm Lý Học và phân tích hành vi của bạn.',
        explanation_source: 'AI_GENERATED',
      },
      {
        book_id: 2,
        title: 'Kinh Tế Học Hài Hước',
        slug: 'kinh-te-hoc-hai-huoc',
        price: 145000,
        original_price: 165000,
        primary_author: 'Steven D. Levitt',
        cover_image_url: 'https://images.unsplash.com/freak.jpg',
        category_id: 2,
        category_name: 'Kinh Tế',
        available_stock: 12,
        match_score: 0.884,
        algorithm_type: 'BOOKMATCH_AI',
        explanation: 'Dựa trên việc bạn yêu thích các tác phẩm kinh tế tư duy phản biện.',
        explanation_source: 'RULE_BASED_FALLBACK',
      },
    ],
    taste_profile: {
      user_id: 42,
      is_cold_start: false,
      top_categories: [{ category_id: 1, name: 'Tâm Lý Học', weight: 6.0 }],
      top_authors: [{ author_id: 1, name: 'Daniel Kahneman', weight: 5.0 }],
      total_orders_analyzed: 3,
      total_reviews_analyzed: 2,
      total_wishlist_analyzed: 1,
    },
    generated_at: new Date().toISOString(),
    disclaimer: 'Gợi ý dựa trên phân tích sở thích đọc thực tế và tồn kho sẵn có.',
  };

  const mockColdStartResponse: BookMatchResponse = {
    user_id: null,
    is_cold_start: true,
    algorithm: 'TRENDING_POPULARITY',
    total_candidates_analyzed: 10,
    recommendations: [
      {
        book_id: 3,
        title: 'Nhà Giả Kim',
        slug: 'nha-gia-kim',
        price: 79000,
        original_price: 90000,
        primary_author: 'Paulo Coelho',
        cover_image_url: 'https://images.unsplash.com/alchemist.jpg',
        category_id: 3,
        category_name: 'Văn Học',
        available_stock: 50,
        match_score: 0.95,
        algorithm_type: 'TRENDING',
        explanation: 'Tác phẩm tiêu biểu được bạn đọc Novelia Books đánh giá cao nhất.',
        explanation_source: 'RULE_BASED_FALLBACK',
      },
    ],
    taste_profile: null,
    generated_at: new Date().toISOString(),
    disclaimer: 'Gợi ý dựa trên các tác phẩm bán chạy nhất toàn hệ thống.',
  };

  const setupMocks = (isLoggedIn = true, addToCartMock = vi.fn()) => {
    const authVal = {
      user: isLoggedIn ? mockUser : null,
      token: isLoggedIn ? 'mock_jwt_token' : null,
      isAuthenticated: isLoggedIn,
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

    const commerceVal = {
      cart: null,
      wishlist: null,
      cartCount: 2,
      wishlistCount: 1,
      cartLoading: false,
      cartError: null,
      isCartOpen: false,
      openCart: vi.fn(),
      closeCart: vi.fn(),
      isCheckoutOpen: false,
      openCheckout: vi.fn(),
      closeCheckout: vi.fn(),
      addToCart: addToCartMock,
      updateCartQuantity: vi.fn(),
      removeFromCart: vi.fn(),
      clearCart: vi.fn(),
      addToWishlist: vi.fn(),
      removeFromWishlist: vi.fn(),
      isInWishlist: vi.fn(),
      moveWishlistToCart: vi.fn(),
      refreshCart: vi.fn(),
      refreshWishlist: vi.fn(),
    };
    vi.spyOn(commerceContext, 'useCommerce').mockReturnValue(commerceVal);
    vi.spyOn(commerceContext, 'useSafeCommerce').mockReturnValue(commerceVal);
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders personalized recommendations and taste summary for authenticated user', async () => {
    setupMocks(true);
    vi.spyOn(recApi, 'fetchPersonalizedRecommendations').mockResolvedValueOnce(mockPersonalizedResponse);

    render(<BookMatchSection />);

    await waitFor(() => {
      expect(screen.getByText('BookMatch AI™ Cá Nhân Hóa')).toBeInTheDocument();
      expect(screen.getByText('Gợi Ý Dành Riêng Cho Gu Đọc Của Bạn')).toBeInTheDocument();
      expect(screen.getByText('Tư Duy Nhanh Và Chậm')).toBeInTheDocument();
      expect(screen.getByText('Daniel Kahneman')).toBeInTheDocument();
      expect(screen.getByText('189.000 đ')).toBeInTheDocument();
      expect(screen.getByText('95% Phù hợp')).toBeInTheDocument();
      expect(screen.getByText(/Phù hợp với sở thích đọc thể loại Tâm Lý Học/i)).toBeInTheDocument();
    });
  });

  it('renders trending cold-start state for unauthenticated guest visitor', async () => {
    setupMocks(false);
    vi.spyOn(recApi, 'fetchPersonalizedRecommendations').mockResolvedValueOnce(mockColdStartResponse);

    render(<BookMatchSection />);

    await waitFor(() => {
      expect(screen.getByText('Tuyển Tập Độc Giả Yêu Thích Nhất')).toBeInTheDocument();
      expect(screen.getByText('Nhà Giả Kim')).toBeInTheDocument();
      expect(screen.getByText('Paulo Coelho')).toBeInTheDocument();
      expect(screen.getByText('Thịnh hành')).toBeInTheDocument();
      expect(screen.getByText('Còn 50 cuốn')).toBeInTheDocument();
    });
  });

  it('triggers addToCart and sends telemetry event when user clicks Thêm giỏ', async () => {
    const addToCartMock = vi.fn().mockResolvedValue(undefined);
    setupMocks(true, addToCartMock);
    vi.spyOn(recApi, 'fetchPersonalizedRecommendations').mockResolvedValueOnce(mockPersonalizedResponse);
    const eventSpy = vi.spyOn(recApi, 'sendRecommendationEvent').mockResolvedValue({});

    render(<BookMatchSection />);

    await waitFor(() => {
      expect(screen.getByText('Tư Duy Nhanh Và Chậm')).toBeInTheDocument();
    });

    const addBtns = screen.getAllByText('Thêm giỏ');
    fireEvent.click(addBtns[0]);

    await waitFor(() => {
      expect(addToCartMock).toHaveBeenCalledWith(1, 1);
      expect(eventSpy).toHaveBeenCalledWith('mock_jwt_token', expect.objectContaining({
        book_id: 1,
        event_type: 'ADD_TO_CART',
      }));
    });
  });

  it('triggers onSelectBook callback when user clicks a recommendation card', async () => {
    setupMocks(true);
    vi.spyOn(recApi, 'fetchPersonalizedRecommendations').mockResolvedValueOnce(mockPersonalizedResponse);
    const onSelectMock = vi.fn();
    const eventSpy = vi.spyOn(recApi, 'sendRecommendationEvent').mockResolvedValue({});

    render(<BookMatchSection onSelectBook={onSelectMock} />);

    await waitFor(() => {
      expect(screen.getByText('Tư Duy Nhanh Và Chậm')).toBeInTheDocument();
    });

    const cardTitle = screen.getByText('Tư Duy Nhanh Và Chậm');
    fireEvent.click(cardTitle);

    expect(onSelectMock).toHaveBeenCalledWith(1);
    expect(eventSpy).toHaveBeenCalledWith('mock_jwt_token', expect.objectContaining({
      book_id: 1,
      event_type: 'CLICK',
    }));
  });

  it('re-fetches recommendations when Làm mới gợi ý button is clicked', async () => {
    setupMocks(true);
    const fetchSpy = vi.spyOn(recApi, 'fetchPersonalizedRecommendations')
      .mockResolvedValue(mockPersonalizedResponse);

    render(<BookMatchSection />);

    await waitFor(() => {
      expect(screen.getByText('Tư Duy Nhanh Và Chậm')).toBeInTheDocument();
    });

    const refreshBtn = screen.getByText('Làm mới gợi ý');
    fireEvent.click(refreshBtn);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(2);
    });
  });
});
