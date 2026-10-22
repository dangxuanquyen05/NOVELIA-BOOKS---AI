import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import App from '../src/App';
import { BookCard } from '../src/components/BookCard';
import { BookDetailModal } from '../src/components/BookDetailModal';
import { FilterSidebar } from '../src/components/FilterSidebar';
import { CatalogStorefront } from '../src/components/CatalogStorefront';
import { BookSummary, BookDetail, Category } from '../src/types/catalog';

const MOCK_BOOK: BookSummary = {
  id: 1,
  isbn: '9786045622544',
  sku: 'NOV-NGK-01',
  title: 'Nhà Giả Kim',
  slug: 'nha-gia-kim',
  price: 79000,
  original_price: 95000,
  discount_percent: 17,
  cover_image_url: 'https://images.novelia.vn/books/nhagiakim.jpg',
  cover_type: 'PAPERBACK',
  status: 'ACTIVE',
  primary_author: 'Paulo Coelho',
  authors: [
    {
      author_id: 1,
      name: 'Paulo Coelho',
      slug: 'paulo-coelho',
      is_primary: true,
      order_index: 0,
    },
  ],
  categories: [
    {
      category_id: 1,
      name: 'Văn Học Kinh Điển',
      slug: 'van-hoc-kinh-dien',
    },
  ],
  stock_available: 42,
  is_in_stock: true,
  created_at: '2026-01-01T00:00:00Z',
};

const MOCK_CATEGORIES: Category[] = [
  {
    id: 1,
    name: 'Văn Học Kinh Điển',
    slug: 'van-hoc-kinh-dien',
    display_order: 1,
    created_at: '2026-01-01T00:00:00Z',
    book_count: 15,
    subcategories: [],
  },
  {
    id: 2,
    name: 'Kinh Tế & Kinh Doanh',
    slug: 'kinh-te-kinh-doanh',
    display_order: 2,
    created_at: '2026-01-01T00:00:00Z',
    book_count: 8,
    subcategories: [],
  },
];

