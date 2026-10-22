import React, { useEffect, useState, useCallback } from 'react';
import { MapPin, Plus, Trash2, CheckCircle2, AlertCircle, Loader2, Home, Navigation } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/authApi';
import { Address, AddressCreatePayload } from '../types/auth';
import { SmartAddressPicker } from './SmartAddressPicker';

export const AddressBookView: React.FC = () => {
  const { token, user } = useAuth();
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form modal state
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchAddresses = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      const data = await authApi.listAddresses(token);
      setAddresses(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Không thể tải danh sách địa chỉ');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchAddresses();
  }, [fetchAddresses]);

  const handleSaveSmartAddress = async (payload: AddressCreatePayload) => {
    if (!token) return;
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await authApi.createAddress(token, payload);
      setSuccess('Thêm địa chỉ giao hàng thành công!');
      setShowForm(false);
      await fetchAddresses();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Không thể tạo địa chỉ');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (addressId: number) => {
    if (!token) return;
    if (!window.confirm('Bạn có chắc chắn muốn xóa địa chỉ nhận hàng này?')) return;

    try {
      await authApi.deleteAddress(token, addressId);
      setSuccess('Đã xóa địa chỉ thành công');
      await fetchAddresses();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Không thể xóa địa chỉ');
    }
  };

  const handleSetDefault = async (address: Address) => {
    if (!token || address.is_default) return;
    try {
      await authApi.updateAddress(token, address.id, { is_default: true });
      setSuccess('Đã đặt làm địa chỉ giao hàng mặc định');
      await fetchAddresses();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Không thể cập nhật địa chỉ mặc định');
    }
  };

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="address-container">
      <div className="address-header-row">
        <div>
          <h2 className="section-title">Sổ Địa Chỉ Nhận Hàng</h2>
          <p className="section-subtitle">Quản lý các địa chỉ giao nhận sách phục vụ đặt hàng thuận tiện</p>
        </div>
        <button
          type="button"
          onClick={() => { setShowForm(!showForm); clearMessages(); }}
          className="refresh-btn add-address-btn"
        >
          <Plus size={18} />
          <span>{showForm ? 'Đóng biểu mẫu' : 'Thêm địa chỉ mới'}</span>
        </button>
      </div>

      {success && (
        <div className="alert-box alert-success" role="alert">
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="alert-box alert-error" role="alert">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Smart Address Creation Form */}
      {showForm && (
        <div className="mb-8">
          <SmartAddressPicker
            token={token || ''}
            initialRecipientName={user?.full_name || ''}
            initialPhone={user?.phone || ''}
            onSaveAddress={handleSaveSmartAddress}
            onCancel={() => setShowForm(false)}
            submitting={submitting}
            breadcrumb="Tài khoản / Sổ địa chỉ"
            submitButtonText="Lưu địa chỉ vào sổ tay"
          />
        </div>
      )}

      {/* Address List */}
      {loading ? (
        <div className="loading-state-box">
          <Loader2 size={32} className="spin-icon text-gold" />
          <p>Đang tải danh sách địa chỉ...</p>
        </div>
      ) : addresses.length === 0 ? (
        <div className="empty-state-box">
          <MapPin size={48} className="text-muted" />
          <h3>Chưa có địa chỉ giao hàng nào</h3>
          <p>Hãy thêm địa chỉ để sẵn sàng đặt sách nhanh chóng và nhận tính toán cước phí chính xác.</p>
        </div>
      ) : (
        <div className="address-cards-grid">
          {addresses.map((addr) => (
            <div key={addr.id} className={`address-card ${addr.is_default ? 'address-card-default' : ''}`}>
              <div className="address-card-header">
                <div className="address-card-title">
                  <Home size={18} className="text-gold" />
                  <h4>{addr.recipient_name}</h4>
                  {addr.is_default && (
                    <span className="badge-default">Mặc định</span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(addr.id)}
                  className="delete-icon-btn"
                  title="Xóa địa chỉ"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              <div className="address-card-body">
                <p className="addr-phone"><strong>Điện thoại:</strong> {addr.phone}</p>
                <p className="addr-street font-medium text-stone-900">{addr.street_address}</p>
                <p className="addr-area text-stone-600">{addr.ward_name}, {addr.district_name}, {addr.province_name}</p>
                {addr.latitude && addr.longitude && (
                  <div className="flex items-center gap-2 mt-2 pt-2 border-t border-stone-100 text-[11px] text-amber-800">
                    <Navigation size={12} className="rotate-45 text-amber-600" />
                    <span>Tọa độ GPS: {addr.latitude.toFixed(4)}, {addr.longitude.toFixed(4)}</span>
                    {addr.source_provider && (
                      <span className="bg-amber-100/70 text-amber-900 px-1.5 py-0.2 rounded font-semibold text-[10px]">
                        {addr.source_provider}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {!addr.is_default && (
                <div className="address-card-footer">
                  <button
                    type="button"
                    onClick={() => handleSetDefault(addr)}
                    className="set-default-btn"
                  >
                    Đặt làm mặc định
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
