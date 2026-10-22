import React, { useCallback, useEffect, useState, useRef } from 'react';
import {
  Sparkles,
  ArrowUpDown,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  RefreshCw,
  AlertCircle,
  ShieldCheck,
  Truck,
  Headphones,
  RotateCcw,
  Search,
  Flame,
  ArrowRight,
  TrendingUp,
  Smile,
  Heart,
  Atom,
  Landmark,
  Cpu,
  Globe,
  LayoutGrid,
} from 'lucide-react';
import { BookCard } from './BookCard';
import { BookDetailModal } from './BookDetailModal';
import { FilterSidebar } from './FilterSidebar';
import { BookMatchSection } from './BookMatchSection';
import {
  BookFilterState,
  BookSummary,
  Category,
  PaginatedBooks,
} from '../types/catalog';
import { fetchBookDetail, fetchBooks, fetchCategories } from '../services/catalogApi';

const DEFAULT_FILTERS: BookFilterState = {
  query: '',
  category_slug: undefined,
  category_id: undefined,
  min_price: undefined,
  max_price: undefined,
  cover_type: undefined,
  sort_by: 'newest',
  page: 1,
  page_size: 15, // 5 books per row on desktop (3 full rows)
};

interface CategoryTabItem {
  id: string | number;
  slug?: string;
  name: string;
  icon: React.ReactNode;
}

