import React, { useState, useEffect, useCallback } from 'react';
import {
  X,
  MapPin,
  CreditCard,
  Tag,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Truck,
  ShieldCheck,
  ArrowRight,
  ExternalLink,
  Receipt,
  FileCheck,
  Navigation,
  Map as MapIcon,
  Info,
  Check,
  Edit3,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCommerce } from '../context/CommerceContext';
import { authApi } from '../services/authApi';
import { formatVND } from '../services/catalogApi';
import * as commerceApi from '../services/commerceApi';
import { Address, ReverseGeocodeResult } from '../types/auth';
import { CheckoutPayload, CouponValidationResult, Order } from '../types/commerce';
import { InteractiveMapModal } from './InteractiveMapModal';

interface CheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOrderSuccess: (order: Order) => void;
}

export const CheckoutModal: React.FC<CheckoutModalProps> = ({
  isOpen,
  onClose,
  onOrderSuccess,
}) => {
  const { token, user } = useAuth();
  const { cart, refreshCart } = useCommerce();

  // Saved addresses
  const [savedAddresses, setSavedAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<number | 'NEW'>('NEW');
  const [loadingAddresses, setLoadingAddresses] = useState<boolean>(false);

  // Address form fields
  const [recipientName, setRecipientName] = useState<string>('');
  const [recipientPhone, setRecipientPhone] = useState<string>('');
  const [shippingProvince, setShippingProvince] = useState<string>('Hà Nội');
  const [shippingDistrict, setShippingDistrict] = useState<string>('Cầu Giấy');
  const [shippingWard, setShippingWard] = useState<string>('Dịch Vọng Hậu');
  const [shippingStreetAddress, setShippingStreetAddress] = useState<string>('');
  const [shippingFormattedAddress, setShippingFormattedAddress] = useState<string>('');
  const [shippingLatitude, setShippingLatitude] = useState<number | null>(null);
  const [shippingLongitude, setShippingLongitude] = useState<number | null>(null);
  const [detectedAddress, setDetectedAddress] = useState<ReverseGeocodeResult | null>(null);
  const [isLocating, setIsLocating] = useState<boolean>(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [showMapModal, setShowMapModal] = useState<boolean>(false);
  const [showManualFields, setShowManualFields] = useState<boolean>(false);
  const [customerNotes, setCustomerNotes] = useState<string>('');

  // Payment method
  const [paymentMethod, setPaymentMethod] = useState<string>('COD');

  // Coupon state
  const [couponCode, setCouponCode] = useState<string>('');
  const [couponLoading, setCouponLoading] = useState<boolean>(false);
  const [appliedCoupon, setAppliedCoupon] = useState<CouponValidationResult | null>(null);
  const [couponError, setCouponError] = useState<string | null>(null);

  // Submission state
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [completedOrder, setCompletedOrder] = useState<Order | null>(null);

  const applyGeocodedResult = useCallback((res: ReverseGeocodeResult) => {
    setDetectedAddress(res);
    setShippingProvince(res.province_name);
    setShippingDistrict(res.district_name);
    setShippingWard(res.ward_name);
    setShippingStreetAddress(res.street_address);
    setShippingFormattedAddress(res.formatted_address);
    setShippingLatitude(res.latitude);
    setShippingLongitude(res.longitude);
    setLocationError(null);
  }, []);

  const handleRequestCurrentLocation = () => {
    if (!token) return;
    setLocationError(null);
    if (!navigator.geolocation) {
      setLocationError('Trình duyệt không hỗ trợ Geolocation. Vui lòng bấm "Chọn trên bản đồ".');
      return;
    }
    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const res = await authApi.reverseGeocode(token, pos.coords.latitude, pos.coords.longitude);
          applyGeocodedResult(res.address);
        } catch (err: unknown) {
          setLocationError(err instanceof Error ? err.message : 'Không thể lấy thông tin địa chỉ từ tọa độ.');
        } finally {
          setIsLocating(false);
        }
      },
      (err) => {
        setIsLocating(false);
        if (err.code === err.PERMISSION_DENIED) {
          setLocationError('Bạn đã từ chối quyền truy cập vị trí trên trình duyệt. Vui lòng chọn vị trí trên bản đồ.');
        } else {
          setLocationError(`Lỗi định vị: ${err.message}. Vui lòng thử lại hoặc chọn trên bản đồ.`);
        }
      },
      { timeout: 10000, enableHighAccuracy: true },
    );
  };

  // Initialize and prefill address
  useEffect(() => {
    if (!isOpen || !token) return;

    // Reset completion on new open
    setCompletedOrder(null);
    setCheckoutError(null);

    // Prefill name & phone from user profile if empty
    if (user) {
      setRecipientName((prev) => prev || user.full_name || '');
      setRecipientPhone((prev) => prev || user.phone || '');
    }

    // Load saved address list
    setLoadingAddresses(true);
    authApi
      .listAddresses(token)
      .then((addresses) => {
        setSavedAddresses(addresses);
        if (addresses.length > 0) {
          const defaultAddr = addresses.find((a) => a.is_default) || addresses[0];
          setSelectedAddressId(defaultAddr.id);
          applySavedAddress(defaultAddr);
        } else {
          setSelectedAddressId('NEW');
        }
      })
      .catch(() => {
        setSelectedAddressId('NEW');
      })
      .finally(() => {
        setLoadingAddresses(false);
      });
  }, [isOpen, token, user]);

  const applySavedAddress = (addr: Address) => {
    setRecipientName(addr.recipient_name);
    setRecipientPhone(addr.phone);
    setShippingProvince(addr.province_name);
    setShippingDistrict(addr.district_name);
    setShippingWard(addr.ward_name);
    setShippingStreetAddress(addr.street_address);
    setShippingFormattedAddress(addr.formatted_address || addr.street_address);
    setShippingLatitude(addr.latitude || null);
    setShippingLongitude(addr.longitude || null);
    if (addr.latitude && addr.longitude) {
      setDetectedAddress({
        province_name: addr.province_name,
        province_code: addr.province_code,
        district_name: addr.district_name,
        district_code: addr.district_code,
        ward_name: addr.ward_name,
        ward_code: addr.ward_code,
        street_address: addr.street_address,
        formatted_address: addr.formatted_address || addr.street_address,
        latitude: addr.latitude,
        longitude: addr.longitude,
        place_id: addr.place_id,
        confidence: addr.confidence || 0.95,
        level: 'house_number',
        source_provider: addr.source_provider || 'SAVED',
        is_mock: false,
      });
    } else {
      setDetectedAddress(null);
    }
  };

  const handleSelectAddress = (idStr: string) => {
    if (idStr === 'NEW') {
      setSelectedAddressId('NEW');
      setShippingStreetAddress('');
      setShippingFormattedAddress('');
      setShippingLatitude(null);
      setShippingLongitude(null);
      setDetectedAddress(null);
    } else {
      const id = Number(idStr);
      setSelectedAddressId(id);
      const found = savedAddresses.find((a) => a.id === id);
      if (found) applySavedAddress(found);
    }
  };

  // Cart subtotal
  const rawSubtotal = cart ? Number(cart.subtotal_amount) : 0;
  // Shipping calculation mirrors backend logic: free >= 500k, otherwise 30k
  const shippingFee = rawSubtotal >= 500000 ? 0 : 30000;
  const discountAmount = appliedCoupon ? Number(appliedCoupon.discount_amount) : 0;
  const estimatedTotal = Math.max(0, rawSubtotal + shippingFee - discountAmount);

  // Validate coupon handler
  const handleApplyCoupon = async () => {
    if (!couponCode.trim()) return;
    setCouponLoading(true);
    setCouponError(null);
    try {
      const result = await commerceApi.validateCoupon(
        couponCode.trim(),
        rawSubtotal,
        token || undefined
      );
      if (result.is_valid) {
        setAppliedCoupon(result);
        setCouponError(null);
      } else {
        setAppliedCoupon(null);
        setCouponError(result.message || 'Mã giảm giá không hợp lệ.');
      }
    } catch (err: unknown) {
      setAppliedCoupon(null);
      setCouponError(err instanceof Error ? err.message : 'Lỗi kiểm tra mã giảm giá');
    } finally {
      setCouponLoading(false);
    }
  };

  const handleRemoveCoupon = () => {
    setAppliedCoupon(null);
    setCouponCode('');
    setCouponError(null);
  };

  // Submit checkout
  const handleSubmitOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setCheckoutError('Vui lòng đăng nhập để tiến hành đặt hàng.');
      return;
    }

    if (!recipientName.trim() || !recipientPhone.trim() || !shippingStreetAddress.trim()) {
      setCheckoutError('Vui lòng điền đầy đủ họ tên, số điện thoại và địa chỉ giao hàng.');
      return;
    }

    setSubmitting(true);
    setCheckoutError(null);

    // Client-side idempotency key to prevent double submits on rapid clicks
    const idempotencyKey = `NVL-IDEM-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;

    const payload: CheckoutPayload = {
      recipient_name: recipientName.trim(),
      recipient_phone: recipientPhone.trim(),
      shipping_province: shippingProvince.trim(),
      shipping_district: shippingDistrict.trim(),
      shipping_ward: shippingWard.trim(),
      shipping_street_address: shippingStreetAddress.trim(),
      shipping_formatted_address: shippingFormattedAddress.trim() || undefined,
      shipping_latitude: shippingLatitude || undefined,
      shipping_longitude: shippingLongitude || undefined,
      customer_notes: customerNotes.trim() || undefined,
      coupon_code: appliedCoupon ? appliedCoupon.code : undefined,
      payment_method: paymentMethod,
      idempotency_key: idempotencyKey,
    };

    try {
      const createdOrder = await commerceApi.checkoutOrder(token, payload);
      setCompletedOrder(createdOrder);
      await refreshCart();
      onOrderSuccess(createdOrder);
    } catch (err: unknown) {
      setCheckoutError(err instanceof Error ? err.message : 'Đặt hàng không thành công.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="checkout-modal-backdrop"
      onClick={onClose}
      data-testid="checkout-modal-backdrop"
    >
      <div
        className="checkout-modal-container"
        onClick={(e) => e.stopPropagation()}
        data-testid="checkout-modal"
      >
        {/* Header */}
        <div className="checkout-modal-header">
          <div className="checkout-header-title">
            <Receipt className="text-gold" size={22} />
            <h2>Hoàn Tất Đặt Hàng</h2>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Đóng thanh toán"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div className="checkout-modal-body">
          {completedOrder ? (
            /* Order Success View */
            <div className="checkout-success-view" data-testid="checkout-success-box">
              <div className="success-icon-wrap">
                <CheckCircle2 size={56} className="text-success" />
              </div>
              <h3>Đặt Hàng Thành Công!</h3>
              <p className="order-code-display">
                Mã đơn hàng: <strong>{completedOrder.order_code}</strong>
              </p>
              <p className="order-status-notice">
                Trạng thái: <span className="status-badge status-confirmed">{completedOrder.status}</span>
              </p>
              <div className="order-summary-card">
                <div className="summary-line">
                  <span>Người nhận:</span>
                  <strong>{completedOrder.recipient_name} ({completedOrder.recipient_phone})</strong>
                </div>
                <div className="summary-line">
                  <span>Địa chỉ giao:</span>
                  <span>{completedOrder.shipping_street_address}, {completedOrder.shipping_ward}, {completedOrder.shipping_district}, {completedOrder.shipping_province}</span>
                </div>
                <div className="summary-line">
                  <span>Phương thức:</span>
                  <strong>{completedOrder.payment_method || 'COD'}</strong>
                </div>
                <div className="summary-line total-line">
                  <span>Tổng thanh toán:</span>
                  <span className="total-gold">{formatVND(completedOrder.total_amount)}</span>
                </div>
              </div>

              {completedOrder.payment_url && (
                <div className="payment-gateway-redirect-box">
                  <p>Cổng thanh toán điện tử đã sẵn sàng. Vui lòng nhấn bên dưới để hoàn tất giao dịch:</p>
                  <a
                    href={completedOrder.payment_url}
                    target="_blank"
                    rel="noreferrer"
                    className="gateway-btn"
                  >
                    <span>Mở Cổng Thanh Toán Sandbox</span>
                    <ExternalLink size={16} />
                  </a>
                </div>
              )}

              <div className="success-action-buttons">
                <button
                  type="button"
                  className="btn-primary"
                  onClick={onClose}
                >
                  Tiếp tục khám phá sách
                </button>
              </div>
            </div>
          ) : (
            /* Standard Checkout Form */
            <form onSubmit={handleSubmitOrder} className="checkout-form-grid">
              {/* Left Column: Delivery & Payment */}
              <div className="checkout-main-col">
                {/* 1. Delivery Address Section */}
                <div className="checkout-section-card">
                  <div className="section-card-title flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MapPin size={18} className="text-gold" />
                      <h3>1. Thông tin giao hàng</h3>
                    </div>
                  </div>

                  {savedAddresses.length > 0 && (
                    <div className="saved-address-selector mb-4">
                      <label className="input-label">Chọn địa chỉ đã lưu:</label>
                      <select
                        className="form-input"
                        value={String(selectedAddressId)}
                        onChange={(e) => handleSelectAddress(e.target.value)}
                        disabled={submitting || loadingAddresses}
                      >
                        {savedAddresses.map((addr) => (
                          <option key={addr.id} value={String(addr.id)}>
                            {addr.recipient_name} — {addr.street_address}, {addr.district_name} {addr.is_default ? '(Mặc định)' : ''}
                          </option>
                        ))}
                        <option value="NEW">+ Nhập địa chỉ mới bằng GPS / Bản đồ</option>
                      </select>
                    </div>
                  )}

                  {/* Smart Address 2-Option Selector */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                    <button
                      type="button"
                      onClick={handleRequestCurrentLocation}
                      disabled={isLocating || submitting}
                      className={`flex items-center justify-between p-3.5 rounded-xl border text-left transition-all ${
                        isLocating
                          ? 'border-amber-400 bg-amber-50/80 shadow-sm'
                          : 'border-amber-200/90 bg-amber-50/40 hover:bg-amber-50/90 hover:border-amber-300'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center shrink-0 text-amber-700">
                          {isLocating ? <Loader2 size={18} className="animate-spin text-amber-700" /> : <Navigation size={18} className="rotate-45" />}
                        </div>
                        <div>
                          <h4 className="font-bold text-stone-900 text-xs sm:text-sm">Sử dụng vị trí hiện tại</h4>
                          <p className="text-[11px] text-stone-500 line-clamp-1">
                            {isLocating ? 'Đang truy vấn GPS...' : 'Tự động điền địa chỉ qua GPS'}
                          </p>
                        </div>
                      </div>
                      <ArrowRight size={16} className="text-stone-400 shrink-0 ml-1" />
                    </button>

                    <button
                      type="button"
                      onClick={() => setShowMapModal(true)}
                      disabled={submitting}
                      className="flex items-center justify-between p-3.5 rounded-xl border border-stone-200 bg-stone-50/60 hover:bg-stone-100/80 hover:border-stone-300 text-left transition-all"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-stone-200 flex items-center justify-center shrink-0 text-stone-700">
                          <MapIcon size={18} />
                        </div>
                        <div>
                          <h4 className="font-bold text-stone-900 text-xs sm:text-sm">Chọn trên bản đồ</h4>
                          <p className="text-[11px] text-stone-500 line-clamp-1">Đặt ghim vị trí nhận hàng</p>
                        </div>
                      </div>
                      <ArrowRight size={16} className="text-stone-400 shrink-0 ml-1" />
                    </button>
                  </div>

                  {/* Location Error Notice */}
                  {locationError && (
                    <div className="p-3 mb-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-2.5 text-xs">
                      <AlertCircle size={16} className="text-amber-700 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold">Lưu ý định vị: </span>
                        <span>{locationError}</span>
                      </div>
                    </div>
                  )}

                  {/* Recognized Address Card */}
                  {detectedAddress && (
                    <div className="p-4 mb-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px]">
                            <Check size={11} strokeWidth={3} />
                          </div>
                          <span className="text-xs font-bold text-emerald-900">Địa chỉ được hệ thống nhận diện</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setShowManualFields(!showManualFields)}
                          className="text-[11px] text-emerald-800 hover:text-emerald-950 font-semibold flex items-center gap-1 hover:underline"
                        >
                          <Edit3 size={11} />
                          <span>{showManualFields ? 'Thu gọn điều chỉnh' : 'Điều chỉnh chi tiết'}</span>
                        </button>
                      </div>

                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <p className="text-xs sm:text-sm font-medium text-stone-900">
                            {detectedAddress.formatted_address}
                          </p>
                          <div className="flex flex-wrap items-center gap-2 pt-0.5">
                            <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                              Tự động điền từ vị trí của bạn
                            </span>
                            <span className="text-[11px] text-stone-500 flex items-center gap-1">
                              <Info size={11} />
                              Độ chính xác: {Math.round(detectedAddress.confidence * 100)}%
                            </span>
                          </div>
                        </div>

                        {detectedAddress.latitude && detectedAddress.longitude && (
                          <div className="relative w-20 h-16 rounded-lg overflow-hidden border border-emerald-200 bg-stone-100 shrink-0 shadow-inner flex items-center justify-center">
                            <div className="p-1 bg-red-600 text-white rounded-full shadow">
                              <MapPin size={12} />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="form-row-2">
                    <div className="form-group">
                      <label className="input-label">Họ và tên người nhận *</label>
                      <input
                        type="text"
                        className="form-input"
                        required
                        value={recipientName}
                        onChange={(e) => setRecipientName(e.target.value)}
                        placeholder="Nguyễn Văn A"
                        disabled={submitting}
                      />
                    </div>
                    <div className="form-group">
                      <label className="input-label">Số điện thoại *</label>
                      <input
                        type="tel"
                        className="form-input"
                        required
                        value={recipientPhone}
                        onChange={(e) => setRecipientPhone(e.target.value)}
                        placeholder="0912 345 678"
                        disabled={submitting}
                      />
                    </div>
                  </div>

                  {/* Manual Administrative Fields (Visible when adjusting or when no GPS detected yet) */}
                  {(showManualFields || !detectedAddress) && (
                    <div className="space-y-3 pt-1 border-t border-stone-100 mt-2">
                      <div className="form-row-3">
                        <div className="form-group">
                          <label className="input-label">Tỉnh / Thành phố *</label>
                          <input
                            type="text"
                            className="form-input"
                            required
                            value={shippingProvince}
                            onChange={(e) => setShippingProvince(e.target.value)}
                            disabled={submitting}
                          />
                        </div>
                        <div className="form-group">
                          <label className="input-label">Quận / Huyện *</label>
                          <input
                            type="text"
                            className="form-input"
                            required
                            value={shippingDistrict}
                            onChange={(e) => setShippingDistrict(e.target.value)}
                            disabled={submitting}
                          />
                        </div>
                        <div className="form-group">
                          <label className="input-label">Phường / Xã *</label>
                          <input
                            type="text"
                            className="form-input"
                            required
                            value={shippingWard}
                            onChange={(e) => setShippingWard(e.target.value)}
                            disabled={submitting}
                          />
                        </div>
                      </div>

                      <div className="form-group">
                        <label className="input-label">Địa chỉ chi tiết (Số nhà, tên đường, toà nhà) *</label>
                        <input
                          type="text"
                          className="form-input"
                          required
                          value={shippingStreetAddress}
                          onChange={(e) => setShippingStreetAddress(e.target.value)}
                          placeholder="Số 10 Phạm Văn Đồng, P. Dịch Vọng Hậu"
                          disabled={submitting}
                        />
                      </div>
                    </div>
                  )}

                  <div className="form-group">
                    <label className="input-label">Ghi chú cho shipper (tuỳ chọn)</label>
                    <textarea
                      className="form-input textarea-notes"
                      rows={2}
                      value={customerNotes}
                      onChange={(e) => setCustomerNotes(e.target.value)}
                      placeholder="Giao giờ hành chính, gọi trước khi đến..."
                      disabled={submitting}
                    />
                  </div>
                </div>

                {/* 2. Payment Method Section */}
                <div className="checkout-section-card">
                  <div className="section-card-title">
                    <CreditCard size={18} className="text-gold" />
                    <h3>2. Phương thức thanh toán</h3>
                  </div>

                  <div className="payment-options-grid">
                    <label
                      className={`payment-option-card ${paymentMethod === 'COD' ? 'payment-selected' : ''}`}
                    >
                      <input
                        type="radio"
                        name="paymentMethod"
                        value="COD"
                        checked={paymentMethod === 'COD'}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                        disabled={submitting}
                      />
                      <div className="payment-card-body">
                        <div className="payment-name">COD — Tiền mặt khi nhận hàng</div>
                        <div className="payment-desc">Kiểm tra kiện hàng và thanh toán trực tiếp cho nhân viên vận chuyển.</div>
                      </div>
                    </label>

                    <label
                      className={`payment-option-card ${paymentMethod === 'VNPAY' ? 'payment-selected' : ''}`}
                    >
                      <input
                        type="radio"
                        name="paymentMethod"
                        value="VNPAY"
                        checked={paymentMethod === 'VNPAY'}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                        disabled={submitting}
                      />
                      <div className="payment-card-body">
                        <div className="payment-name">VNPAY Sandbox (Mô phỏng QR &amp; Thẻ)</div>
                        <div className="payment-desc">Xác thực mã hóa HMAC-SHA512 qua cổng thanh toán thử nghiệm VNPAY.</div>
                      </div>
                    </label>

                    <label
                      className={`payment-option-card ${paymentMethod === 'MOCK' ? 'payment-selected' : ''}`}
                    >
                      <input
                        type="radio"
                        name="paymentMethod"
                        value="MOCK"
                        checked={paymentMethod === 'MOCK'}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                        disabled={submitting}
                      />
                      <div className="payment-card-body">
                        <div className="payment-name">MOCK Gateway (Ký số Sandbox)</div>
                        <div className="payment-desc">Mô phỏng phản hồi IPN tức thì chống trùng lặp request (Idempotency).</div>
                      </div>
                    </label>

                    <label
                      className={`payment-option-card ${paymentMethod === 'BANK_TRANSFER' ? 'payment-selected' : ''}`}
                    >
                      <input
                        type="radio"
                        name="paymentMethod"
                        value="BANK_TRANSFER"
                        checked={paymentMethod === 'BANK_TRANSFER'}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                        disabled={submitting}
                      />
                      <div className="payment-card-body">
                        <div className="payment-name">Chuyển khoản Ngân hàng (Manual Verification)</div>
                        <div className="payment-desc">Chuyển qua số tài khoản cửa hàng, nhân viên xác nhận đối soát.</div>
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              {/* Right Column: Order Items & Authoritative Summary */}
              <div className="checkout-summary-col">
                <div className="checkout-summary-card">
                  <div className="summary-card-header">
                    <FileCheck size={18} className="text-gold" />
                    <h3>Đơn hàng của bạn ({cart?.total_items || 0} sản phẩm)</h3>
                  </div>

                  {/* Compact items list */}
                  <div className="checkout-items-preview">
                    {cart?.items.map((item) => (
                      <div key={item.id} className="checkout-item-row">
                        <img
                          src={item.cover_image_url || 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&q=80&w=200'}
                          alt={item.book_title}
                          className="checkout-item-thumb"
                        />
                        <div className="checkout-item-info">
                          <div className="item-title">{item.book_title}</div>
                          <div className="item-meta">
                            <span>SL: {item.quantity}</span>
                            <span>&times;</span>
                            <span>{formatVND(item.unit_price)}</span>
                          </div>
                        </div>
                        <div className="item-subtotal">{formatVND(item.subtotal)}</div>
                      </div>
                    ))}
                  </div>

                  {/* Coupon Application Row */}
                  <div className="coupon-box">
                    <label className="input-label">
                      <Tag size={14} className="text-gold" />
                      <span>Mã giảm giá (Coupon):</span>
                    </label>
                    <div className="coupon-input-group">
                      <input
                        type="text"
                        className="form-input coupon-input"
                        placeholder="VD: GIAM20, NOVELIA10"
                        value={couponCode}
                        onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                        disabled={submitting || couponLoading || !!appliedCoupon}
                      />
                      {appliedCoupon ? (
                        <button
                          type="button"
                          className="btn-remove-coupon"
                          onClick={handleRemoveCoupon}
                          disabled={submitting}
                        >
                          Gỡ bỏ
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="btn-apply-coupon"
                          onClick={handleApplyCoupon}
                          disabled={submitting || couponLoading || !couponCode.trim()}
                        >
                          {couponLoading ? <Loader2 size={14} className="spin" /> : 'Áp dụng'}
                        </button>
                      )}
                    </div>

                    {appliedCoupon && (
                      <div className="coupon-success-tag">
                        <CheckCircle2 size={14} />
                        <span>Áp dụng thành công mã <strong>{appliedCoupon.code}</strong> (-{formatVND(appliedCoupon.discount_amount)})</span>
                      </div>
                    )}

                    {couponError && (
                      <div className="coupon-error-tag">
                        <AlertCircle size={14} />
                        <span>{couponError}</span>
                      </div>
                    )}
                  </div>

                  {/* Financial Breakdown */}
                  <div className="price-breakdown">
                    <div className="price-row">
                      <span>Tạm tính sách:</span>
                      <span>{formatVND(rawSubtotal)}</span>
                    </div>

                    <div className="price-row">
                      <span className="flex-center gap-1">
                        <Truck size={14} /> Phí vận chuyển:
                      </span>
                      <span>{shippingFee === 0 ? <strong className="text-success">Miễn phí</strong> : formatVND(shippingFee)}</span>
                    </div>

                    {discountAmount > 0 && (
                      <div className="price-row text-success">
                        <span>Giảm giá khuyến mãi:</span>
                        <span>-{formatVND(discountAmount)}</span>
                      </div>
                    )}

                    <div className="price-row total-order-row">
                      <span>Tổng thanh toán:</span>
                      <span className="grand-total-amount">{formatVND(estimatedTotal)}</span>
                    </div>
                  </div>

                  {checkoutError && (
                    <div className="checkout-error-banner" data-testid="checkout-error">
                      <AlertCircle size={16} />
                      <span>{checkoutError}</span>
                    </div>
                  )}

                  {/* Submit Button */}
                  <button
                    type="submit"
                    className="submit-checkout-btn"
                    disabled={submitting || !cart || cart.items.length === 0 || cart.has_stock_issues}
                  >
                    {submitting ? (
                      <>
                        <Loader2 size={18} className="spin" />
                        <span>Đang khóa kho &amp; khởi tạo đơn...</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck size={18} />
                        <span>Xác nhận &amp; Đặt hàng ngay</span>
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>

                  <p className="checkout-security-notice">
                    <ShieldCheck size={14} />
                    Mọi giao dịch tuân thủ kiểm định tồn kho ACID và chữ ký số an toàn.
                  </p>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Interactive Map Modal for Pin Placement */}
      <InteractiveMapModal
        isOpen={showMapModal}
        onClose={() => setShowMapModal(false)}
        initialLat={shippingLatitude}
        initialLng={shippingLongitude}
        onConfirmLocation={applyGeocodedResult}
        token={token || ''}
      />
    </div>
  );
};
