import React, { useState, useEffect, useCallback } from 'react';
import {
  Package,
  Calendar,
  MapPin,
  CreditCard,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Truck,
  Loader2,
  XCircle,
  FileText,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { formatVND } from '../services/catalogApi';
import * as commerceApi from '../services/commerceApi';
import * as shippingApi from '../services/shippingApi';
import { Order, OrderStatus } from '../types/commerce';
import { ShipmentDetail } from '../types/shipping';

const STATUS_CONFIG: Record<
  OrderStatus,
  { label: string; className: string; icon: React.ReactNode }
> = {
  PENDING: {
    label: 'Chờ xử lý',
    className: 'badge-pending',
    icon: <Clock size={14} />,
  },
  CONFIRMED: {
    label: 'Đã xác nhận',
    className: 'badge-confirmed',
    icon: <CheckCircle2 size={14} />,
  },
  PROCESSING: {
    label: 'Đang đóng gói',
    className: 'badge-processing',
    icon: <Package size={14} />,
  },
  SHIPPING: {
    label: 'Đang vận chuyển',
    className: 'badge-shipping',
    icon: <Truck size={14} />,
  },
  COMPLETED: {
    label: 'Giao thành công',
    className: 'badge-completed',
    icon: <CheckCircle2 size={14} />,
  },
  CANCELLED: {
    label: 'Đã hủy bỏ',
    className: 'badge-cancelled',
    icon: <XCircle size={14} />,
  },
};

export const OrderHistoryView: React.FC = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');

  // Cancel modal state
  const [cancellingOrder, setCancellingOrder] = useState<Order | null>(null);
  const [cancelReason, setCancelReason] = useState<string>('');
  const [submittingCancel, setSubmittingCancel] = useState<boolean>(false);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Tracking modal state
  const [trackingOrder, setTrackingOrder] = useState<Order | null>(null);
  const [trackingDetail, setTrackingDetail] = useState<ShipmentDetail | null>(null);
  const [loadingTracking, setLoadingTracking] = useState<boolean>(false);
  const [trackingError, setTrackingError] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await commerceApi.fetchMyOrders(
        token,
        1,
        20,
        selectedStatus === 'ALL' ? undefined : selectedStatus
      );
      setOrders(data.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Không thể tải lịch sử đơn hàng.');
    } finally {
      setLoading(false);
    }
  }, [token, selectedStatus]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleOpenCancel = (order: Order) => {
    setCancellingOrder(order);
    setCancelReason('');
    setCancelError(null);
  };

  const handleConfirmCancel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !cancellingOrder) return;
    if (!cancelReason.trim()) {
      setCancelError('Vui lòng nhập lý do hủy đơn hàng.');
      return;
    }

    setSubmittingCancel(true);
    setCancelError(null);
    try {
      const updated = await commerceApi.cancelOrder(
        token,
        cancellingOrder.order_code,
        cancelReason.trim()
      );
      setActionSuccess(`Đã hủy thành công đơn hàng ${updated.order_code}. Tồn kho giữ hàng đã được hoàn trả.`);
      setCancellingOrder(null);
      // Refresh list
      await fetchOrders();
      setTimeout(() => setActionSuccess(null), 6000);
    } catch (err: unknown) {
      setCancelError(err instanceof Error ? err.message : 'Lỗi hủy đơn hàng');
    } finally {
      setSubmittingCancel(false);
    }
  };

  // Open Tracking details
  const handleOpenTracking = async (order: Order) => {
    if (!token) return;
    setTrackingOrder(order);
    setTrackingDetail(null);
    setLoadingTracking(true);
    setTrackingError(null);

    try {
      const detail = await shippingApi.fetchOrderTracking(token, order.order_code);
      setTrackingDetail(detail);
    } catch (err: unknown) {
      setTrackingError(
        err instanceof Error ? err.message : 'Không thể tải hành trình vận chuyển.'
      );
    } finally {
      setLoadingTracking(false);
    }
  };

  return (
    <div className="order-history-page" data-testid="order-history-view">
      {/* Top Banner */}
      <div className="order-history-header">
        <div className="header-text-wrap">
          <div className="flex-center gap-2">
            <Package size={24} className="text-gold" />
            <h2>Đơn Hàng Của Tôi</h2>
          </div>
          <p className="subtitle">
            Theo dõi hành trình đơn hàng, tra cứu mã vận đơn GHN / GHTK và bảo vệ quyền lợi người mua.
          </p>
        </div>
        <button
          type="button"
          className="btn-refresh-orders"
          onClick={fetchOrders}
          disabled={loading}
          title="Làm mới danh sách"
        >
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
          <span>Làm mới</span>
        </button>
      </div>

      {actionSuccess && (
        <div className="order-alert-banner alert-success">
          <CheckCircle2 size={18} />
          <span>{actionSuccess}</span>
        </div>
      )}

      {error && (
        <div className="order-alert-banner alert-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="order-status-tabs">
        {[
          { key: 'ALL', label: 'Tất cả đơn' },
          { key: 'PENDING', label: 'Chờ xử lý' },
          { key: 'CONFIRMED', label: 'Đã xác nhận' },
          { key: 'PROCESSING', label: 'Đang đóng gói' },
          { key: 'SHIPPING', label: 'Đang vận chuyển' },
          { key: 'COMPLETED', label: 'Giao thành công' },
          { key: 'CANCELLED', label: 'Đã hủy' },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`status-tab-btn ${selectedStatus === tab.key ? 'tab-active' : ''}`}
            onClick={() => setSelectedStatus(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Orders List */}
      <div className="orders-container">
        {loading && (
          <div className="orders-loading-state">
            <Loader2 size={36} className="spin text-gold" />
            <p>Đang tải danh sách đơn hàng từ MySQL...</p>
          </div>
        )}

        {!loading && orders.length === 0 && (
          <div className="orders-empty-state">
            <Package size={52} className="text-muted" />
            <h3>Chưa có đơn hàng nào</h3>
            <p>
              {selectedStatus === 'ALL'
                ? 'Bạn chưa đặt mua cuốn sách nào. Hãy dạo qua thư viện để chọn tác phẩm yêu thích.'
                : `Không có đơn hàng nào ở trạng thái '${selectedStatus}'.`}
            </p>
          </div>
        )}

        {!loading &&
          orders.map((order) => {
            const statusMeta =
              STATUS_CONFIG[order.status] || {
                label: order.status,
                className: 'badge-pending',
                icon: <Clock size={14} />,
              };
            const canCancel = order.status === 'PENDING';

            return (
              <div
                key={order.id}
                className="order-card"
                data-testid={`order-card-${order.order_code}`}
              >
                {/* Order Card Header */}
                <div className="order-card-header">
                  <div className="order-meta-left">
                    <span className="order-code-badge">
                      <FileText size={14} className="text-gold" />
                      <strong>{order.order_code}</strong>
                    </span>
                    <span className="order-date">
                      <Calendar size={13} />
                      {new Date(order.created_at).toLocaleDateString('vi-VN', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>

                  <div className="order-status-badge-wrap flex-center gap-2">
                    {order.shipment_tracking_code && (
                      <span className="carrier-pill" title="Mã vận đơn bưu cục">
                        <Truck size={12} className="text-gold" />
                        <span>{order.shipment_carrier}: {order.shipment_tracking_code}</span>
                      </span>
                    )}
                    <span className={`status-badge ${statusMeta.className}`}>
                      {statusMeta.icon}
                      <span>{statusMeta.label}</span>
                    </span>
                  </div>
                </div>

                {/* Line Items Snapshot */}
                <div className="order-items-list">
                  {order.items.map((item) => (
                    <div key={item.id} className="order-item-row">
                      <div className="item-details">
                        <div className="item-title">{item.book_title_snapshot}</div>
                        <div className="item-subinfo">
                          <span>ISBN: {item.book_isbn_snapshot}</span>
                          <span>&bull;</span>
                          <span>SKU: {item.book_sku_snapshot}</span>
                        </div>
                      </div>
                      <div className="item-calc">
                        <span className="item-qty">x{item.quantity}</span>
                        <span className="item-price">{formatVND(item.price_at_purchase)}</span>
                        <span className="item-subtotal-bold">{formatVND(item.subtotal)}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Card Footer Breakdown & Actions */}
                <div className="order-card-footer">
                  <div className="delivery-summary">
                    <div className="info-line">
                      <MapPin size={14} className="text-muted" />
                      <span>
                        Giao đến: <strong>{order.recipient_name}</strong> ({order.recipient_phone}) —{' '}
                        {order.shipping_street_address}, {order.shipping_ward}, {order.shipping_district},{' '}
                        {order.shipping_province}
                      </span>
                    </div>
                    <div className="info-line">
                      <CreditCard size={14} className="text-muted" />
                      <span>
                        Phương thức: <strong>{order.payment_method || 'COD'}</strong> | Trạng thái: <strong>{order.payment_status || 'PENDING'}</strong>
                      </span>
                    </div>
                    {order.cancelled_reason && (
                      <div className="info-line text-cancelled">
                        <XCircle size={14} />
                        <span>Lý do hủy: {order.cancelled_reason}</span>
                      </div>
                    )}
                  </div>

                  <div className="order-totals-and-actions">
                    <div className="order-total-price">
                      <span className="total-label">Tổng thanh toán:</span>
                      <span className="total-gold-price">{formatVND(order.total_amount)}</span>
                    </div>

                    <div className="order-btn-actions flex-center gap-2">
                      {order.shipment_tracking_code && (
                        <button
                          type="button"
                          className="btn-track-order"
                          onClick={() => handleOpenTracking(order)}
                          data-testid={`track-btn-${order.order_code}`}
                          title="Xem hành trình giao hàng"
                        >
                          <Truck size={14} />
                          <span>Hành trình đơn</span>
                        </button>
                      )}

                      {canCancel && (
                        <button
                          type="button"
                          className="btn-cancel-order"
                          onClick={() => handleOpenCancel(order)}
                          data-testid={`cancel-btn-${order.order_code}`}
                        >
                          <XCircle size={15} />
                          <span>Hủy đơn hàng</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
      </div>

      {/* Cancel Order Confirmation Modal */}
      {cancellingOrder && (
        <div
          className="checkout-modal-backdrop"
          onClick={() => setCancellingOrder(null)}
          data-testid="cancel-modal-backdrop"
        >
          <div
            className="cancel-modal-container"
            onClick={(e) => e.stopPropagation()}
            data-testid="cancel-order-modal"
          >
            <div className="cancel-modal-header">
              <div className="flex-center gap-2">
                <AlertTriangle size={20} className="text-warning" />
                <h3>Hủy Đơn Hàng {cancellingOrder.order_code}</h3>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setCancellingOrder(null)}
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleConfirmCancel} className="cancel-modal-body">
              <p className="cancel-notice">
                Khi hủy đơn hàng, toàn bộ các cuốn sách đang được tạm khóa giữ (Reserved Stock) sẽ được giải phóng ngay lập tức về kho hàng khả dụng. Mã giảm giá (nếu có) sẽ được hoàn trả cho bạn.
              </p>

              <div className="form-group">
                <label className="input-label">Lý do hủy đơn hàng *</label>
                <textarea
                  className="form-input"
                  rows={3}
                  required
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="Ví dụ: Tôi muốn thay đổi địa chỉ nhận hàng, đặt nhầm số lượng..."
                  disabled={submittingCancel}
                />
              </div>

              {cancelError && (
                <div className="order-alert-banner alert-error">
                  <AlertTriangle size={16} />
                  <span>{cancelError}</span>
                </div>
              )}

              <div className="cancel-modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setCancellingOrder(null)}
                  disabled={submittingCancel}
                >
                  Giữ lại đơn hàng
                </button>
                <button
                  type="submit"
                  className="btn-danger"
                  disabled={submittingCancel || !cancelReason.trim()}
                  data-testid="confirm-cancel-btn"
                >
                  {submittingCancel ? (
                    <>
                      <Loader2 size={16} className="spin" />
                      <span>Đang xử lý hủy...</span>
                    </>
                  ) : (
                    <span>Xác nhận Hủy Đơn</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Customer Tracking Timeline Modal */}
      {trackingOrder && (
        <div
          className="checkout-modal-backdrop"
          onClick={() => setTrackingOrder(null)}
          data-testid="customer-tracking-modal-backdrop"
        >
          <div
            className="cancel-modal-container tracking-modal-container"
            onClick={(e) => e.stopPropagation()}
            data-testid="customer-tracking-modal"
          >
            <div className="cancel-modal-header">
              <div className="flex-center gap-2">
                <Truck size={20} className="text-gold" />
                <h3>Hành Trình Giao Hàng — {trackingOrder.order_code}</h3>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setTrackingOrder(null)}
              >
                &times;
              </button>
            </div>

            <div className="cancel-modal-body">
              {loadingTracking ? (
                <div className="orders-loading-state">
                  <Loader2 size={32} className="spin text-gold" />
                  <p>Đang tải hành trình từ đối tác vận chuyển...</p>
                </div>
              ) : trackingError ? (
                <div className="order-alert-banner alert-error">
                  <AlertTriangle size={16} />
                  <span>{trackingError}</span>
                </div>
              ) : trackingDetail ? (
                <div className="tracking-content">
                  {/* Summary Metric */}
                  <div className="tracking-summary-card">
                    <div className="tracking-metric">
                      <span className="metric-label">Đối tác giao nhận</span>
                      <strong className="metric-val">{trackingDetail.carrier}</strong>
                    </div>
                    <div className="tracking-metric">
                      <span className="metric-label">Mã vận đơn</span>
                      <strong className="metric-val text-gold">{trackingDetail.tracking_code}</strong>
                    </div>
                    <div className="tracking-metric">
                      <span className="metric-label">Trạng thái</span>
                      <span className="shipment-status-chip">{trackingDetail.status_label}</span>
                    </div>
                  </div>

                  <div className="tracking-submeta">
                    <div className="submeta-row">
                      <MapPin size={14} className="text-muted" />
                      <span>Địa chỉ nhận: {trackingDetail.recipient_name} — {trackingDetail.shipping_address}</span>
                    </div>
                    {trackingDetail.estimated_delivery_date && (
                      <div className="submeta-row">
                        <Calendar size={14} className="text-muted" />
                        <span>Dự kiến giao: <strong>{new Date(trackingDetail.estimated_delivery_date).toLocaleDateString('vi-VN')}</strong></span>
                      </div>
                    )}
                  </div>

                  {/* Vertical Checkpoints Timeline */}
                  <div className="tracking-timeline-wrap">
                    <h4 className="timeline-title">Tiến Độ Chuyển Phát</h4>
                    {trackingDetail.events.length === 0 ? (
                      <p className="text-muted text-sm">Chưa có mốc sự kiện nào được ghi nhận.</p>
                    ) : (
                      <div className="tracking-timeline">
                        {trackingDetail.events.map((ev, idx) => (
                          <div key={ev.id || idx} className="timeline-step">
                            <div className="timeline-marker" />
                            <div className="timeline-step-content">
                              <div className="timeline-step-header">
                                <span className="step-time">
                                  <Clock size={12} />
                                  {new Date(ev.occurred_at).toLocaleString('vi-VN')}
                                </span>
                                <span className="step-status-tag">{ev.status}</span>
                              </div>
                              <div className="step-description">{ev.description}</div>
                              {ev.location && (
                                <div className="step-location">
                                  <MapPin size={12} />
                                  <span>{ev.location}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ) : null}

              <div className="cancel-modal-actions mt-3">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setTrackingOrder(null)}
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