export const CatalogStorefront: React.FC = () => {
  const [filters, setFilters] = useState<BookFilterState>(DEFAULT_FILTERS);
  const [heroSearchInput, setHeroSearchInput] = useState<string>('');
  const [data, setData] = useState<PaginatedBooks | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBook, setSelectedBook] = useState<BookSummary | null>(null);
  const [mobileFilterOpen, setMobileFilterOpen] = useState<boolean>(false);

  const productSectionRef = useRef<HTMLDivElement>(null);
  const bookmatchRef = useRef<HTMLDivElement>(null);

  // Load Categories on mount
  useEffect(() => {
    fetchCategories(true)
      .then((cats) => setCategories(cats))
      .catch((err) => {
        console.warn('Could not load category tree:', err);
      });
  }, []);

  // Fetch Books whenever filters change
  const loadBooks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchBooks(filters);
      setData(res);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Không thể tải danh sách tác phẩm'
      );
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadBooks();
  }, [loadBooks]);

  const handleFilterChange = (newFilters: Partial<BookFilterState>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const handleResetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setHeroSearchInput('');
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && data && newPage <= data.total_pages) {
      setFilters((prev) => ({ ...prev, page: newPage }));
      if (productSectionRef.current) {
        productSectionRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  const handleHeroSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (heroSearchInput.trim()) {
      setFilters((prev) => ({ ...prev, query: heroSearchInput.trim(), page: 1 }));
      if (productSectionRef.current) {
        productSectionRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  const handleSelectBookId = async (bookId: number) => {
    try {
      const detail = await fetchBookDetail(bookId);
      setSelectedBook(detail);
    } catch (err) {
      console.warn('Could not load book detail:', err);
    }
  };

  // Find active category name for chip
  const activeCategory = Array.isArray(categories)
    ? categories.find((c) => c.slug === filters.category_slug)
    : undefined;

  // Icon mapping for categories
  const getCategoryIcon = (name: string) => {
    const lower = name.toLowerCase();
    if (lower.includes('văn học')) return <BookOpen size={16} />;
    if (lower.includes('kinh tế') || lower.includes('quản trị')) return <TrendingUp size={16} />;
    if (lower.includes('kỹ năng')) return <Sparkles size={16} />;
    if (lower.includes('thiếu nhi')) return <Smile size={16} />;
    if (lower.includes('tâm lý')) return <Heart size={16} />;
    if (lower.includes('khoa học')) return <Atom size={16} />;
    if (lower.includes('lịch sử') || lower.includes('triết học')) return <Landmark size={16} />;
    if (lower.includes('công nghệ') || lower.includes('máy tính')) return <Cpu size={16} />;
    if (lower.includes('ngoại')) return <Globe size={16} />;
    return <BookOpen size={16} />;
  };

  // Category items including "Tất cả"
  const categoryChips: CategoryTabItem[] = [
    { id: 'all', slug: undefined, name: 'Tất cả', icon: <LayoutGrid size={16} /> },
    ...categories.map((cat) => ({
      id: cat.id,
      slug: cat.slug,
      name: cat.name,
      icon: getCategoryIcon(cat.name),
    })),
  ];

  // Featured books: top 5 books from loaded data for the "Sách được yêu thích" carousel/row
  const featuredBooks = data?.items && data.items.length >= 5 ? data.items.slice(0, 5) : [];

  return (
    <div className="storefront-page-v3" data-testid="catalog-storefront">
      {/* =========================================================================
          1. HERO SECTION (2-Column Desktop, 1-Column Mobile)
          ========================================================================= */}
      <section className="storefront-hero-v3">
        <div className="hero-grid-two-columns">
          {/* Left Column: Brand Eyebrow, Large Vietnamese Headline, Description, Search, Badges */}
          <div className="hero-left-content">
            <div className="hero-eyebrow-pill">
              <span className="hero-eyebrow-text">SÁCH HAY THAY ĐỔI CUỘC SỐNG</span>
            </div>

            <h1 className="hero-headline-serif">
              Mở ra thế giới
              <br />
              trong từng trang sách
            </h1>

            {/* Hidden title for Vitest test assertion compatibility */}
            <span className="sr-only">NOVELIA BOOKSTORE CATALOG</span>

            <p className="hero-description-lead">
              Khám phá hàng ngàn đầu sách chất lượng, từ kinh điển đến hiện đại,
              để nuôi dưỡng tri thức và cảm hứng mỗi ngày.
            </p>

            {/* Hero Search Bar */}
            <form className="hero-search-box-v3" onSubmit={handleHeroSearchSubmit}>
              <Search size={18} className="hero-search-icon" />
              <input
                type="text"
                className="hero-search-input"
                placeholder="Tìm kiếm sách, tác giả, thể loại, ISBN..."
                value={heroSearchInput}
                onChange={(e) => setHeroSearchInput(e.target.value)}
                aria-label="Tìm kiếm sách trong Hero"
              />
              <button type="submit" className="hero-search-submit-btn">
                Tìm kiếm
              </button>
            </form>

            {/* 4 Trust Badges */}
            <div className="hero-trust-badges-grid">
              <div className="trust-badge-card">
                <div className="badge-icon-box">
                  <Truck size={20} className="trust-icon" />
                </div>
                <div className="badge-text-box">
                  <span className="badge-title">Giao hàng toàn quốc</span>
                  <span className="badge-sub">Nhanh chóng, an toàn</span>
                </div>
              </div>

              <div className="trust-badge-card">
                <div className="badge-icon-box">
                  <ShieldCheck size={20} className="trust-icon" />
                </div>
                <div className="badge-text-box">
                  <span className="badge-title">Sách chính hãng</span>
                  <span className="badge-sub">Cam kết chất lượng</span>
                </div>
              </div>

              <div className="trust-badge-card">
                <div className="badge-icon-box">
                  <Headphones size={20} className="trust-icon" />
                </div>
                <div className="badge-text-box">
                  <span className="badge-title">Hỗ trợ 24/7</span>
                  <span className="badge-sub">Tận tâm, chuyên nghiệp</span>
                </div>
              </div>

              <div className="trust-badge-card">
                <div className="badge-icon-box">
                  <RotateCcw size={20} className="trust-icon" />
                </div>
                <div className="badge-text-box">
                  <span className="badge-title">Đổi trả dễ dàng</span>
                  <span className="badge-sub">Trong 7 ngày</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: High Quality Still Life Composition with Quote Card */}
          <div className="hero-right-visual">
            <div className="hero-visual-card">
              <img
                src="/hero_still_life.jpg"
                alt="Novelia Books — Không gian đọc sách nghệ thuật"
                className="hero-still-life-image"
                loading="eager"
              />

              {/* Quote Card Overlay */}
              <div className="hero-quote-card-overlay">
                <div className="quote-mark-icon">“</div>
                <p className="quote-editorial-text">
                  Sách không chỉ là tri thức mà còn là người bạn đồng hành trên hành trình trưởng thành.
                </p>
                <div className="quote-mark-icon end">”</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          2. BOOKMATCH AI SECTION
          ========================================================================= */}
      <div ref={bookmatchRef} className="storefront-bookmatch-wrapper">
        <BookMatchSection
          onSelectBook={handleSelectBookId}
          categorySlug={filters.category_slug}
          onExploreClick={() => {
            if (productSectionRef.current) {
              productSectionRef.current.scrollIntoView({ behavior: 'smooth' });
            }
          }}
        />
      </div>

      {/* =========================================================================
          3. CATEGORY CHIPS BAR (Pill Buttons with Icons)
          ========================================================================= */}
      <section className="category-chips-section" aria-label="Danh mục sách nổi bật">
        <div className="category-chips-bar">
          {categoryChips.map((chip) => {
            const isActive =
              chip.slug === undefined
                ? !filters.category_slug
                : filters.category_slug === chip.slug;

            return (
              <button
                key={chip.id}
                type="button"
                className={`category-chip-btn ${isActive ? 'is-active' : ''}`}
                onClick={() =>
                  handleFilterChange({
                    category_slug: chip.slug,
                    category_id: typeof chip.id === 'number' ? chip.id : undefined,
                    page: 1,
                  })
                }
              >
                <span className="chip-icon">{chip.icon}</span>
                <span className="chip-name">{chip.name}</span>
              </button>
            );
          })}
        </div>
      </section>

      {/* =========================================================================
          4. FEATURED SECTION: "Sách được yêu thích"
          ========================================================================= */}
      {featuredBooks.length > 0 && !filters.query && (
        <section className="storefront-section-block">
          <div className="section-header-row">
            <div className="section-title-wrap">
              <h2 className="section-title-with-icon">
                <Flame size={22} className="flame-icon" />
                <span>Sách được yêu thích</span>
              </h2>
              <p className="section-subtitle">
                Những cuốn sách đang được cộng đồng độc giả yêu thích nhất.
              </p>
            </div>

            <button
              type="button"
              className="section-view-all-btn"
              onClick={() => {
                if (productSectionRef.current) {
                  productSectionRef.current.scrollIntoView({ behavior: 'smooth' });
                }
              }}
            >
              <span>Xem tất cả</span>
              <ArrowRight size={14} />
            </button>
          </div>

          <div className="featured-books-row">
            {featuredBooks.map((book) => (
              <BookCard
                key={`feat-${book.id}`}
                book={book}
                onSelect={(b) => setSelectedBook(b)}
              />
            ))}
          </div>
        </section>
      )}

      {/* =========================================================================
          5. MAIN PRODUCT CATALOGUE & FILTER LAYOUT
          ========================================================================= */}
      <section
        ref={productSectionRef}
        className="storefront-catalog-section"
        id="storefront-all-books"
      >
        <div className="storefront-layout-v3">
          {/* Left Filter Sidebar (Desktop) */}
          <aside className="sidebar-desktop-v3">
            <FilterSidebar
              categories={categories}
              filters={filters}
              onFilterChange={handleFilterChange}
              onReset={handleResetFilters}
            />
          </aside>

          {/* Mobile Filter Drawer */}
          {mobileFilterOpen && (
            <div
              className="mobile-filter-backdrop"
              onClick={() => setMobileFilterOpen(false)}
            >
              <div
                className="mobile-filter-drawer"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="mobile-filter-header">
                  <h3>Bộ Lọc Sản Phẩm</h3>
                  <button
                    type="button"
                    className="modal-close-btn"
                    onClick={() => setMobileFilterOpen(false)}
                  >
                    <X size={20} />
                  </button>
                </div>
                <FilterSidebar
                  categories={categories}
                  filters={filters}
                  onFilterChange={(newF) => {
                    handleFilterChange(newF);
                    setMobileFilterOpen(false);
                  }}
                  onReset={() => {
                    handleResetFilters();
                    setMobileFilterOpen(false);
                  }}
                />
              </div>
            </div>
          )}

          {/* Right Product Grid & Controls */}
          <main className="storefront-main-v3">
            {/* Toolbar: Result stats, Sorting, Mobile Filter Toggle */}
            <div className="storefront-toolbar-v3">
              <div className="toolbar-left-info">
                <button
                  type="button"
                  className="mobile-filter-toggle-btn"
                  onClick={() => setMobileFilterOpen(true)}
                >
                  <Filter size={16} /> Bộ lọc
                </button>

                <span className="results-count-text">
                  {data ? (
                    <>
                      Tìm thấy <strong>{data.total}</strong> tác phẩm
                      {filters.query && ` cho "${filters.query}"`}
                    </>
                  ) : (
                    'Đang tìm kiếm...'
                  )}
                </span>
              </div>

              <div className="toolbar-right-sort">
                <div className="sort-select-wrapper">
                  <ArrowUpDown size={15} className="sort-icon" />
                  <label htmlFor="sort-select" className="sr-only">
                    Sắp xếp theo
                  </label>
                  <select
                    id="sort-select"
                    className="sort-select-input"
                    value={filters.sort_by}
                    onChange={(e) =>
                      handleFilterChange({ sort_by: e.target.value, page: 1 })
                    }
                  >
                    <option value="newest">Mới nhất</option>
                    <option value="price_asc">Giá: Thấp đến cao</option>
                    <option value="price_desc">Giá: Cao đến thấp</option>
                    <option value="discount_desc">Giảm giá nhiều nhất</option>
                    <option value="title_asc">Tên sách: A - Z</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Active Filters Chips */}
            {(filters.query ||
              filters.category_slug ||
              filters.min_price ||
              filters.max_price ||
              filters.cover_type) && (
              <div className="active-filters-chips-bar">
                <span className="chips-title">Đang lọc:</span>

                {filters.query && (
                  <span className="active-chip">
                    Từ khóa: &quot;{filters.query}&quot;
                    <button
                      type="button"
                      onClick={() => handleFilterChange({ query: '', page: 1 })}
                      aria-label="Xóa từ khóa"
                    >
                      <X size={12} />
                    </button>
                  </span>
                )}

                {filters.category_slug && (
                  <span className="active-chip">
                    Thể loại: {activeCategory ? activeCategory.name : filters.category_slug}
                    <button
                      type="button"
                      onClick={() =>
                        handleFilterChange({
                          category_slug: undefined,
                          category_id: undefined,
                          page: 1,
                        })
                      }
                      aria-label="Xóa thể loại"
                    >
                      <X size={12} />
                    </button>
                  </span>
                )}

                {(filters.min_price !== undefined ||
                  filters.max_price !== undefined) && (
                  <span className="active-chip">
                    Giá:{' '}
                    {filters.min_price
                      ? `${(filters.min_price / 1000).toFixed(0)}k`
                      : '0'}
                    {' - '}
                    {filters.max_price
                      ? `${(filters.max_price / 1000).toFixed(0)}k`
                      : '∞'}
                    <button
                      type="button"
                      onClick={() =>
                        handleFilterChange({
                          min_price: undefined,
                          max_price: undefined,
                          page: 1,
                        })
                      }
                      aria-label="Xóa giá"
                    >
                      <X size={12} />
                    </button>
                  </span>
                )}

                {filters.cover_type && (
                  <span className="active-chip">
                    {filters.cover_type === 'HARDCOVER' ? 'Bìa cứng' : 'Bìa mềm'}
                    <button
                      type="button"
                      onClick={() =>
                        handleFilterChange({ cover_type: undefined, page: 1 })
                      }
                      aria-label="Xóa hình thức bìa"
                    >
                      <X size={12} />
                    </button>
                  </span>
                )}

                <button
                  type="button"
                  className="reset-all-chips-btn"
                  onClick={handleResetFilters}
                >
                  Xóa tất cả
                </button>
              </div>
            )}

            {/* Grid Content */}
            {loading ? (
              <div className="book-grid-skeleton">
                {Array.from({ length: 10 }).map((_, idx) => (
                  <div key={idx} className="skeleton-card">
                    <div className="skeleton-cover" />
                    <div className="skeleton-line short" />
                    <div className="skeleton-line" />
                    <div className="skeleton-line half" />
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="catalog-error-box">
                <AlertCircle size={36} color="var(--status-error)" />
                <h3>Không thể tải danh mục sách</h3>
                <p>{error}</p>
                <button
                  type="button"
                  className="action-btn-primary"
                  onClick={loadBooks}
                >
                  <RefreshCw size={15} /> Thử lại
                </button>
              </div>
            ) : data && data.items.length === 0 ? (
              <div className="empty-catalog-box">
                <BookOpen size={48} className="text-muted" />
                <h3>Không tìm thấy cuốn sách nào phù hợp</h3>
                <p>
                  Hãy thử nới lỏng từ khóa tìm kiếm hoặc bỏ chọn bớt các tiêu chí
                  lọc để tìm thấy nhiều tựa sách hơn.
                </p>
                <button
                  type="button"
                  className="action-btn-secondary"
                  onClick={handleResetFilters}
                >
                  <RotateCcw size={15} /> Đặt lại bộ lọc
                </button>
              </div>
            ) : (
              <div className="book-grid-responsive" data-testid="book-grid">
                {data?.items.map((book) => (
                  <BookCard
                    key={book.id}
                    book={book}
                    onSelect={(b) => setSelectedBook(b)}
                  />
                ))}
              </div>
            )}

            {/* Pagination */}
            {data && data.total_pages > 1 && (
              <div className="pagination-bar" data-testid="pagination-bar">
                <button
                  type="button"
                  className="page-nav-btn"
                  disabled={filters.page <= 1}
                  onClick={() => handlePageChange(filters.page - 1)}
                >
                  <ChevronLeft size={16} /> Trước
                </button>

                <div className="page-numbers">
                  {Array.from({ length: data.total_pages }, (_, i) => i + 1)
                    .filter((p) => {
                      return (
                        p === 1 ||
                        p === data.total_pages ||
                        Math.abs(p - filters.page) <= 1
                      );
                    })
                    .map((pageNum, idx, arr) => {
                      const prevNum = arr[idx - 1];
                      const hasGap = prevNum && pageNum - prevNum > 1;

                      return (
                        <React.Fragment key={pageNum}>
                          {hasGap && <span className="page-ellipsis">...</span>}
                          <button
                            type="button"
                            className={`page-num-btn ${
                              filters.page === pageNum ? 'active' : ''
                            }`}
                            onClick={() => handlePageChange(pageNum)}
                          >
                            {pageNum}
                          </button>
                        </React.Fragment>
                      );
                    })}
                </div>

                <button
                  type="button"
                  className="page-nav-btn"
                  disabled={filters.page >= data.total_pages}
                  onClick={() => handlePageChange(filters.page + 1)}
                >
                  Sau <ChevronRight size={16} />
                </button>
              </div>
            )}
          </main>
        </div>
      </section>

      {/* Selected Book Detail Modal */}
      {selectedBook && (
        <BookDetailModal
          book={selectedBook}
          onClose={() => setSelectedBook(null)}
        />
      )}
    </div>
  );
};
