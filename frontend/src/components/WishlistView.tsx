import React from 'react';
import { Heart, ShoppingCart, Trash2, BookOpen, AlertCircle } from 'lucide-react';
import { useCommerce } from '../context/CommerceContext';
import { formatVND } from '../services/catalogApi';

interface WishlistViewProps {
  onExploreStore: () => void;
}

export const WishlistView: React.FC<WishlistViewProps> = ({ onExploreStore }) => {
  const { wishlist, removeFromWishlist, moveWishlistToCart } = useCommerce();

  return (
    <div className="wishlist-page" data-testid="wishlist-view">
      <div className="section-header">
        <div className="section-title-wrap">
          <Heart size={24} className="text-gold" fill="currentColor" />
          <div>
            <h2 className="section-title">Danh Sách Yêu Thích</h2>
            <p className="section-subtitle">
              Lưu giữ những tác phẩm bạn quan tâm để dễ dàng theo dõi và đặt hàng sau này.
            </p>
          </div>
        </div>
      </div>

      {!wishlist || wishlist.items.length === 0 ? (
        <div className="empty-state-box">
          <Heart size={48} className="text-muted" />
          <h3>Danh sách yêu thích đang trống</h3>
          <p>
            Bạn chưa lưu tác phẩm nào. Hãy khám phá kho tàng sách của Novelia và nhấn biểu tượng trái tim để lưu lại.
          </p>
          <button
            type="button"
            className="action-btn-primary"
            onClick={onExploreStore}
          >
            <BookOpen size={16} /> Khám phá Cửa hàng sách
          </button>
        </div>
      ) : (
        <div className="wishlist-grid">
          {wishlist.items.map((item) => (
            <div key={item.id} className="wishlist-card" data-testid={`wishlist-item-${item.book_id}`}>
              <div className="wishlist-cover-wrap">
                <img
                  src={item.cover_image_url}
                  alt={item.book_title}
                  className="wishlist-cover"
                />
              </div>

              <div className="wishlist-card-body">
                <h4 className="wishlist-book-title" title={item.book_title}>
                  {item.book_title}
                </h4>

                <div className="wishlist-price-row">
                  <span className="price-current">{formatVND(item.price)}</span>
                  {item.original_price && item.original_price > item.price && (
                    <span className="price-original">
                      {formatVND(item.original_price)}
                    </span>
                  )}
                </div>

                <div className="wishlist-stock-status">
                  {item.is_in_stock ? (
                    <span className="stock-in">Còn {item.available_stock} cuốn</span>
                  ) : (
                    <span className="stock-out">
                      <AlertCircle size={12} /> Hết hàng
                    </span>
                  )}
                </div>

                <div className="wishlist-actions">
                  <button
                    type="button"
                    className="action-btn-primary btn-sm"
                    disabled={!item.is_in_stock}
                    onClick={() => moveWishlistToCart(item.book_id)}
                  >
                    <ShoppingCart size={15} /> Chuyển vào giỏ
                  </button>

                  <button
                    type="button"
                    className="action-btn-icon"
                    onClick={() => removeFromWishlist(item.book_id)}
                    title="Xóa khỏi yêu thích"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
