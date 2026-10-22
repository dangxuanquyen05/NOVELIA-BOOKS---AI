import React from 'react';
import {
  X,
  ShoppingCart,
  Trash2,
  Plus,
  Minus,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
} from 'lucide-react';
import { useCommerce } from '../context/CommerceContext';
import { formatVND } from '../services/catalogApi';

export const CartDrawer: React.FC = () => {
  const {
    cart,
    cartLoading,
    cartError,
    isCartOpen,
    closeCart,
    openCheckout,
    updateCartQuantity,
    removeFromCart,
    clearCart,
  } = useCommerce();

  if (!isCartOpen) return null;

  return (
    <div
      className="cart-drawer-backdrop"
      onClick={closeCart}
      data-testid="cart-drawer-backdrop"
    >
      <div
        className="cart-drawer-container cart-drawer"
        onClick={(e) => e.stopPropagation()}
        data-testid="cart-drawer"
      >
        {/* Header */}
        <div className="cart-drawer-header">
          <div className="cart-drawer-title-wrap">
            <ShoppingCart size={20} className="text-gold" />
            <h3 className="cart-drawer-title">
              Giỏ Hàng ({cart?.total_items || 0})
            </h3>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={closeCart}
            aria-label="Đóng giỏ hàng"
          >
            <X size={20} />
          </button>
        </div>

        {/* Free Shipping Progress */}
        <div className="free-shipping-bar">
          <ShieldCheck size={16} className="text-gold" />
          <span>Miễn phí vận chuyển cho đơn hàng từ 250.000 ₫</span>
        </div>

        {cartError && (
          <div className="cart-error-banner">
            <AlertTriangle size={16} />
            <span>{cartError}</span>
          </div>
        )}

        {/* Cart Items List */}
        <div className="cart-drawer-body">
          {!cart || cart.items.length === 0 ? (
            <div className="empty-cart-box">
              <ShoppingCart size={48} className="text-muted" />
              <h4>Giỏ hàng đang trống</h4>
              <p>Khám phá các tác phẩm đặc sắc và thêm vào giỏ hàng ngay hôm nay.</p>
              <button
                type="button"
                className="action-btn-primary"
                onClick={closeCart}
              >
                Tiếp tục mua sắm
              </button>
            </div>
          ) : (
            <div className="cart-items-list">
              {cart.items.map((item) => (
                <div key={item.id} className="cart-item-card cart-item-row" data-testid={`cart-item-${item.book_id}`}>
                  <img
                    src={item.cover_image_url}
                    alt={item.book_title}
                    className="cart-item-thumb cart-item-img"
                  />
                  <div className="cart-item-info">
                    <h5 className="cart-item-title" title={item.book_title}>
                      {item.book_title}
                    </h5>
                    <div className="cart-item-prices">
                      <span className="cart-unit-price">
                        {formatVND(item.unit_price)}
                      </span>
                      {item.discount_percent > 0 && (
                        <span className="cart-orig-price">
                          {formatVND(item.original_price)}
                        </span>
                      )}
                    </div>

                    {/* Stock Alert Warning */}
                    {!item.is_available && (
                      <div className="cart-stock-warning">
                        <AlertTriangle size={13} />
                        <span>
                          {item.available_stock > 0
                            ? `Chỉ còn ${item.available_stock} cuốn`
                            : 'Đã hết hàng'}
                        </span>
                      </div>
                    )}

                    {/* Quantity Stepper & Remove */}
                    <div className="cart-item-actions">
                      <div className="qty-stepper">
                        <button
                          type="button"
                          className="qty-btn"
                          disabled={item.quantity <= 1 || cartLoading}
                          onClick={() =>
                            updateCartQuantity(item.book_id, item.quantity - 1)
                          }
                          aria-label="Giảm số lượng"
                        >
                          <Minus size={13} />
                        </button>
                        <span className="qty-value">{item.quantity}</span>
                        <button
                          type="button"
                          className="qty-btn"
                          disabled={
                            item.quantity >= item.available_stock || cartLoading
                          }
                          onClick={() =>
                            updateCartQuantity(item.book_id, item.quantity + 1)
                          }
                          aria-label="Tăng số lượng"
                        >
                          <Plus size={13} />
                        </button>
                      </div>

                      <button
                        type="button"
                        className="cart-remove-btn"
                        onClick={() => removeFromCart(item.book_id)}
                        disabled={cartLoading}
                        title="Xóa khỏi giỏ hàng"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer Summary */}
        {cart && cart.items.length > 0 && (
          <div className="cart-drawer-footer">
            <div className="cart-subtotal-row">
              <span className="subtotal-label">Tổng cộng tạm tính:</span>
              <span className="subtotal-amount">
                {formatVND(cart.subtotal_amount)}
              </span>
            </div>

            <div className="cart-footer-buttons">
              <button
                type="button"
                className="checkout-btn cart-checkout-btn"
                data-testid="proceed-to-checkout-btn"
                disabled={cart.has_stock_issues || cartLoading}
                onClick={openCheckout}
              >
                <span>Tiến hành Đặt hàng</span>
                <ArrowRight size={17} />
              </button>

              <button
                type="button"
                className="cart-clear-btn"
                onClick={clearCart}
                disabled={cartLoading}
              >
                <RotateCcw size={14} /> Làm trống giỏ
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
