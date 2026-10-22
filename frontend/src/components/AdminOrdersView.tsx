import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldAlert,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Package,
  Loader2,
  RefreshCw,
  Edit,
  Truck,
  ExternalLink,
  MapPin,
  Calendar,
  Clock,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { formatVND } from '../services/catalogApi';
import * as commerceApi from '../services/commerceApi';
import * as shippingApi from '../services/shippingApi';
import { Order, OrderStatus } from '../types/commerce';
import { ShipmentDetail, ShippingProviderStatus } from '../types/shipping';

const STATUS_LABELS: Record<OrderStatus, { label: string; color: string }> = {
  PENDING: { label: 'Chờ xử lý', color: 'badge-pending' },
  CONFIRMED: { label: 'Đã xác nhận', color: 'badge-confirmed' },
  PROCESSING: { label: 'Đang đóng gói', color: 'badge-processing' },
  SHIPPING: { label: 'Đang vận chuyển', color: 'badge-shipping' },
  COMPLETED: { label: 'Giao thành công', color: 'badge-completed' },
  CANCELLED: { label: 'Đã hủy', color: 'badge-cancelled' },
};

export const AdminOrdersView: React.FC = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  // Status transition modal
  const [activeOrder, setActiveOrder] = useState<Order | null>(null);
  const [targetStatus, setTargetStatus] = useState<string>('CONFIRMED');
  const [staffNotes, setStaffNotes] = useState<string>('');
  const [cancellationReason, setCancellationReason] = useState<string>('');
  const [updating, setUpdating] = useState<boolean>(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  // Shipping Provider & Dispatch Modal
  const [providerStatuses, setProviderStatuses] = useState<ShippingProviderStatus[]>([]);
  const [dispatchOrderTarget, setDispatchOrderTarget] = useState<Order | null>(null);
  const [dispatchCarrier, setDispatchCarrier] = useState<string>('GHN');
  const [dispatchWeight, setDispatchWeight] = useState<number>(500);
  const [dispatchLength, setDispatchLength] = useState<number>(20);
  const [dispatchWidth, setDispatchWidth] = useState<number>(15);
  const [dispatchHeight, setDispatchHeight] = useState<number>(5);
  const [dispatchNote, setDispatchNote] = useState<string>('CHOXEMHANGKHONGTHU');
  const [dispatchStaffNotes, setDispatchStaffNotes] = useState<string>('');
  const [dispatching, setDispatching] = useState<boolean>(false);
  const [dispatchError, setDispatchError] = useState<string | null>(null);

  // Tracking details modal
  const [trackingOrderTarget, setTrackingOrderTarget] = useState<Order | null>(null);
  const [trackingDetail, setTrackingDetail] = useState<ShipmentDetail | null>(null);
  const [loadingTracking, setLoadingTracking] = useState<boolean>(false);
  const [trackingError, setTrackingError] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await commerceApi.fetchAdminOrders(
        token,
        1,
        50,
        statusFilter === 'ALL' ? undefined : statusFilter,
        searchQuery || undefined
      );
      setOrders(data.items);
      setTotalCount(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Không thể tải danh sách quản trị đơn.');
    } finally {
      setLoading(false);
    }
  }, [token, statusFilter, searchQuery]);

  const fetchProviders = useCallback(async () => {
    try {
      const statuses = await shippingApi.fetchShippingProvidersStatus();
      setProviderStatuses(statuses);
    } catch {
      // Non-critical, fallback gracefully
    }
  }, []);

  useEffect(() => {
    fetchOrders();
    fetchProviders();
  }, [fetchOrders, fetchProviders]);

  const handleOpenStatusModal = (order: Order) => {
    setActiveOrder(order);
    setTargetStatus(order.status);
    setStaffNotes('');
    setCancellationReason('');
    setUpdateError(null);
  };

  const handleSaveStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !activeOrder) return;

    if (targetStatus === 'CANCELLED' && !cancellationReason.trim()) {
      setUpdateError('Bắt buộc phải nhập lý do khi hủy đơn hàng.');
      return;
    }

    setUpdating(true);
    setUpdateError(null);
    try {
      const updated = await commerceApi.updateOrderStatus(
        token,
        activeOrder.order_code,
        targetStatus,
        staffNotes.trim() || undefined,
        cancellationReason.trim() || undefined
      );
      setSuccessNotice(`Cập nhật đơn hàng ${updated.order_code} sang trạng thái '${updated.status}' thành công.`);
      setActiveOrder(null);
      await fetchOrders();
      setTimeout(() => setSuccessNotice(null), 5000);
    } catch (err: unknown) {
      setUpdateError(err instanceof Error ? err.message : 'Lỗi cập nhật trạng thái đơn');
    } finally {
      setUpdating(false);
    }
  };

  // Open Dispatch Modal
  const handleOpenDispatchModal = (order: Order) => {
    setDispatchOrderTarget(order);
    setDispatchCarrier('GHN');
    setDispatchWeight(500);
    setDispatchLength(20);
    setDispatchWidth(15);
    setDispatchHeight(5);
    setDispatchNote('CHOXEMHANGKHONGTHU');
    setDispatchStaffNotes('');
    setDispatchError(null);
  };

  // Submit Dispatch to Carrier
  const handleConfirmDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !dispatchOrderTarget) return;

    setDispatching(true);
    setDispatchError(null);
    try {
      const shipment = await shippingApi.dispatchOrder(token, dispatchOrderTarget.order_code, {
        carrier: dispatchCarrier as 'GHN' | 'GHTK' | 'MOCK',
        weight: Number(dispatchWeight),
        length: Number(dispatchLength),
        width: Number(dispatchWidth),
        height: Number(dispatchHeight),
        required_note: dispatchNote as 'CHOXEMHANGKHONGTHU' | 'CHOTHUHANG' | 'KHONGCHOXEMHANG',
        staff_notes: dispatchStaffNotes.trim() || undefined,
      });

      setSuccessNotice(
        `Đã tạo vận đơn thành công với ${shipment.carrier}! Mã vận đơn: ${shipment.tracking_code}. Trạng thái đơn chuyển sang SHIPPING.`
      );
      setDispatchOrderTarget(null);
      await fetchOrders();
      setTimeout(() => setSuccessNotice(null), 6000);
    } catch (err: unknown) {
      setDispatchError(
        err instanceof Error
          ? err.message
          : 'Lỗi tạo vận đơn. Vui lòng kiểm tra cấu hình đối tác vận chuyển.'
      );
    } finally {
      setDispatching(false);
    }
  };

  // Open Tracking Modal
  const handleOpenTrackingModal = async (order: Order) => {
    if (!token) return;
    setTrackingOrderTarget(order);
    setTrackingDetail(null);
    setLoadingTracking(true);
    setTrackingError(null);

    try {
      const detail = await shippingApi.fetchOrderTracking(token, order.order_code);
      setTrackingDetail(detail);
    } catch (err: unknown) {
      setTrackingError(
        err instanceof Error ? err.message : 'Không thể tải hành trình vận chuyển từ đối tác.'
      );
    } finally {
      setLoadingTracking(false);
    }
  };

  return (
    <div className="admin-orders-page" data-testid="admin-orders-view">
      {/* Top Banner */}
      <div className="admin-orders-header">
        <div className="header-text-wrap">
          <div className="flex-center gap-2">
            <ShieldAlert size={24} className="text-gold" />
            <h2>Quản Trị Đơn Hàng &amp; Điều Vận (Backoffice)</h2>
          </div>
          <p className="subtitle">
            Kiểm soát vòng đời đơn hàng, xác nhận giao dịch, điều vận đơn hàng với GHN / GHTK và kích hoạt trừ tồn kho vật lý.
          </p>
        </div>

        <div className="header-actions-wrap flex-center gap-2">
          {providerStatuses.length > 0 && (
            <div className="carrier-status-pills flex-center gap-1">
              {providerStatuses.map((p) => (
                <span
                  key={p.carrier}
                  className={`carrier-chip ${!p.is_live_ready ? 'chip-warning' : 'chip-ready'}`}
                  title={p.notes}
                >
                  <Truck size={12} />
                  <span>{p.carrier}: {!p.is_live_ready ? 'BLOCKED (Cần Token)' : 'SẴN SÀNG'}</span>
                </span>
              ))}
            </div>
          )}

          <button
            type="button"
            className="btn-refresh-orders"
            onClick={() => {
              fetchOrders();
              fetchProviders();
            }}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {successNotice && (
        <div className="order-alert-banner alert-success">
          <CheckCircle2 size={18} />
          <span>{successNotice}</span>
        </div>
      )}

      {error && (
        <div className="order-alert-banner alert-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Search & Filter Toolbar */}
      <div className="admin-filter-toolbar">
        <div className="search-input-wrap">
          <Search size={16} className="text-muted search-icon" />
          <input
            type="text"
            className="form-input search-input"
            placeholder="Tìm theo mã đơn (NVL-...), tên khách, SĐT..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-select-wrap">
          <Filter size={16} className="text-muted" />
          <select
            className="form-input select-status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">Tất cả trạng thái</option>
            <option value="PENDING">Chờ xử lý (PENDING)</option>
            <option value="CONFIRMED">Đã xác nhận (CONFIRMED)</option>
            <option value="PROCESSING">Đang đóng gói (PROCESSING)</option>
            <option value="SHIPPING">Đang vận chuyển (SHIPPING)</option>
            <option value="COMPLETED">Giao thành công (COMPLETED)</option>
            <option value="CANCELLED">Đã hủy (CANCELLED)</option>
          </select>
        </div>

        <span className="count-badge">Tổng: {totalCount} đơn</span>
      </div>

      {/* Orders Table */}
      <div className="admin-table-card">
        {loading ? (
          <div className="orders-loading-state">
            <Loader2 size={36} className="spin text-gold" />
            <p>Đang tải dữ liệu đơn hàng...</p>
          </div>
        ) : orders.length === 0 ? (
          <div className="orders-empty-state">
            <Package size={48} className="text-muted" />
            <h3>Không tìm thấy đơn hàng nào</h3>
            <p>Thử thay đổi từ khóa tìm kiếm hoặc bộ lọc trạng thái.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="admin-orders-table" data-testid="admin-orders-table">
              <thead>
                <tr>
                  <th>Mã đơn</th>
                  <th>Thời gian</th>
                  <th>Khách hàng &amp; Giao hàng</th>
                  <th>Thanh toán</th>
                  <th>Tổng tiền</th>
                  <th>Trạng thái &amp; Vận đơn</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => {
                  const statusInfo = STATUS_LABELS[o.status] || {
                    label: o.status,
                    color: 'badge-pending',
                  };
                  const canDispatch =
                    (o.status === 'CONFIRMED' || o.status === 'PROCESSING') &&
                    !o.shipment_tracking_code;

                  return (
                    <tr key={o.id}>
                      <td>
                        <span className="order-code-text">{o.order_code}</span>
                      </td>
                      <td>
                        <div className="table-date">
                          {new Date(o.created_at).toLocaleDateString('vi-VN', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                      </td>
                      <td>
                        <div className="customer-info-cell">
                          <strong>{o.recipient_name}</strong> ({o.recipient_phone})
                          <div className="addr-snippet">
                            {o.shipping_street_address}, {o.shipping_ward}, {o.shipping_district}
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="payment-cell">
                          <span>{o.payment_method || 'COD'}</span>
                          <span className={`pay-status-pill pay-${(o.payment_status || 'PENDING').toLowerCase()}`}>
                            {o.payment_status || 'PENDING'}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className="order-amount-bold">{formatVND(o.total_amount)}</span>
                      </td>
                      <td>
                        <div className="status-shipment-cell">
                          <span className={`status-badge ${statusInfo.color}`}>
                            {statusInfo.label}
                          </span>
                          {o.shipment_tracking_code && (
                            <div className="shipment-code-pill" title="Mã vận đơn">
                              <Truck size={12} className="text-gold" />
                              <span>{o.shipment_carrier}: <strong>{o.shipment_tracking_code}</strong></span>
                            </div>
                          )}
                        </div>
                      </td>
                      <td>
                        <div className="action-buttons-cell flex-center gap-1">
                          <button
                            type="button"
                            className="btn-action-status"
                            onClick={() => handleOpenStatusModal(o)}
                            data-testid={`manage-btn-${o.order_code}`}
                            title="Cập nhật trạng thái"
                          >
                            <Edit size={14} />
                            <span>Cập nhật</span>
                          </button>

                          {canDispatch && (
                            <button
                              type="button"
                              className="btn-action-dispatch"
                              onClick={() => handleOpenDispatchModal(o)}
                              data-testid={`dispatch-btn-${o.order_code}`}
                              title="Tạo vận đơn với GHN / GHTK"
                            >
                              <Truck size={14} />
                              <span>Điều vận</span>
                            </button>
                          )}

                          {o.shipment_tracking_code && (
                            <button
                              type="button"
                              className="btn-action-tracking"
                              onClick={() => handleOpenTrackingModal(o)}
                              data-testid={`tracking-btn-${o.order_code}`}
                              title="Xem hành trình vận chuyển"
                            >
                              <ExternalLink size={13} />
                              <span>Vận đơn</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Status Update Modal */}
      {activeOrder && (
        <div
          className="checkout-modal-backdrop"
          onClick={() => setActiveOrder(null)}
          data-testid="admin-status-modal-backdrop"
        >
          <div
            className="cancel-modal-container"
            onClick={(e) => e.stopPropagation()}
            data-testid="admin-status-modal"
          >
            <div className="cancel-modal-header">
              <div className="flex-center gap-2">
                <Edit size={20} className="text-gold" />
                <h3>Cập Nhật Đơn Hàng {activeOrder.order_code}</h3>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setActiveOrder(null)}
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleSaveStatus} className="cancel-modal-body">
              <div className="form-group">
                <label className="input-label">Trạng thái mới:</label>
                <select
                  className="form-input"
                  value={targetStatus}
                  onChange={(e) => setTargetStatus(e.target.value)}
                  disabled={updating}
                >
                  <option value="PENDING">PENDING — Chờ xử lý</option>
                  <option value="CONFIRMED">CONFIRMED — Đã xác nhận</option>
                  <option value="PROCESSING">PROCESSING — Đang đóng gói</option>
                  <option value="SHIPPING">SHIPPING — Xuất kho &amp; Vận chuyển (Trừ tồn kho vật lý)</option>
                  <option value="COMPLETED">COMPLETED — Giao hàng thành công</option>
                  <option value="CANCELLED">CANCELLED — Hủy đơn hàng (Hoàn trả tồn kho)</option>
                </select>
              </div>

              {targetStatus === 'CANCELLED' && (
                <div className="form-group">
                  <label className="input-label">Lý do hủy đơn *</label>
                  <textarea
                    className="form-input"
                    rows={2}
                    required
                    value={cancellationReason}
                    onChange={(e) => setCancellationReason(e.target.value)}
                    placeholder="Lý do hủy đơn từ phía cửa hàng hoặc khách hàng..."
                    disabled={updating}
                  />
                </div>
              )}

              <div className="form-group">
                <label className="input-label">Ghi chú nội bộ (Staff Notes):</label>
                <input
                  type="text"
                  className="form-input"
                  value={staffNotes}
                  onChange={(e) => setStaffNotes(e.target.value)}
                  placeholder="Ghi chú đóng gói, kiểm tra sách..."
                  disabled={updating}
                />
              </div>

              {updateError && (
                <div className="order-alert-banner alert-error">
                  <AlertTriangle size={16} />
                  <span>{updateError}</span>
                </div>
              )}

              <div className="cancel-modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setActiveOrder(null)}
                  disabled={updating}
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={updating}
                  data-testid="save-status-btn"
                >
                  {updating ? (
                    <>
                      <Loader2 size={16} className="spin" />
                      <span>Đang lưu...</span>
                    </>
                  ) : (
                    <span>Lưu Trạng Thái</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Carrier Dispatch Modal */}
      {dispatchOrderTarget && (
        <div
          className="checkout-modal-backdrop"
          onClick={() => setDispatchOrderTarget(null)}
          data-testid="dispatch-modal-backdrop"
        >
          <div
            className="cancel-modal-container dispatch-modal-container"
            onClick={(e) => e.stopPropagation()}
            data-testid="dispatch-order-modal"
          >
            <div className="cancel-modal-header">
              <div className="flex-center gap-2">
                <Truck size={20} className="text-gold" />
                <h3>Điều Vận &amp; Tạo Vận Đơn — {dispatchOrderTarget.order_code}</h3>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setDispatchOrderTarget(null)}
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleConfirmDispatch} className="cancel-modal-body">
              {/* Order quick summary */}
              <div className="dispatch-summary-box">
                <div className="summary-row">
                  <span>Khách hàng:</span>
                  <strong>{dispatchOrderTarget.recipient_name} ({dispatchOrderTarget.recipient_phone})</strong>
                </div>
                <div className="summary-row">
                  <span>Địa chỉ nhận:</span>
                  <span>{dispatchOrderTarget.shipping_street_address}, {dispatchOrderTarget.shipping_ward}, {dispatchOrderTarget.shipping_district}, {dispatchOrderTarget.shipping_province}</span>
                </div>
                <div className="summary-row">
                  <span>Thu hộ (COD):</span>
                  <strong>{dispatchOrderTarget.payment_method === 'COD' ? formatVND(dispatchOrderTarget.total_amount) : '0 ₫ (Đã thanh toán Online)'}</strong>
                </div>
              </div>

              {/* Carrier Selection */}
              <div className="form-group">
                <label className="input-label">Đối tác vận chuyển:</label>
                <select
                  className="form-input"
                  value={dispatchCarrier}
                  onChange={(e) => setDispatchCarrier(e.target.value)}
                  disabled={dispatching}
                >
                  <option value="GHN">Giao Hàng Nhanh (GHN Express)</option>
                  <option value="GHTK">Giao Hàng Tiết Kiệm (GHTK Fast)</option>
                  <option value="MOCK">MOCK Carrier (Giả lập môi trường Test)</option>
                </select>
              </div>

              {/* Package Dimensions */}
              <div className="form-grid-4">
                <div className="form-group">
                  <label className="input-label">Trọng lượng (g)</label>
                  <input
                    type="number"
                    min="50"
                    max="50000"
                    className="form-input"
                    value={dispatchWeight}
                    onChange={(e) => setDispatchWeight(Number(e.target.value))}
                    disabled={dispatching}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="input-label">Dài (cm)</label>
                  <input
                    type="number"
                    min="1"
                    max="200"
                    className="form-input"
                    value={dispatchLength}
                    onChange={(e) => setDispatchLength(Number(e.target.value))}
                    disabled={dispatching}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="input-label">Rộng (cm)</label>
                  <input
                    type="number"
                    min="1"
                    max="200"
                    className="form-input"
                    value={dispatchWidth}
                    onChange={(e) => setDispatchWidth(Number(e.target.value))}
                    disabled={dispatching}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="input-label">Cao (cm)</label>
                  <input
                    type="number"
                    min="1"
                    max="200"
                    className="form-input"
                    value={dispatchHeight}
                    onChange={(e) => setDispatchHeight(Number(e.target.value))}
                    disabled={dispatching}
                    required
                  />
                </div>
              </div>

              {/* Required Note */}
              <div className="form-group">
                <label className="input-label">Lưu ý giao hàng cho shipper:</label>
                <select
                  className="form-input"
                  value={dispatchNote}
                  onChange={(e) => setDispatchNote(e.target.value)}
                  disabled={dispatching}
                >
                  <option value="CHOXEMHANGKHONGTHU">Cho xem hàng không cho thử (CHOXEMHANGKHONGTHU)</option>
                  <option value="CHOTHUHANG">Cho thử hàng (CHOTHUHANG)</option>
                  <option value="KHONGCHOXEMHANG">Không cho xem hàng (KHONGCHOXEMHANG)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="input-label">Ghi chú điều vận:</label>
                <input
                  type="text"
                  className="form-input"
                  value={dispatchStaffNotes}
                  onChange={(e) => setDispatchStaffNotes(e.target.value)}
                  placeholder="Gói sách cẩn thận kèm bookmark..."
                  disabled={dispatching}
                />
              </div>

              {dispatchError && (
                <div className="order-alert-banner alert-error">
                  <AlertTriangle size={16} />
                  <span>{dispatchError}</span>
                </div>
              )}

              <div className="cancel-modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setDispatchOrderTarget(null)}
                  disabled={dispatching}
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={dispatching}
                  data-testid="confirm-dispatch-btn"
                >
                  {dispatching ? (
                    <>
                      <Loader2 size={16} className="spin" />
                      <span>Đang tạo vận đơn...</span>
                    </>
                  ) : (
                    <span>Tạo Vận Đơn &amp; Xuất Kho</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Tracking Details Modal */}
      {trackingOrderTarget && (
        <div
          className="checkout-modal-backdrop"
          onClick={() => setTrackingOrderTarget(null)}
          data-testid="tracking-modal-backdrop"
        >
          <div
            className="cancel-modal-container tracking-modal-container"
            onClick={(e) => e.stopPropagation()}
            data-testid="tracking-detail-modal"
          >
            <div className="cancel-modal-header">
              <div className="flex-center gap-2">
                <Truck size={20} className="text-gold" />
                <h3>Hành Trình Vận Đơn — {trackingOrderTarget.order_code}</h3>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setTrackingOrderTarget(null)}
              >
                &times;
              </button>
            </div>

            <div className="cancel-modal-body">
              {loadingTracking ? (
                <div className="orders-loading-state">
                  <Loader2 size={32} className="spin text-gold" />
                  <p>Đang đồng bộ hành trình từ đối tác vận chuyển...</p>
                </div>
              ) : trackingError ? (
                <div className="order-alert-banner alert-error">
                  <AlertTriangle size={16} />
                  <span>{trackingError}</span>
                </div>
              ) : trackingDetail ? (
                <div className="tracking-content">
                  {/* Summary Bar */}
                  <div className="tracking-summary-card">
                    <div className="tracking-metric">
                      <span className="metric-label">Nhà vận chuyển</span>
                      <strong className="metric-val">{trackingDetail.carrier}</strong>
                    </div>
                    <div className="tracking-metric">
                      <span className="metric-label">Mã vận đơn</span>
                      <strong className="metric-val text-gold">{trackingDetail.tracking_code || 'Chưa cấp'}</strong>
                    </div>
                    <div className="tracking-metric">
                      <span className="metric-label">Trạng thái</span>
                      <span className="shipment-status-chip">{trackingDetail.status_label}</span>
                    </div>
                    <div className="tracking-metric">
                      <span className="metric-label">Phí ship</span>
                      <strong className="metric-val">{formatVND(trackingDetail.shipping_fee)}</strong>
                    </div>
                  </div>

                  {/* Address & Estimated Date */}
                  <div className="tracking-submeta">
                    <div className="submeta-row">
                      <MapPin size={14} className="text-muted" />
                      <span>Giao đến: {trackingDetail.recipient_name} — {trackingDetail.shipping_address}</span>
                    </div>
                    {trackingDetail.estimated_delivery_date && (
                      <div className="submeta-row">
                        <Calendar size={14} className="text-muted" />
                        <span>Dự kiến giao: <strong>{new Date(trackingDetail.estimated_delivery_date).toLocaleDateString('vi-VN')}</strong></span>
                      </div>
                    )}
                  </div>

                  {/* Vertical Events Timeline */}
                  <div className="tracking-timeline-wrap">
                    <h4 className="timeline-title">Lịch Sử Chuyển Phát</h4>
                    {trackingDetail.events.length === 0 ? (
                      <p className="text-muted text-sm">Chưa có sự kiện vận chuyển nào được ghi nhận.</p>
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
                  onClick={() => setTrackingOrderTarget(null)}
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
