import React, { useEffect, useState, useCallback } from 'react';
import {
  Star,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Send,
  MessageSquare,
} from 'lucide-react';
import { useSafeAuth } from '../context/AuthContext';
import { BookReviewSummary, Review } from '../types/commerce';
import * as commerceApi from '../services/commerceApi';

interface ReviewSectionProps {
  bookId: number;
}

export const ReviewSection: React.FC<ReviewSectionProps> = ({ bookId }) => {
  const { user, token, isAuthenticated } = useSafeAuth();
  const [summary, setSummary] = useState<BookReviewSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [rating, setRating] = useState<number>(5);
  const [hoverRating, setHoverRating] = useState<number>(0);
  const [title, setTitle] = useState<string>('');
  const [comment, setComment] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const loadReviews = useCallback(async () => {
    setLoading(true);
    try {
      const data = await commerceApi.fetchBookReviews(bookId);
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể tải đánh giá');
    } finally {
      setLoading(false);
    }
  }, [bookId]);

  useEffect(() => {
    loadReviews();
  }, [loadReviews]);

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !isAuthenticated) {
      setFormError('Vui lòng đăng nhập để gửi bài đánh giá.');
      return;
    }

    if (comment.trim().length < 10) {
      setFormError('Nội dung đánh giá cần ít nhất 10 ký tự.');
      return;
    }

    setSubmitting(true);
    setFormError(null);
    setFormSuccess(null);

    try {
      await commerceApi.createBookReview(token, bookId, {
        rating,
        title: title.trim() || undefined,
        comment: comment.trim(),
      });
      setFormSuccess('Cảm ơn bạn! Đánh giá đã được ghi nhận thành công.');
      setTitle('');
      setComment('');
      setRating(5);
      await loadReviews();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Lỗi gửi đánh giá');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteReview = async (reviewId: number) => {
    if (!token) return;
    if (!confirm('Bạn có chắc chắn muốn xóa bài đánh giá này không?')) return;
    try {
      await commerceApi.deleteBookReview(token, reviewId);
      await loadReviews();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Lỗi xóa đánh giá');
    }
  };

  const isUserReviewAuthor = (rev: Review): boolean => {
    if (!user) return false;
    return rev.user_id === user.id || user.roles.includes('ADMIN');
  };

  return (
    <div className="review-section" data-testid="review-section">
      <div className="review-section-header">
        <h4 className="specs-title">
          <MessageSquare size={16} /> Đánh Giá &amp; Nhận Xét Từ Độc Giả
        </h4>
      </div>

      {loading ? (
        <div className="loading-state-box">
          <div className="spinner-large" />
          <p>Đang tải nhận xét...</p>
        </div>
      ) : error ? (
        <div className="empty-state-box">
          <AlertCircle size={24} color="var(--status-error)" />
          <p>{error}</p>
        </div>
      ) : (
        <div className="review-layout">
          {/* Summary Breakdown */}
          <div className="review-summary-card">
            <div className="score-box">
              <span className="big-score">
                {summary ? summary.average_rating.toFixed(1) : '0.0'}
              </span>
              <div className="stars-row">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    size={16}
                    className={
                      summary && star <= Math.round(summary.average_rating)
                        ? 'star-filled'
                        : 'star-empty'
                    }
                  />
                ))}
              </div>
              <span className="total-rev-count">
                {summary?.total_reviews || 0} bài đánh giá
              </span>
            </div>

            {/* Distribution Bars */}
            <div className="rating-bars">
              {[5, 4, 3, 2, 1].map((stars) => {
                const count = summary?.rating_distribution?.[String(stars)] ?? 0;
                const total = summary?.total_reviews || 1;
                const pct = summary?.total_reviews ? (count / total) * 100 : 0;

                return (
                  <div key={stars} className="rating-bar-row">
                    <span className="bar-label">{stars} sao</span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="bar-count">({count})</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Submission Form */}
          <div className="review-form-card">
            <h5 className="form-title">Gửi nhận xét của bạn</h5>
            {isAuthenticated ? (
              <form onSubmit={handleSubmitReview} className="review-form">
                {/* Star Picker */}
                <div className="star-picker-row">
                  <span className="picker-label">Mức độ hài lòng:</span>
                  <div className="star-picker">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        type="button"
                        key={star}
                        className="star-pick-btn"
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(0)}
                        onClick={() => setRating(star)}
                        aria-label={`Đánh giá ${star} sao`}
                      >
                        <Star
                          size={22}
                          className={
                            star <= (hoverRating || rating)
                              ? 'star-filled'
                              : 'star-empty'
                          }
                        />
                      </button>
                    ))}
                    <span className="rating-text-hint">
                      {rating === 5 && 'Tuyệt tác bất hủ'}
                      {rating === 4 && 'Rất đáng đọc'}
                      {rating === 3 && 'Tác phẩm hay'}
                      {rating === 2 && 'Bình thường'}
                      {rating === 1 && 'Chưa hài lòng'}
                    </span>
                  </div>
                </div>

                <div className="form-field">
                  <input
                    type="text"
                    placeholder="Tiêu đề bài nhận xét (tùy chọn)"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="form-input"
                    maxLength={150}
                  />
                </div>

                <div className="form-field">
                  <textarea
                    placeholder="Chia sẻ cảm nhận chi tiết của bạn về nội dung, nhân vật, hành văn (tối thiểu 10 ký tự)..."
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    className="form-textarea"
                    rows={4}
                    required
                  />
                  <span className="char-count">
                    {comment.length} / 2000 ký tự (tối thiểu 10)
                  </span>
                </div>

                {formError && (
                  <div className="form-alert-error">
                    <AlertCircle size={15} />
                    <span>{formError}</span>
                  </div>
                )}

                {formSuccess && (
                  <div className="form-alert-success">
                    <CheckCircle2 size={15} />
                    <span>{formSuccess}</span>
                  </div>
                )}

                <button
                  type="submit"
                  className="action-btn-primary"
                  disabled={submitting || comment.trim().length < 10}
                >
                  <Send size={15} />
                  <span>{submitting ? 'Đang gửi...' : 'Gửi nhận xét'}</span>
                </button>
              </form>
            ) : (
              <div className="login-to-review-hint">
                <AlertCircle size={18} className="text-gold" />
                <p>
                  Vui lòng <strong>đăng nhập</strong> tài khoản để gửi bài nhận xét và chia sẻ góc nhìn cùng cộng đồng độc giả Novelia.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Review List */}
      <div className="review-list">
        {summary && summary.reviews.length > 0 ? (
          summary.reviews.map((rev) => (
            <div key={rev.id} className="review-item-card" data-testid={`review-item-${rev.id}`}>
              <div className="review-item-header">
                <div className="reviewer-meta">
                  <div className="reviewer-avatar">
                    {(rev.user_name || 'Độc giả').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <span className="reviewer-name">{rev.user_name || 'Độc giả'}</span>
                    {rev.is_verified_purchase && (
                      <span className="verified-badge">
                        <CheckCircle2 size={12} /> Đã mua sách tại Novelia
                      </span>
                    )}
                  </div>
                </div>

                <div className="review-item-actions">
                  <div className="stars-row">
                    {[1, 2, 3, 4, 5].map((s) => (
                      <Star
                        key={s}
                        size={14}
                        className={s <= rev.rating ? 'star-filled' : 'star-empty'}
                      />
                    ))}
                  </div>

                  {isUserReviewAuthor(rev) && (
                    <button
                      type="button"
                      className="delete-review-btn"
                      onClick={() => handleDeleteReview(rev.id)}
                      title="Xóa đánh giá này"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>

              {rev.title && <h6 className="review-title">{rev.title}</h6>}
              <p className="review-comment">{rev.comment}</p>
              <span className="review-date">
                {new Date(rev.created_at).toLocaleDateString('vi-VN')}
              </span>
            </div>
          ))
        ) : (
          <div className="no-reviews-note">
            Chưa có bài nhận xét nào. Hãy là người đầu tiên chia sẻ cảm nghĩ về cuốn sách này!
          </div>
        )}
      </div>
    </div>
  );
};
