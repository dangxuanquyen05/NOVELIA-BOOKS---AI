import React, { useEffect, useState, useCallback } from 'react';
import {
  Sparkles,
  RefreshCw,
  ShoppingBag,
  ChevronRight,
  BookOpen,
  Info,
  CheckCircle2,
  Brain,
  ArrowRight,
} from 'lucide-react';
import { useSafeAuth } from '../context/AuthContext';
import { useSafeCommerce } from '../context/CommerceContext';
import {
  fetchPersonalizedRecommendations,
  sendRecommendationEvent,
} from '../services/recommendationApi';
import {
  BookMatchResponse,
  BookRecommendationItem,
} from '../types/recommendation';
import { generateFallbackCover } from '../utils/coverUtils';

interface BookMatchSectionProps {
  onSelectBook?: (bookId: number) => void;
  categorySlug?: string;
  onExploreClick?: () => void;
}

export const BookMatchSection: React.FC<BookMatchSectionProps> = ({
  onSelectBook,
  categorySlug,
  onExploreClick,
}) => {
  const { token, isAuthenticated } = useSafeAuth();
  const { addToCart } = useSafeCommerce();

  const [data, setData] = useState<BookMatchResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [addingBookId, setAddingBookId] = useState<number | null>(null);
  const [addedBookId, setAddedBookId] = useState<number | null>(null);
  const [showDetailGrid, setShowDetailGrid] = useState<boolean>(true);

  const loadRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchPersonalizedRecommendations(token, 4, categorySlug);
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Không thể tải đề xuất BookMatch AI.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [token, categorySlug]);

  useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  const handleQuickAdd = async (book: BookRecommendationItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isAuthenticated) {
      alert('Quý khách vui lòng đăng nhập để thêm sách vào giỏ hàng.');
      return;
    }

    setAddingBookId(book.book_id);
    try {
      await addToCart(book.book_id, 1);
      setAddedBookId(book.book_id);
      setTimeout(() => setAddedBookId(null), 2500);

      // Send telemetry click/add_to_cart event
      sendRecommendationEvent(token, {
        book_id: book.book_id,
        event_type: 'ADD_TO_CART',
        metadata_json: { match_score: book.match_score, algorithm: book.algorithm_type },
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Không thể thêm sản phẩm vào giỏ hàng.';
      alert(msg);
    } finally {
      setAddingBookId(null);
    }
  };

  const handleCardClick = (book: BookRecommendationItem) => {
    sendRecommendationEvent(token, {
      book_id: book.book_id,
      event_type: 'CLICK',
      metadata_json: { match_score: book.match_score },
    });
    if (onSelectBook) {
      onSelectBook(book.book_id);
    }
  };

  return (
    <section className="bookmatch-v3-container" data-testid="bookmatch-section">
      {/* Editorial AI Banner Card */}
      <div className="bookmatch-banner-card">
        <div className="bookmatch-banner-left">
          {/* Eyebrow badge */}
          <div className="bookmatch-brand-pill">
            <span className="pill-ai-tag">AI</span>
            <span className="pill-text">BookMatch AI™ Cá Nhân Hóa</span>
          </div>

          <h2 className="bookmatch-main-heading">
            Tìm cuốn sách dành riêng cho bạn
          </h2>

          <p className="bookmatch-main-desc">
            Dựa trên sở thích, lịch sử đọc và hành vi của bạn, BookMatch AI sẽ gợi ý những cuốn sách
            phù hợp nhất, giúp bạn khám phá thế giới đọc theo cách riêng.
          </p>

          <div className="bookmatch-banner-actions">
            <button
              type="button"
              className="bookmatch-cta-btn"
              onClick={() => {
                setShowDetailGrid(true);
                if (onExploreClick) onExploreClick();
              }}
            >
              <Sparkles size={16} />
              <span>Khám phá BookMatch</span>
              <ArrowRight size={15} />
            </button>

            <button
              type="button"
              className="bookmatch-refresh-btn"
              onClick={loadRecommendations}
              disabled={loading}
              title="Làm mới danh sách gợi ý"
            >
              <RefreshCw size={14} className={loading ? 'spin-icon' : ''} />
              <span>Làm mới gợi ý</span>
            </button>
          </div>
        </div>

        {/* Right Art & Quote Callout */}
        <div className="bookmatch-banner-right">
          <div className="bookmatch-quote-speech-bubble">
            <div className="bubble-icon-circle">
              <Brain size={18} className="brain-icon" />
            </div>
            <p className="bubble-quote-text">
              “Mỗi người đều có một hành trình đọc riêng...”
            </p>
          </div>

          {/* Elegant SVG Line-art Illustration of Book Stack & Botanical Plant */}
          <div className="bookmatch-art-illustration" aria-hidden="true">
            <svg
              viewBox="0 0 260 180"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="bookmatch-svg-art"
            >
              {/* Plant pot and leaves */}
              <ellipse cx="60" cy="155" rx="22" ry="6" fill="#E8E2D5" />
              <path
                d="M48 152 L52 118 C52 115 68 115 68 118 L72 152 Z"
                stroke="#6B8576"
                strokeWidth="1.75"
                fill="#F4EFEA"
              />
              <path
                d="M60 115 C55 85 40 70 30 65 C45 75 52 95 60 115 Z"
                fill="#8BA895"
                stroke="#5F7D6B"
                strokeWidth="1.2"
              />
              <path
                d="M60 115 C65 80 85 68 100 62 C85 75 75 95 60 115 Z"
                fill="#9DBBA8"
                stroke="#5F7D6B"
                strokeWidth="1.2"
              />
              <path
                d="M60 110 C60 70 60 50 60 40"
                stroke="#5F7D6B"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
              <path
                d="M60 85 C50 75 42 75 36 78 C42 85 52 86 60 85 Z"
                fill="#ABC5B3"
              />
              <path
                d="M60 70 C70 62 80 62 86 66 C80 72 70 72 60 70 Z"
                fill="#ABC5B3"
              />

              {/* Books Stack */}
              {/* Base Book */}
              <rect
                x="110"
                y="136"
                width="135"
                height="22"
                rx="3"
                fill="#FAF7F2"
                stroke="#708579"
                strokeWidth="1.75"
              />
              <path d="M125 136 L125 158" stroke="#D1C7B7" strokeWidth="1.5" />
              <path d="M110 147 L245 147" stroke="#E3DACD" strokeWidth="1" strokeDasharray="2 3" />

              {/* Middle Book */}
              <rect
                x="118"
                y="112"
                width="120"
                height="24"
                rx="3"
                fill="#F0EAE1"
                stroke="#6A8073"
                strokeWidth="1.75"
              />
              <path d="M132 112 L132 136" stroke="#D1C7B7" strokeWidth="1.5" />
              <line x1="145" y1="124" x2="225" y2="124" stroke="#9AA89E" strokeWidth="1.5" />

              {/* Top Book */}
              <rect
                x="125"
                y="88"
                width="105"
                height="24"
                rx="3"
                fill="#FFFFFF"
                stroke="#5E7567"
                strokeWidth="1.75"
              />
              <path d="M138 88 L138 112" stroke="#C27D38" strokeWidth="1.75" />
              <circle cx="178" cy="100" r="4" fill="#C27D38" />

              {/* Gentle floating sparkles */}
              <path d="M235 70 Q240 70 240 65 Q240 70 245 70 Q240 70 240 75 Q240 70 235 70 Z" fill="#C27D38" />
              <path d="M105 45 Q108 45 108 42 Q108 45 111 45 Q108 45 108 48 Q108 45 105 45 Z" fill="#8BA895" />
            </svg>
          </div>
        </div>
      </div>

      {/* Recommended Books Grid */}
      {showDetailGrid && (
        <div className="bookmatch-detail-section">
          <div className="bookmatch-results-header">
            <div className="results-header-left">
              <span className="results-badge">
                <Sparkles size={14} className="sparkle-gold" />
                {data?.is_cold_start
                  ? 'Tuyển Tập Độc Giả Yêu Thích Nhất'
                  : 'Gợi Ý Dành Riêng Cho Gu Đọc Của Bạn'}
              </span>
              <p className="results-subtitle">
                {data?.is_cold_start
                  ? 'Sách bán chạy và được đánh giá cao nhất toàn hệ thống, đối soát tồn kho thời gian thực 100%.'
                  : `Phân tích dựa trên các tác phẩm bạn đã đọc và quan tâm (${data?.taste_profile?.top_categories?.map((c) => c.name).join(', ') || 'Đa dạng thể loại'}).`}
              </p>
            </div>
          </div>

          {loading && !data ? (
            <div className="bookmatch-grid-v3">
              {[1, 2, 3, 4].map((n) => (
                <div key={n} className="bookmatch-skeleton-card">
                  <div className="skeleton-cover-box" />
                  <div className="skeleton-line full" />
                  <div className="skeleton-line half" />
                  <div className="skeleton-line price" />
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="bookmatch-error-box">
              <Info size={24} className="text-warning" />
              <p>{error}</p>
              <button
                type="button"
                className="retry-btn"
                onClick={loadRecommendations}
              >
                Thử lại
              </button>
            </div>
          ) : data?.recommendations && data.recommendations.length > 0 ? (
            <div className="bookmatch-grid-v3">
              {data.recommendations.map((book) => {
                const matchPercent = Math.round(book.match_score * 100);
                const bookCover =
                  book.cover_image_url ||
                  generateFallbackCover(book.title, book.primary_author);

                return (
                  <div
                    key={book.book_id}
                    onClick={() => handleCardClick(book)}
                    className="bookmatch-card-v3"
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardClick(book);
                    }}
                  >
                    {/* Cover Wrap */}
                    <div className="bookmatch-cover-wrap">
                      <img
                        src={bookCover}
                        alt={book.title}
                        className="bookmatch-cover-img"
                        loading="lazy"
                        onError={(e) => {
                          const target = e.currentTarget;
                          target.src = generateFallbackCover(book.title, book.primary_author);
                        }}
                      />

                      {/* Match Badge */}
                      <div className="bookmatch-match-pill">
                        <Sparkles size={11} />
                        <span>
                          {book.algorithm_type === 'TRENDING'
                            ? 'Thịnh hành'
                            : `${matchPercent}% Phù hợp`}
                        </span>
                      </div>

                      {/* Stock availability */}
                      <div className="bookmatch-stock-tag">
                        Còn {book.available_stock} cuốn
                      </div>
                    </div>

                    {/* Book Details */}
                    <div className="bookmatch-card-info">
                      <div className="bookmatch-genre">
                        {book.category_name || 'Văn học'}
                      </div>

                      <h4 className="bookmatch-title" title={book.title}>
                        {book.title}
                      </h4>

                      <p className="bookmatch-author">
                        {book.primary_author || 'Nhiều tác giả'}
                      </p>

                      {/* Pricing */}
                      <div className="bookmatch-pricing">
                        <span className="price-primary">
                          {Number(book.price).toLocaleString('vi-VN')} đ
                        </span>
                        {book.original_price && Number(book.original_price) > Number(book.price) && (
                          <span className="price-original">
                            {Number(book.original_price).toLocaleString('vi-VN')} đ
                          </span>
                        )}
                      </div>

                      {/* AI Explanation Quote */}
                      <div className="bookmatch-ai-reason">
                        <div className="reason-label">
                          <Info size={11} />
                          <span>
                            {book.explanation_source === 'AI_GENERATED'
                              ? 'BookMatch AI nhận định:'
                              : 'Lý do đề xuất:'}
                          </span>
                        </div>
                        <p className="reason-text">"{book.explanation}"</p>
                      </div>

                      {/* Add to Cart Action */}
                      <div className="bookmatch-actions">
                        <button
                          type="button"
                          className="bookmatch-add-cart-btn"
                          disabled={addingBookId === book.book_id}
                          onClick={(e) => handleQuickAdd(book, e)}
                        >
                          {addedBookId === book.book_id ? (
                            <>
                              <CheckCircle2 size={14} />
                              <span>Đã thêm</span>
                            </>
                          ) : (
                            <>
                              <ShoppingBag size={14} />
                              <span>
                                {addingBookId === book.book_id
                                  ? 'Đang thêm...'
                                  : 'Thêm giỏ'}
                              </span>
                            </>
                          )}
                        </button>

                        {onSelectBook && (
                          <button
                            type="button"
                            className="bookmatch-view-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectBook(book.book_id);
                            }}
                            title="Xem chi tiết sách"
                          >
                            <ChevronRight size={16} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bookmatch-empty-box">
              <BookOpen size={36} className="text-muted" />
              <p>Hiện chưa có đề xuất phù hợp cho tiêu chí này.</p>
            </div>
          )}

          {/* Footer Disclaimer */}
          <div className="bookmatch-footer-note">
            <span>{data?.disclaimer}</span>
            <span className="highlight-tag">100% Sách Thật • Tồn Kho Xác Thực</span>
          </div>
        </div>
      )}
    </section>
  );
};
