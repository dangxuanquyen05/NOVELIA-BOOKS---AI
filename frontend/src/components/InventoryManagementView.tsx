import React, { useEffect, useState, useCallback } from 'react';
import {
  Boxes,
  AlertTriangle,
  ArrowDownToLine,
  Sliders,
  History,
  Search,
  RefreshCw,
  CheckCircle2,
  XCircle,
  X,
  FileText,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  InventoryItem,
  InventoryTransaction,
  PaginatedInventory,
} from '../types/commerce';
import * as commerceApi from '../services/commerceApi';

export const InventoryManagementView: React.FC = () => {
  const { token, user } = useAuth();
  const [data, setData] = useState<PaginatedInventory | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const [lowStockOnly, setLowStockOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals state
  const [selectedBook, setSelectedBook] = useState<InventoryItem | null>(null);
  const [isInboundOpen, setIsInboundOpen] = useState<boolean>(false);
  const [isAdjustOpen, setIsAdjustOpen] = useState<boolean>(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);

  // Form states
  const [formQuantity, setFormQuantity] = useState<number>(10);
  const [formRefCode, setFormRefCode] = useState<string>('');
  const [formReason, setFormReason] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [modalFeedback, setModalFeedback] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // History state
  const [historyItems, setHistoryItems] = useState<InventoryTransaction[]>([]);
  const [historyLoading, setHistoryLoading] = useState<boolean>(false);

  const isStaffOrAdmin =
    user?.roles.some((r) => r === 'STAFF' || r === 'ADMIN') ?? false;

  const loadInventory = useCallback(async () => {
    if (!token || !isStaffOrAdmin) return;
    setLoading(true);
    setError(null);
    try {
      const res = await commerceApi.fetchInventory(
        token,
        page,
        lowStockOnly,
        searchQuery
      );
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lỗi tải danh mục kho');
    } finally {
      setLoading(false);
    }
  }, [token, isStaffOrAdmin, page, lowStockOnly, searchQuery]);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  const handleOpenInbound = (item: InventoryItem) => {
    setSelectedBook(item);
    setFormQuantity(20);
    setFormRefCode(`INB-${Date.now().toString().slice(-6)}`);
    setFormReason('Nhập hàng định kỳ từ nhà xuất bản');
    setModalFeedback(null);
    setIsInboundOpen(true);
  };

  const handleOpenAdjust = (item: InventoryItem) => {
    setSelectedBook(item);
    setFormQuantity(0);
    setFormRefCode(`ADJ-${Date.now().toString().slice(-6)}`);
    setFormReason('');
    setModalFeedback(null);
    setIsAdjustOpen(true);
  };

  const handleOpenHistory = async (item: InventoryItem) => {
    if (!token) return;
    setSelectedBook(item);
    setIsHistoryOpen(true);
    setHistoryLoading(true);
    try {
      const history = await commerceApi.fetchInventoryHistory(token, item.book_id);
      setHistoryItems(history);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lỗi tải lịch sử kho');
    } finally {
      setHistoryLoading(false);
    }
  };

  const submitInbound = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedBook) return;
    if (formQuantity <= 0) {
      setModalFeedback({
        type: 'error',
        message: 'Số lượng nhập phải lớn hơn 0.',
      });
      return;
    }
    setSubmitting(true);
    setModalFeedback(null);
    try {
      await commerceApi.inboundRestock(token, {
        book_id: selectedBook.book_id,
        quantity: formQuantity,
        reference_code: formRefCode,
        reason: formReason,
      });
      setModalFeedback({
        type: 'success',
        message: `Đã nhập thêm +${formQuantity} cuốn vào kho thành công!`,
      });
      loadInventory();
      setTimeout(() => setIsInboundOpen(false), 1200);
    } catch (err) {
      setModalFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : 'Lỗi thực hiện nhập kho',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const submitAdjustment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedBook) return;
    if (formQuantity === 0) {
      setModalFeedback({
        type: 'error',
        message: 'Số lượng điều chỉnh (delta) không được bằng 0.',
      });
      return;
    }
    if (!formReason.trim()) {
      setModalFeedback({
        type: 'error',
        message: 'Bắt buộc phải nhập lý do điều chỉnh kho (kiểm toán nội bộ).',
      });
      return;
    }
    setSubmitting(true);
    setModalFeedback(null);
    try {
      await commerceApi.adjustStock(token, {
        book_id: selectedBook.book_id,
        quantity_change: formQuantity,
        reference_code: formRefCode,
        reason: formReason.trim(),
      });
      setModalFeedback({
        type: 'success',
        message: `Đã điều chỉnh kho (${formQuantity > 0 ? '+' : ''}${formQuantity}) thành công!`,
      });
      loadInventory();
      setTimeout(() => setIsAdjustOpen(false), 1200);
    } catch (err) {
      setModalFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : 'Lỗi thực hiện điều chỉnh kho',
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (!isStaffOrAdmin) {
    return (
      <div className="inventory-access-denied">
        <AlertTriangle size={48} color="var(--status-warning)" />
        <h2>Khu vực Quản trị &amp; Thủ kho</h2>
        <p>
          Bạn không có quyền truy cập vào bảng kiểm soát tồn kho. Tính năng này chỉ
          dành cho tài khoản có vai trò <strong>STAFF</strong> hoặc <strong>ADMIN</strong>.
        </p>
      </div>
    );
  }

  return (
    <div className="inventory-container" data-testid="inventory-view">
      {/* Header bar */}
      <div className="inventory-header">
        <div>
          <h2 className="inventory-title">
            <Boxes size={24} color="var(--accent-gold)" /> Quản trị Tồn kho &amp; Kiểm toán
          </h2>
          <p className="inventory-subtitle">
            Hệ thống quản lý định lượng vật lý, số lượng đặt trước, và lịch sử giao dịch ACID.
          </p>
        </div>

        <div className="inventory-actions-bar">
          <button
            type="button"
            className="action-btn-secondary"
            onClick={loadInventory}
            disabled={loading}
          >
            <RefreshCw size={15} className={loading ? 'spin-icon' : ''} />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="inventory-filter-bar">
        <div className="inventory-search-box">
          <Search size={16} />
          <input
            type="text"
            placeholder="Tìm theo tiêu đề sách, ISBN, SKU..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <button
          type="button"
          className={`filter-low-stock-btn ${lowStockOnly ? 'active' : ''}`}
          onClick={() => {
            setLowStockOnly(!lowStockOnly);
            setPage(1);
          }}
        >
          <AlertTriangle size={15} />
          <span>Chỉ xem sách tồn thấp (≤ ngưỡng báo động)</span>
        </button>
      </div>

      {/* Main Table */}
      {loading && !data ? (
        <div className="inventory-loading">
          <div className="spinner-large" />
          <p>Đang tải dữ liệu tồn kho từ MySQL Server...</p>
        </div>
      ) : error ? (
        <div className="inventory-error">
          <XCircle size={28} color="var(--status-error)" />
          <p>{error}</p>
          <button type="button" onClick={loadInventory} className="action-btn-primary">
            Thử lại
          </button>
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="inventory-empty">
          <Boxes size={48} color="var(--text-muted)" />
          <p>Không tìm thấy bản ghi tồn kho nào phù hợp với bộ lọc.</p>
        </div>
      ) : (
        <div className="inventory-table-wrapper">
          <table className="inventory-table">
            <thead>
              <tr>
                <th>Tác phẩm / SKU</th>
                <th>Tồn thực tế</th>
                <th>Đang giữ hàng</th>
                <th>Khả dụng bán</th>
                <th>Ngưỡng cảnh báo</th>
                <th>Trạng thái</th>
                <th className="text-right">Thao tác nghiệp vụ</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => {
                const isLowStock = item.available_stock <= item.low_stock_threshold;
                const isOutOfStock = item.available_stock <= 0;

                return (
                  <tr
                    key={item.book_id}
                    className={isOutOfStock ? 'row-out-of-stock' : isLowStock ? 'row-low-stock' : ''}
                  >
                    <td>
                      <div className="inv-book-info">
                        <strong>{item.book_title}</strong>
                        <span className="inv-sku">
                          SKU: {item.book_sku} | ISBN: {item.book_isbn}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="stock-num stock-physical">{item.physical_stock}</span>
                    </td>
                    <td>
                      <span className="stock-num stock-reserved">{item.reserved_stock}</span>
                    </td>
                    <td>
                      <span
                        className={`stock-num stock-avail ${
                          isOutOfStock ? 'avail-zero' : isLowStock ? 'avail-low' : 'avail-ok'
                        }`}
                      >
                        {item.available_stock}
                      </span>
                    </td>
                    <td>
                      <span className="stock-threshold">{item.low_stock_threshold} cuốn</span>
                    </td>
                    <td>
                      {isOutOfStock ? (
                        <span className="inv-badge badge-out">
                          <XCircle size={12} /> Hết hàng
                        </span>
                      ) : isLowStock ? (
                        <span className="inv-badge badge-warn">
                          <AlertTriangle size={12} /> Tồn thấp
                        </span>
                      ) : (
                        <span className="inv-badge badge-ok">
                          <CheckCircle2 size={12} /> Ổn định
                        </span>
                      )}
                    </td>
                    <td className="text-right">
                      <div className="inv-actions">
                        <button
                          type="button"
                          className="btn-inv-action btn-inbound"
                          title="Nhập hàng bổ sung"
                          onClick={() => handleOpenInbound(item)}
                        >
                          <ArrowDownToLine size={14} />
                          <span>Nhập kho</span>
                        </button>
                        <button
                          type="button"
                          className="btn-inv-action btn-adjust"
                          title="Điều chỉnh số lượng kiểm toán"
                          onClick={() => handleOpenAdjust(item)}
                        >
                          <Sliders size={14} />
                          <span>Điều chỉnh</span>
                        </button>
                        <button
                          type="button"
                          className="btn-inv-action btn-history"
                          title="Xem lịch sử giao dịch kho"
                          onClick={() => handleOpenHistory(item)}
                        >
                          <History size={14} />
                          <span>Lịch sử</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="inventory-pagination">
            <span className="pagination-info">
              Hiển thị {data.items.length} trên tổng số {data.total} tác phẩm (Trang {data.page}/{data.total_pages})
            </span>
            <div className="pagination-buttons">
              <button
                type="button"
                disabled={data.page <= 1}
                onClick={() => setPage(page - 1)}
                className="action-btn-secondary"
              >
                Trang trước
              </button>
              <button
                type="button"
                disabled={data.page >= data.total_pages}
                onClick={() => setPage(page + 1)}
                className="action-btn-secondary"
              >
                Trang sau
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inbound Restock Modal */}
      {isInboundOpen && selectedBook && (
        <div className="modal-backdrop" onClick={() => setIsInboundOpen(false)}>
          <div className="modal-container inv-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                <ArrowDownToLine size={18} color="var(--accent-gold)" /> Nhập kho bổ sung
              </h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setIsInboundOpen(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={submitInbound} className="inv-form">
              <div className="inv-form-target">
                <strong>{selectedBook.book_title}</strong>
                <span>
                  Hiện có: {selectedBook.physical_stock} cuốn (Khả dụng: {selectedBook.available_stock})
                </span>
              </div>

              {modalFeedback && (
                <div className={`form-feedback ${modalFeedback.type}`}>
                  {modalFeedback.type === 'success' ? (
                    <CheckCircle2 size={16} />
                  ) : (
                    <XCircle size={16} />
                  )}
                  <span>{modalFeedback.message}</span>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="inbound-qty">Số lượng nhập thêm (+):</label>
                <input
                  id="inbound-qty"
                  type="number"
                  min="1"
                  required
                  value={formQuantity}
                  onChange={(e) => setFormQuantity(parseInt(e.target.value) || 0)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="inbound-ref">Mã tham chiếu / Số phiếu:</label>
                <input
                  id="inbound-ref"
                  type="text"
                  required
                  value={formRefCode}
                  onChange={(e) => setFormRefCode(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="inbound-reason">Ghi chú / Nguồn nhập:</label>
                <input
                  id="inbound-reason"
                  type="text"
                  value={formReason}
                  onChange={(e) => setFormReason(e.target.value)}
                  placeholder="Ví dụ: Lô hàng tái bản NXB Trẻ"
                />
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="action-btn-secondary"
                  onClick={() => setIsInboundOpen(false)}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="action-btn-primary"
                >
                  {submitting ? 'Đang cập nhật kho...' : 'Xác nhận nhập kho'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Adjustment Modal */}
      {isAdjustOpen && selectedBook && (
        <div className="modal-backdrop" onClick={() => setIsAdjustOpen(false)}>
          <div className="modal-container inv-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                <Sliders size={18} color="var(--accent-gold)" /> Điều chỉnh tồn kho có lý do
              </h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setIsAdjustOpen(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={submitAdjustment} className="inv-form">
              <div className="inv-form-target">
                <strong>{selectedBook.book_title}</strong>
                <span>
                  Tồn vật lý: {selectedBook.physical_stock} | Đang giữ: {selectedBook.reserved_stock}
                </span>
              </div>

              {modalFeedback && (
                <div className={`form-feedback ${modalFeedback.type}`}>
                  {modalFeedback.type === 'success' ? (
                    <CheckCircle2 size={16} />
                  ) : (
                    <XCircle size={16} />
                  )}
                  <span>{modalFeedback.message}</span>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="adj-qty">
                  Số lượng thay đổi (Delta, nhập số âm để trừ, dương để tăng):
                </label>
                <input
                  id="adj-qty"
                  type="number"
                  required
                  value={formQuantity}
                  onChange={(e) => setFormQuantity(parseInt(e.target.value) || 0)}
                />
                <span className="form-help">
                  Tồn vật lý mới sẽ là:{' '}
                  <strong>{selectedBook.physical_stock + formQuantity}</strong> cuốn.
                </span>
              </div>

              <div className="form-group">
                <label htmlFor="adj-ref">Mã biên bản / Mã tham chiếu:</label>
                <input
                  id="adj-ref"
                  type="text"
                  required
                  value={formRefCode}
                  onChange={(e) => setFormRefCode(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="adj-reason">
                  Lý do điều chỉnh (Bắt buộc theo quy chuẩn kiểm toán):
                </label>
                <textarea
                  id="adj-reason"
                  required
                  rows={3}
                  value={formReason}
                  onChange={(e) => setFormReason(e.target.value)}
                  placeholder="Ví dụ: Kiểm kê định kỳ phát hiện 2 cuốn ướt hỏng do vận chuyển..."
                />
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="action-btn-secondary"
                  onClick={() => setIsAdjustOpen(false)}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="action-btn-primary"
                >
                  {submitting ? 'Đang điều chỉnh...' : 'Xác nhận điều chỉnh'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* History Modal */}
      {isHistoryOpen && selectedBook && (
        <div className="modal-backdrop" onClick={() => setIsHistoryOpen(false)}>
          <div className="modal-container inv-history-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                <History size={18} color="var(--accent-gold)" /> Lịch sử biến động tồn kho: {selectedBook.book_title}
              </h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setIsHistoryOpen(false)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="inv-history-body">
              {historyLoading ? (
                <div className="inventory-loading">
                  <div className="spinner-large" />
                  <p>Đang tải lịch sử giao dịch từ MySQL...</p>
                </div>
              ) : historyItems.length === 0 ? (
                <div className="inventory-empty">
                  <FileText size={36} color="var(--text-muted)" />
                  <p>Chưa có giao dịch biến động nào được ghi nhận cho sách này.</p>
                </div>
              ) : (
                <div className="history-table-wrapper">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Thời gian</th>
                        <th>Loại giao dịch</th>
                        <th>Biến động</th>
                        <th>Tồn trước → sau</th>
                        <th>Mã tham chiếu</th>
                        <th>Lý do &amp; Ghi chú</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historyItems.map((tx) => (
                        <tr key={tx.id}>
                          <td>{new Date(tx.created_at).toLocaleString('vi-VN')}</td>
                          <td>
                            <span className={`tx-type-pill tx-${tx.transaction_type.toLowerCase()}`}>
                              {tx.transaction_type}
                            </span>
                          </td>
                          <td className={tx.quantity_change >= 0 ? 'tx-plus' : 'tx-minus'}>
                            {tx.quantity_change > 0 ? `+${tx.quantity_change}` : tx.quantity_change}
                          </td>
                          <td>
                            {tx.balance_after - tx.quantity_change} → <strong>{tx.balance_after}</strong>
                          </td>
                          <td>
                            <code>{tx.reference_code || '—'}</code>
                          </td>
                          <td>{tx.reason || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="action-btn-secondary"
                onClick={() => setIsHistoryOpen(false)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
