import React, { useState, useCallback } from 'react';
import {
  Navigation,
  Map as MapIcon,
  MapPin,
  User as UserIcon,
  Phone,
  ChevronRight,
  Loader2,
  AlertCircle,
  Edit3,
  Check,
  Info,
} from 'lucide-react';
import { authApi } from '../services/authApi';
import { AddressCreatePayload, ReverseGeocodeResult } from '../types/auth';
import { InteractiveMapModal } from './InteractiveMapModal';

export interface SmartAddressPickerProps {
  token: string;
  initialRecipientName?: string;
  initialPhone?: string;
  onSaveAddress: (payload: AddressCreatePayload) => Promise<void>;
  onCancel?: () => void;
  submitting?: boolean;
  submitButtonText?: string;
  cancelButtonText?: string;
  breadcrumb?: string;
}

export const SmartAddressPicker: React.FC<SmartAddressPickerProps> = ({
  token,
  initialRecipientName = '',
  initialPhone = '',
  onSaveAddress,
  onCancel,
  submitting = false,
  submitButtonText = 'Lưu địa chỉ',
  cancelButtonText = 'Hủy',
  breadcrumb = 'Trang chủ / Thanh toán',
}) => {
  // Form fields
  const [recipientName, setRecipientName] = useState(initialRecipientName);
  const [phone, setPhone] = useState(initialPhone);
  const [isDefault, setIsDefault] = useState(false);

  // Address state
  const [detectedAddress, setDetectedAddress] = useState<ReverseGeocodeResult | null>(null);
  const [provinceName, setProvinceName] = useState('Hà Nội');
  const [provinceCode, setProvinceCode] = useState('01');
  const [districtName, setDistrictName] = useState('Quận Cầu Giấy');
  const [districtCode, setDistrictCode] = useState('005');
  const [wardName, setWardName] = useState('Phường Dịch Vọng');
  const [wardCode, setWardCode] = useState('00184');
  const [streetAddress, setStreetAddress] = useState('');
  const [formattedAddress, setFormattedAddress] = useState('');
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [placeId, setPlaceId] = useState<string | null>(null);
  const [sourceProvider, setSourceProvider] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);

  // UI state
  const [isLocating, setIsLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [showMapModal, setShowMapModal] = useState(false);
  const [showManualFields, setShowManualFields] = useState(false);

  // Apply resolved geocode result to form
  const applyGeocodedResult = useCallback((res: ReverseGeocodeResult) => {
    setDetectedAddress(res);
    setProvinceName(res.province_name);
    setProvinceCode(res.province_code);
    setDistrictName(res.district_name);
    setDistrictCode(res.district_code);
    setWardName(res.ward_name);
    setWardCode(res.ward_code);
    setStreetAddress(res.street_address);
    setFormattedAddress(res.formatted_address);
    setLatitude(res.latitude);
    setLongitude(res.longitude);
    setPlaceId(res.place_id || null);
    setSourceProvider(res.source_provider);
    setConfidence(res.confidence);
    setLocationError(null);
  }, []);

  // Option A: Use current location
  const handleRequestCurrentLocation = () => {
    setLocationError(null);
    if (!navigator.geolocation) {
      setLocationError('Trình duyệt của bạn không hỗ trợ Geolocation. Vui lòng sử dụng tính năng "Chọn trên bản đồ".');
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude: lat, longitude: lng } = position.coords;
        try {
          const res = await authApi.reverseGeocode(token, lat, lng);
          applyGeocodedResult(res.address);
        } catch (err: unknown) {
          setLocationError(
            err instanceof Error
              ? err.message
              : 'Dịch vụ định vị tạm thời không khả dụng. Vui lòng bấm "Chọn trên bản đồ" để xác định vị trí.',
          );
        } finally {
          setIsLocating(false);
        }
      },
      (error) => {
        setIsLocating(false);
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setLocationError(
              'Bạn đã từ chối quyền truy cập vị trí trên trình duyệt. Vui lòng cho phép quyền vị trí hoặc sử dụng "Chọn trên bản đồ".',
            );
            break;
          case error.POSITION_UNAVAILABLE:
            setLocationError('Không thể nhận tín hiệu GPS. Vui lòng thử lại hoặc chọn vị trí trên bản đồ.');
            break;
          case error.TIMEOUT:
            setLocationError('Yêu cầu định vị quá thời gian chờ (timeout). Vui lòng thử lại.');
            break;
          default:
            setLocationError('Lỗi định vị không xác định. Vui lòng sử dụng "Chọn trên bản đồ".');
        }
      },
      {
        timeout: 10000,
        enableHighAccuracy: true,
        maximumAge: 0,
      },
    );
  };

  // Submit Handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recipientName.trim()) {
      alert('Vui lòng nhập họ và tên người nhận.');
      return;
    }
    if (!phone.trim()) {
      alert('Vui lòng nhập số điện thoại người nhận.');
      return;
    }
    if (!streetAddress.trim() && !formattedAddress.trim()) {
      alert('Vui lòng bấm "Sử dụng vị trí hiện tại" hoặc "Chọn trên bản đồ" để tự động xác định địa chỉ.');
      return;
    }

    const payload: AddressCreatePayload = {
      recipient_name: recipientName.trim(),
      phone: phone.trim(),
      province_name: provinceName.trim() || 'Hà Nội',
      province_code: provinceCode.trim() || '01',
      district_name: districtName.trim() || 'Quận Cầu Giấy',
      district_code: districtCode.trim() || '005',
      ward_name: wardName.trim() || 'Phường Dịch Vọng',
      ward_code: wardCode.trim() || '00184',
      street_address: streetAddress.trim() || formattedAddress.trim(),
      formatted_address: formattedAddress.trim() || streetAddress.trim(),
      latitude: latitude,
      longitude: longitude,
      place_id: placeId,
      source_provider: sourceProvider,
      confidence: confidence,
      is_default: isDefault,
    };

    await onSaveAddress(payload);
  };

  return (
    <div className="smart-address-container">
      {/* Breadcrumb & Header */}
      <div>
        <div className="smart-address-breadcrumb">{breadcrumb}</div>
        <h1 className="smart-address-title">Địa chỉ nhận hàng</h1>
        <p className="smart-address-subtitle">
          Chọn vị trí để hệ thống tự động xác định địa chỉ của bạn. Bạn có thể điều chỉnh lại nếu cần.
        </p>
      </div>

      {/* Main 2 Selection Buttons */}
      <div className="smart-address-options-grid">
        {/* Option A: Use Current Location */}
        <button
          type="button"
          onClick={handleRequestCurrentLocation}
          disabled={isLocating}
          className={`smart-address-option-btn smart-address-option-btn-gps ${isLocating ? 'loading' : ''}`}
        >
          <div className="smart-address-option-left">
            <div className="smart-address-option-icon-box smart-address-option-icon-gps">
              {isLocating ? <Loader2 size={24} className="animate-spin text-amber-700" /> : <Navigation size={22} className="rotate-45" />}
            </div>
            <div>
              <h3 className="smart-address-option-heading">Sử dụng vị trí hiện tại</h3>
              <p className="smart-address-option-desc">
                {isLocating ? 'Đang truy vấn tín hiệu GPS...' : 'Cho phép trình duyệt lấy vị trí, sau đó tự điền địa chỉ.'}
              </p>
            </div>
          </div>
          <ChevronRight size={20} className="text-stone-400 shrink-0 ml-2" />
        </button>

        {/* Option B: Choose on Map */}
        <button
          type="button"
          onClick={() => setShowMapModal(true)}
          className="smart-address-option-btn"
        >
          <div className="smart-address-option-left">
            <div className="smart-address-option-icon-box smart-address-option-icon-map">
              <MapIcon size={22} />
            </div>
            <div>
              <h3 className="smart-address-option-heading">Chọn trên bản đồ</h3>
              <p className="smart-address-option-desc">
                Di chuyển bản đồ, đặt ghim đúng vị trí nhà hoặc nơi nhận hàng.
              </p>
            </div>
          </div>
          <ChevronRight size={20} className="text-stone-400 shrink-0 ml-2" />
        </button>
      </div>

      {/* Geolocation Error Alert */}
      {locationError && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-3 mb-4">
          <AlertCircle size={20} className="text-amber-700 shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold">Thông báo định vị vị trí</p>
            <p className="text-xs mt-0.5 text-amber-800">{locationError}</p>
          </div>
        </div>
      )}

      {/* Recognized Address Card */}
      {detectedAddress && (
        <div className="smart-address-recognized-card">
          <div className="smart-address-recognized-header">
            <div className="smart-address-recognized-badge-pill">
              <Check size={13} strokeWidth={3} />
              <span>Địa chỉ được hệ thống nhận diện</span>
            </div>
            <button
              type="button"
              onClick={() => setShowManualFields(!showManualFields)}
              className="smart-address-adjust-link"
            >
              <Edit3 size={13} />
              <span>{showManualFields ? 'Ẩn chi tiết điều chỉnh' : 'Điều chỉnh chi tiết'}</span>
            </button>
          </div>

          <div className="smart-address-recognized-layout">
            {/* Left: Address details and badge */}
            <div>
              <div className="smart-address-recognized-text-box">
                <MapPin size={18} className="smart-address-recognized-pin-icon" />
                <p className="smart-address-recognized-address-text">
                  {detectedAddress.formatted_address}
                </p>
              </div>

              <div className="smart-address-recognized-meta-row">
                <span className="smart-address-pill-autofill">
                  Tự động điền từ vị trí của bạn
                </span>
                <span className="smart-address-confidence-badge">
                  <Info size={12} />
                  Độ chính xác: {Math.round(detectedAddress.confidence * 100)}%
                </span>
                {detectedAddress.is_mock && (
                  <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">
                    TEST MOCK
                  </span>
                )}
              </div>
            </div>

            {/* Right: Mini Map Preview */}
            <div className="smart-address-minimap-preview">
              <div
                className="absolute inset-0 bg-cover bg-center opacity-80"
                style={{
                  backgroundImage: `url('https://tile.openstreetmap.org/16/${Math.floor(((detectedAddress.longitude + 180) / 360) * Math.pow(2, 16))}/${Math.floor(((1 - Math.log(Math.tan((detectedAddress.latitude * Math.PI) / 180) + 1 / Math.cos((detectedAddress.latitude * Math.PI) / 180)) / Math.PI) / 2) * Math.pow(2, 16))}.png')`,
                }}
              />
              <div className="smart-address-minimap-pin">
                <div className="smart-address-minimap-pin-marker">
                  <MapPin size={14} />
                </div>
                <span className="smart-address-minimap-coords">
                  {detectedAddress.latitude.toFixed(4)}, {detectedAddress.longitude.toFixed(4)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Manual Administrative Adjustment Drawer (Collapsible) */}
      {showManualFields && (
        <div className="smart-address-manual-drawer">
          <div className="smart-address-manual-header">
            <h4 className="smart-address-manual-heading">
              Điều chỉnh địa giới hành chính (Tùy chọn)
            </h4>
            <span className="text-xs text-stone-400">Chuẩn hóa hành chính hai cấp</span>
          </div>

          <div className="smart-address-inputs-row">
            <div className="smart-address-form-field">
              <label className="smart-address-form-label">Tỉnh / Thành phố *</label>
              <input
                type="text"
                className="smart-address-input"
                style={{ paddingLeft: '1rem' }}
                value={provinceName}
                onChange={(e) => setProvinceName(e.target.value)}
                placeholder="VD: Hà Nội"
              />
            </div>
            <div className="smart-address-form-field">
              <label className="smart-address-form-label">Phường / Xã *</label>
              <input
                type="text"
                className="smart-address-input"
                style={{ paddingLeft: '1rem' }}
                value={wardName}
                onChange={(e) => setWardName(e.target.value)}
                placeholder="VD: Phường Dịch Vọng"
              />
            </div>
          </div>

          <div className="smart-address-form-field" style={{ marginTop: '0.85rem' }}>
            <label className="smart-address-form-label">Địa chỉ cụ thể (Số nhà, ngõ, tên đường) *</label>
            <div className="smart-address-input-wrapper">
              <input
                type="text"
                className="smart-address-input"
                style={{ paddingLeft: '1rem', paddingRight: '2.5rem' }}
                value={streetAddress}
                onChange={(e) => {
                  setStreetAddress(e.target.value);
                  setFormattedAddress(e.target.value);
                }}
                placeholder="VD: Số 12, ngõ 158 Đường Cầu Giấy"
              />
              <MapPin size={16} className="smart-address-input-icon" style={{ left: 'auto', right: '0.85rem' }} />
            </div>
          </div>
        </div>
      )}

      {/* Recipient Form */}
      <form onSubmit={handleSubmit}>
        <div className="smart-address-inputs-row">
          {/* Recipient Name */}
          <div className="smart-address-form-field">
            <label className="smart-address-form-label">Họ và tên người nhận *</label>
            <div className="smart-address-input-wrapper">
              <UserIcon size={16} className="smart-address-input-icon" />
              <input
                type="text"
                required
                className="smart-address-input"
                placeholder="Nguyễn Văn An"
                value={recipientName}
                onChange={(e) => setRecipientName(e.target.value)}
                disabled={submitting}
              />
            </div>
          </div>

          {/* Recipient Phone */}
          <div className="smart-address-form-field">
            <label className="smart-address-form-label">Số điện thoại *</label>
            <div className="smart-address-input-wrapper">
              <Phone size={16} className="smart-address-input-icon" />
              <input
                type="tel"
                required
                className="smart-address-input"
                placeholder="09xx xxx xxx"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={submitting}
              />
            </div>
          </div>
        </div>

        {/* Checkbox Default Address */}
        <div className="smart-address-checkbox-row">
          <input
            type="checkbox"
            id="smart-default-checkbox"
            checked={isDefault}
            onChange={(e) => setIsDefault(e.target.checked)}
            className="smart-address-checkbox"
          />
          <label htmlFor="smart-default-checkbox" className="smart-address-checkbox-label">
            Đặt làm địa chỉ mặc định
          </label>
        </div>

        {/* Form Action Buttons */}
        <div className="smart-address-actions-row">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={submitting}
              className="smart-address-btn-cancel"
            >
              {cancelButtonText}
            </button>
          )}
          <button
            type="submit"
            disabled={submitting || (!detectedAddress && !streetAddress)}
            className="smart-address-btn-submit"
          >
            {submitting && <Loader2 size={16} className="animate-spin" />}
            <span>{submitButtonText}</span>
          </button>
        </div>
      </form>

      {/* Interactive Map Modal */}
      <InteractiveMapModal
        isOpen={showMapModal}
        onClose={() => setShowMapModal(false)}
        initialLat={latitude}
        initialLng={longitude}
        onConfirmLocation={applyGeocodedResult}
        token={token}
      />
    </div>
  );
};