describe('NOVELIA BOOKS — Phase 4 Book Catalog & Storefront UI', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('BookCard Component', () => {
    it('renders book metadata, pricing, badges, and stock availability', () => {
      const handleSelect = vi.fn();
      render(<BookCard book={MOCK_BOOK} onSelect={handleSelect} />);

      expect(screen.getByText('Nhà Giả Kim')).toBeInTheDocument();
      expect(screen.getByText('Paulo Coelho')).toBeInTheDocument();
      expect(screen.getByText('Văn Học Kinh Điển')).toBeInTheDocument();
      expect(screen.getByText('-17%')).toBeInTheDocument();
      expect(screen.getByText('Bìa mềm')).toBeInTheDocument();
      expect(screen.getByText(/Còn hàng \(42\)/i)).toBeInTheDocument();

      // Click card
      fireEvent.click(screen.getByTestId('book-card-1'));
      expect(handleSelect).toHaveBeenCalledWith(MOCK_BOOK);
    });

    it('renders out-of-stock badge when is_in_stock is false', () => {
      const outOfStockBook: BookSummary = {
        ...MOCK_BOOK,
        id: 2,
        stock_available: 0,
        is_in_stock: false,
      };
      render(<BookCard book={outOfStockBook} onSelect={vi.fn()} />);
      expect(screen.getByText(/Tạm hết hàng/i)).toBeInTheDocument();
    });
  });

  describe('FilterSidebar Component', () => {
    it('handles search submission and price presets', () => {
      const handleFilterChange = vi.fn();
      const handleReset = vi.fn();

      render(
        <FilterSidebar
          categories={MOCK_CATEGORIES}
          filters={{ page: 1, page_size: 12 }}
          onFilterChange={handleFilterChange}
          onReset={handleReset}
        />
      );

      // Search input
      const input = screen.getByPlaceholderText(/Tìm theo tên, ISBN, tác giả.../i);
      fireEvent.change(input, { target: { value: 'Paulo' } });
      fireEvent.click(screen.getByRole('button', { name: 'Tìm' }));
      expect(handleFilterChange).toHaveBeenCalledWith({ query: 'Paulo', page: 1 });

      // Price preset click
      const priceBtn = screen.getByRole('button', { name: 'Dưới 100.000 ₫' });
      fireEvent.click(priceBtn);
      expect(handleFilterChange).toHaveBeenCalledWith({
        min_price: undefined,
        max_price: 100000,
        page: 1,
      });

      // Reset button
      const resetBtn = screen.getByRole('button', { name: /Đặt lại/i });
      fireEvent.click(resetBtn);
      expect(handleReset).toHaveBeenCalled();
    });
  });

  describe('BookDetailModal Component', () => {
    it('fetches full detail, displays specifications and toggles tabs', async () => {
      const mockDetail: BookDetail = {
        ...MOCK_BOOK,
        publisher: {
          id: 1,
          name: 'NXB Hội Nhà Văn',
          slug: 'nxb-hoi-nha-van',
          created_at: '2026-01-01T00:00:00Z',
        },
        page_count: 228,
        dimension: '13 x 20.5 cm',
        weight_grams: 280,
        description: 'Câu chuyện phiêu lưu thần thoại đầy chiêm nghiệm.',
        sample_text: 'Khi bạn khao khát một điều gì đó...',
        images: [],
        updated_at: '2026-01-01T00:00:00Z',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockDetail),
      });

      const handleClose = vi.fn();
      render(<BookDetailModal book={MOCK_BOOK} onClose={handleClose} />);

      await waitFor(() => {
        expect(screen.getByText('NXB Hội Nhà Văn')).toBeInTheDocument();
        expect(screen.getByText('228 trang')).toBeInTheDocument();
        expect(screen.getByText('13 x 20.5 cm')).toBeInTheDocument();
        expect(screen.getByText(/Câu chuyện phiêu lưu thần thoại/i)).toBeInTheDocument();
      });

      // Switch to sample tab
      const sampleTabBtn = screen.getByRole('button', { name: /Đọc thử trích đoạn/i });
      fireEvent.click(sampleTabBtn);
      expect(screen.getByText(/Khi bạn khao khát một điều gì đó/i)).toBeInTheDocument();

      // Add to cart click
      const addBtn = screen.getByRole('button', { name: /Thêm vào giỏ hàng/i });
      fireEvent.click(addBtn);
      expect(screen.getByText(/Đã thêm tác phẩm vào giỏ hàng!/i)).toBeInTheDocument();

      // Close modal
      const closeBtn = screen.getByRole('button', { name: 'Đóng' });
      fireEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalled();
    });
  });

  describe('CatalogStorefront & App Integration', () => {
    it('renders storefront catalog with hero banner and book grid', async () => {
      global.fetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/catalog/categories')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(MOCK_CATEGORIES),
          });
        }
        if (url.includes('/api/v1/catalog/books')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                items: [MOCK_BOOK],
                total: 1,
                page: 1,
                page_size: 12,
                total_pages: 1,
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'healthy' }),
        });
      });

      render(<CatalogStorefront />);

      expect(screen.getByText('NOVELIA BOOKSTORE CATALOG')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Nhà Giả Kim')).toBeInTheDocument();
        expect(screen.getByText(/Tìm thấy/i)).toBeInTheDocument();
      });
    });

    it('allows switching to Catalog tab from App navigation bar', async () => {
      global.fetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/catalog/categories')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(MOCK_CATEGORIES),
          });
        }
        if (url.includes('/api/v1/catalog/books')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                items: [MOCK_BOOK],
                total: 1,
                page: 1,
                page_size: 12,
                total_pages: 1,
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'healthy', database: 'novelia_books' }),
        });
      });

      render(<App />);

      // Initially on health tab
      expect(screen.getByRole('button', { name: /Trạng thái hệ thống/i })).toBeInTheDocument();

      // Click "Cửa hàng sách" tab
      const catalogTabBtn = screen.getByRole('button', { name: /Cửa hàng sách/i });
      fireEvent.click(catalogTabBtn);


      await waitFor(() => {
        expect(screen.getByText('NOVELIA BOOKSTORE CATALOG')).toBeInTheDocument();
        expect(screen.getByText('Nhà Giả Kim')).toBeInTheDocument();
      });
    });
  });
});
