import React, { useEffect, useState } from 'react';
import {
  X,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  FileText,
  ShoppingCart,
  Tag,
  Heart,
  Star,
  Plus,
  Minus,
} from 'lucide-react';
import { BookDetail, BookSummary } from '../types/catalog';
import { fetchBookDetail, formatVND } from '../services/catalogApi';
import { useSafeCommerce } from '../context/CommerceContext';
import { useSafeAuth } from '../context/AuthContext';
import { ReviewSection } from './ReviewSection';
import { generateFallbackCover } from '../utils/coverUtils';

interface BookDetailModalProps {
  book: BookSummary | null;
  onClose: () => void;
}

export const BookDetailModal: React.FC<BookDetailModalProps> = ({
  book,
  onClose,
}) => {
  const [detail, setDetail] = useState<BookDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'desc' | 'sample' | 'reviews'>('desc');
  const [quantity, setQuantity] = useState<number>(1);
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; text: string } | null>(
    null
  );

  const { isAuthenticated } = useSafeAuth();
  const { addToCart, isInWishlist, addToWishlist, removeFromWishlist } = useSafeCommerce();

  useEffect(() => {
    if (!book) return;

    setLoading(true);
    setError(null);
    setSelectedImage(book.cover_image_url);
    setQuantity(1);
    setNotice(null);

    fetchBookDetail(book.id)
      .then((data) => {
        setDetail(data);
        if (data.cover_image_url) {
          setSelectedImage(data.cover_image_url);
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Không thể tải chi tiết sách');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [book]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!book) return null;

  const currentBook = detail || (book as unknown as BookDetail);
  const isFavorited = isInWishlist(currentBook.id);

  const handleAddToCart = async () => {
    if (isAuthenticated) {
      try {
        await addToCart(currentBook.id, quantity);
      } catch (err) {
        setNotice({
          type: 'error',
          text: err instanceof Error ? err.message : 'Lỗi thêm vào giỏ hàng',
        });
        setTimeout(() => setNotice(null), 3000);
        return;
      }
    }
    setNotice({
      type: 'success',
      text: 'Đã thêm tác phẩm vào giỏ hàng!',
    });
    setTimeout(() => setNotice(null), 3000);
  };

  const handleToggleWishlist = async () => {
    if (!isAuthenticated) {
      setNotice({
        type: 'error',
        text: 'Vui lòng đăng nhập để lưu vào danh sách yêu thích.',
      });
      setTimeout(() => setNotice(null), 3000);
      return;
    }

    try {
      if (isFavorited) {
        await removeFromWishlist(currentBook.id);
        setNotice({
          type: 'success',
          text: 'Đã xóa khỏi danh sách yêu thích.',
        });
      } else {
        await addToWishlist(currentBook.id);
        setNotice({
          type: 'success',
          text: 'Đã thêm vào danh sách yêu thích!',
        });
      }
    } catch {
      setNotice({
        type: 'error',
        text: 'Không thể cập nhật danh sách yêu thích.',
      });
    }
    setTimeout(() => setNotice(null), 2500);
  };

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      data-testid="book-detail-modal"
    >
      <div
        className="modal-container book-detail-container"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className="modal-close-btn"
          onClick={onClose}
          aria-label="Đóng"
        >
          <X size={20} />
        </button>

        {loading ? (
          <div className="modal-loading-state">
            <div className="spinner-large" />
            <p>Đang tải thông tin chi tiết tác phẩm...</p>
          </div>
        ) : error ? (
          <div className="modal-error-state">
            <AlertCircle size={32} color="var(--status-error)" />
            <p>{error}</p>
            <button
              type="button"
              className="action-btn-primary"
              onClick={onClose}
            >
              Quay lại
            </button>
          </div>
        ) : (
          <div className="book-detail-layout">
            {/* Left: Gallery & Cover */}
            <div className="book-detail-media">
              <div className="book-detail-cover-box">
                <img
                  src={selectedImage || currentBook.cover_image_url || generateFallbackCover(currentBook.title, currentBook.primary_author)}
                  alt={currentBook.title}
                  className="book-detail-cover"
                  onError={(e) => {
                    const target = e.currentTarget;
                    const fallback = generateFallbackCover(currentBook.title, currentBook.primary_author);
                    if (target.src !== fallback) {
                      target.src = fallback;
                    }
                  }}
                />
                {currentBook.discount_percent > 0 && (
                  <span className="badge-discount-lg">
                    <Tag size={13} /> Tiết kiệm {currentBook.discount_percent}%
                  </span>
                )}
              </div>

              {/* Thumbnail strip if multiple images */}
              {currentBook.images && currentBook.images.length > 1 && (
                <div className="thumbnail-strip">
                  <button
                    type="button"
                    className={`thumb-btn ${
                      selectedImage === currentBook.cover_image_url
                        ? 'active'
                        : ''
                    }`}
                    onClick={() => setSelectedImage(currentBook.cover_image_url)}
                  >
                    <img
                      src={currentBook.cover_image_url}
                      alt="Ảnh bìa"
                    />
                  </button>
                  {currentBook.images.map((img) => (
                    <button
                      key={img.id}
                      type="button"
                      className={`thumb-btn ${
                        selectedImage === img.image_url ? 'active' : ''
                      }`}
                      onClick={() => setSelectedImage(img.image_url)}
                    >
                      <img src={img.image_url} alt={img.alt_text || 'Ảnh phụ'} />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Right: Info, Price, Specs, Sample, Reviews */}
            <div className="book-detail-content">
              {/* Category & Format Pill */}
              <div className="book-detail-tags">
                {currentBook.categories?.map((cat) => (
                  <span key={cat.category_id} className="tag-pill">
                    {cat.name}
                  </span>
                ))}
                <span className="tag-pill-neutral">
                  {currentBook.cover_type === 'HARDCOVER'
                    ? 'Bìa cứng'
                    : 'Bìa mềm'}
                </span>
              </div>

              {/* Title & Author */}
              <h2 className="book-detail-title">{currentBook.title}</h2>
              <p className="book-detail-author">
                Tác giả:{' '}
                <span className="author-highlight">
                  {currentBook.authors?.map((a) => a.name).join(', ') ||
                    currentBook.primary_author ||
                    'Nhiều tác giả'}
                </span>
              </p>

              {/* Price Row */}
              <div className="book-detail-price-box">
                <div className="price-stack">
                  <span className="detail-price-current">
                    {formatVND(currentBook.price)}
                  </span>
                  {currentBook.discount_percent > 0 && (
                    <span className="detail-price-original">
                      {formatVND(currentBook.original_price)}
                    </span>
                  )}
                </div>

                <div className="stock-badge-large">
                  {currentBook.is_in_stock ? (
                    <span className="stock-in-pill">
                      <CheckCircle2 size={16} /> Còn {currentBook.stock_available} cuốn
                    </span>
                  ) : (
                    <span className="stock-out-pill">
                      <AlertCircle size={16} /> Tạm hết hàng
                    </span>
                  )}
                </div>
              </div>

              {/* Add to Cart Actions */}
              <div className="detail-purchase-panel">
                {currentBook.is_in_stock && (
                  <div className="detail-qty-stepper">
                    <span className="stepper-label">Số lượng:</span>
                    <div className="stepper-controls">
                      <button
                        type="button"
                        onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                        disabled={quantity <= 1}
                      >
                        <Minus size={14} />
                      </button>
                      <span>{quantity}</span>
                      <button
                        type="button"
                        onClick={() =>
                          setQuantity((q) =>
                            Math.min(currentBook.stock_available, q + 1)
                          )
                        }
                        disabled={quantity >= currentBook.stock_available}
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                )}

                <div className="detail-actions-row">
                  <button
                    type="button"
                    className="add-to-cart-btn"
                    disabled={!currentBook.is_in_stock}
                    onClick={handleAddToCart}
                  >
                    <ShoppingCart size={18} />
                    {currentBook.is_in_stock
                      ? 'Thêm vào giỏ hàng'
                      : 'Thông báo khi có hàng'}
                  </button>

                  <button
                    type="button"
                    className={`detail-wishlist-btn ${isFavorited ? 'is-favorited' : ''}`}
                    onClick={handleToggleWishlist}
                    title={isFavorited ? 'Bỏ khỏi yêu thích' : 'Thêm vào yêu thích'}
                  >
                    <Heart
                      size={18}
                      fill={isFavorited ? 'var(--status-error)' : 'none'}
                    />
                    <span>{isFavorited ? 'Đã yêu thích' : 'Yêu thích'}</span>
                  </button>
                </div>

                {notice && (
                  <div className={`detail-action-notice notice-${notice.type}`}>
                    {notice.type === 'success' ? (
                      <CheckCircle2 size={16} />
                    ) : (
                      <AlertCircle size={16} />
                    )}
                    <span>{notice.text}</span>
                  </div>
                )}
              </div>

              {/* Specifications Grid */}
              <div className="specs-section">
                <h4 className="specs-title">Thông số xuất bản</h4>
                <div className="specs-grid">
                  <div className="spec-item">
                    <span className="spec-label">Mã SKU:</span>
                    <span className="spec-value">{currentBook.sku}</span>
                  </div>
                  <div className="spec-item">
                    <span className="spec-label">Mã ISBN:</span>
                    <span className="spec-value">{currentBook.isbn}</span>
                  </div>
                  {currentBook.publisher && (
                    <div className="spec-item">
                      <span className="spec-label">Nhà xuất bản:</span>
                      <span className="spec-value">
                        {currentBook.publisher.name}
                      </span>
                    </div>
                  )}
                  {currentBook.page_count && (
                    <div className="spec-item">
                      <span className="spec-label">Số trang:</span>
                      <span className="spec-value">
                        {currentBook.page_count} trang
                      </span>
                    </div>
                  )}
                  {currentBook.dimension && (
                    <div className="spec-item">
                      <span className="spec-label">Kích thước:</span>
                      <span className="spec-value">
                        {currentBook.dimension}
                      </span>
                    </div>
                  )}
                  {currentBook.weight_grams && (
                    <div className="spec-item">
                      <span className="spec-label">Trọng lượng:</span>
                      <span className="spec-value">
                        {currentBook.weight_grams} g
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Tabs for Description, Sample Text, and Reviews */}
              <div className="detail-tabs">
                <div className="tabs-header">
                  <button
                    type="button"
                    className={`tab-btn ${activeTab === 'desc' ? 'active' : ''}`}
                    onClick={() => setActiveTab('desc')}
                  >
                    <BookOpen size={16} /> Giới thiệu tác phẩm
                  </button>
                  {currentBook.sample_text && (
                    <button
                      type="button"
                      className={`tab-btn ${activeTab === 'sample' ? 'active' : ''}`}
                      onClick={() => setActiveTab('sample')}
                    >
                      <FileText size={16} /> Đọc thử trích đoạn
                    </button>
                  )}
                  <button
                    type="button"
                    className={`tab-btn ${activeTab === 'reviews' ? 'active' : ''}`}
                    onClick={() => setActiveTab('reviews')}
                  >
                    <Star size={16} /> Đánh giá bạn đọc
                  </button>
                </div>

                <div className="tab-pane">
                  {activeTab === 'desc' ? (
                    <div className="book-desc-content">
                      {currentBook.description ? (
                        <p>{currentBook.description}</p>
                      ) : (
                        <p className="text-muted">
                          Tác phẩm đang được cập nhật thông tin mô tả chi tiết.
                        </p>
                      )}
                    </div>
                  ) : activeTab === 'sample' ? (
                    <div className="book-sample-content">
                      <blockquote className="sample-quote">
                        {currentBook.sample_text}
                      </blockquote>
                    </div>
                  ) : (
                    <ReviewSection bookId={currentBook.id} />
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
