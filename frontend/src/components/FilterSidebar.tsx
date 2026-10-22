import React, { useState } from 'react';
import {
  Search,
  Filter,
  Layers,
  Tag,
  RotateCcw,
  ChevronRight,
  ChevronDown,
  BookOpen,
} from 'lucide-react';
import { BookFilterState, Category } from '../types/catalog';

interface FilterSidebarProps {
  categories: Category[];
  filters: BookFilterState;
  onFilterChange: (newFilters: Partial<BookFilterState>) => void;
  onReset: () => void;
}

const PRICE_PRESETS = [
  { label: 'Tất cả mức giá', min: undefined, max: undefined },
  { label: 'Dưới 100.000 ₫', min: undefined, max: 100000 },
  { label: '100.000 ₫ – 200.000 ₫', min: 100000, max: 200000 },
  { label: '200.000 ₫ – 300.000 ₫', min: 200000, max: 300000 },
  { label: 'Trên 300.000 ₫', min: 300000, max: undefined },
];

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  categories,
  filters,
  onFilterChange,
  onReset,
}) => {
  const [searchInput, setSearchInput] = useState<string>(filters.query || '');
  const [expandedCats, setExpandedCats] = useState<Record<number, boolean>>({});

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({ query: searchInput, page: 1 });
  };

  const toggleCategoryExpand = (catId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedCats((prev) => ({ ...prev, [catId]: !prev[catId] }));
  };

  const isCurrentPricePreset = (min?: number, max?: number) => {
    return filters.min_price === min && filters.max_price === max;
  };

  return (
    <aside className="filter-sidebar">
      {/* Header */}
      <div className="filter-header">
        <div className="filter-title-wrap">
          <Filter size={18} className="text-gold" />
          <h3 className="filter-title">Bộ Lọc Tác Phẩm</h3>
        </div>
        <button
          type="button"
          className="filter-reset-btn"
          onClick={() => {
            setSearchInput('');
            onReset();
          }}
          title="Xóa bộ lọc"
        >
          <RotateCcw size={14} /> Đặt lại
        </button>
      </div>

      {/* Keyword Search */}
      <div className="filter-group">
        <form onSubmit={handleSearchSubmit} className="search-form">
          <div className="search-input-wrap">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Tìm theo tên, ISBN, tác giả..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="search-input"
            />
          </div>
          <button type="submit" className="search-btn">
            Tìm
          </button>
        </form>
      </div>

      {/* Category Tree */}
      <div className="filter-group">
        <h4 className="filter-group-title">
          <Layers size={15} /> Thể loại
        </h4>
        <div className="category-tree">
          {/* All categories option */}
          <button
            type="button"
            className={`cat-tree-item ${
              !filters.category_slug && !filters.category_id ? 'active' : ''
            }`}
            onClick={() =>
              onFilterChange({
                category_slug: undefined,
                category_id: undefined,
                page: 1,
              })
            }
          >
            <span>Tất cả thể loại</span>
          </button>

          {/* Root Categories */}
          {categories.map((cat) => {
            const isSelected =
              filters.category_slug === cat.slug ||
              filters.category_id === cat.id;
            const hasSub =
              cat.subcategories && cat.subcategories.length > 0;
            const isExpanded = !!expandedCats[cat.id];

            return (
              <div key={cat.id} className="cat-tree-node">
                <div
                  className={`cat-tree-item ${isSelected ? 'active' : ''}`}
                  onClick={() =>
                    onFilterChange({
                      category_slug: cat.slug,
                      category_id: undefined,
                      page: 1,
                    })
                  }
                >
                  <span className="cat-name">{cat.name}</span>
                  <div className="cat-meta">
                    {cat.book_count !== undefined && (
                      <span className="cat-count">({cat.book_count})</span>
                    )}
                    {hasSub && (
                      <button
                        type="button"
                        className="cat-expand-btn"
                        onClick={(e) => toggleCategoryExpand(cat.id, e)}
                        aria-label="Mở rộng danh mục con"
                      >
                        {isExpanded ? (
                          <ChevronDown size={14} />
                        ) : (
                          <ChevronRight size={14} />
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {/* Subcategories */}
                {hasSub && isExpanded && (
                  <div className="cat-sub-tree">
                    {cat.subcategories!.map((sub) => {
                      const isSubSelected =
                        filters.category_slug === sub.slug ||
                        filters.category_id === sub.id;

                      return (
                        <button
                          key={sub.id}
                          type="button"
                          className={`cat-tree-sub-item ${
                            isSubSelected ? 'active' : ''
                          }`}
                          onClick={() =>
                            onFilterChange({
                              category_slug: sub.slug,
                              category_id: undefined,
                              page: 1,
                            })
                          }
                        >
                          <span className="cat-name">{sub.name}</span>
                          {sub.book_count !== undefined && (
                            <span className="cat-count">
                              ({sub.book_count})
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Price Ranges */}
      <div className="filter-group">
        <h4 className="filter-group-title">
          <Tag size={15} /> Khoảng giá
        </h4>
        <div className="price-presets">
          {PRICE_PRESETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              className={`preset-btn ${
                isCurrentPricePreset(p.min, p.max) ? 'active' : ''
              }`}
              onClick={() =>
                onFilterChange({
                  min_price: p.min,
                  max_price: p.max,
                  page: 1,
                })
              }
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Cover Type */}
      <div className="filter-group">
        <h4 className="filter-group-title">
          <BookOpen size={15} /> Hình thức bìa
        </h4>
        <div className="format-options">
          {[
            { label: 'Tất cả', value: undefined },
            { label: 'Bìa mềm', value: 'PAPERBACK' },
            { label: 'Bìa cứng', value: 'HARDCOVER' },
          ].map((fmt, idx) => (
            <button
              key={idx}
              type="button"
              className={`format-btn ${
                filters.cover_type === fmt.value ? 'active' : ''
              }`}
              onClick={() =>
                onFilterChange({ cover_type: fmt.value, page: 1 })
              }
            >
              {fmt.label}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
};
