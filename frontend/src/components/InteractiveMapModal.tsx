import React, { useEffect, useRef, useState, useCallback } from 'react';
import { X, Search, Crosshair, MapPin, CheckCircle2, Loader2, Info, AlertTriangle } from 'lucide-react';
import * as L from 'leaflet';
import { authApi } from '../services/authApi';
import { MapConfig, ReverseGeocodeResult } from '../types/auth';

interface InteractiveMapModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialLat?: number | null;
  initialLng?: number | null;
  onConfirmLocation: (result: ReverseGeocodeResult) => void;
  token: string;
}

export const InteractiveMapModal: React.FC<InteractiveMapModalProps> = ({
  isOpen,
  onClose,
  initialLat,
  initialLng,
  onConfirmLocation,
  token,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  const [currentCoords, setCurrentCoords] = useState<{ lat: number; lng: number }>({
    lat: initialLat || 21.0285,
    lng: initialLng || 105.7896,
  });

  const [resolvedAddress, setResolvedAddress] = useState<ReverseGeocodeResult | null>(null);
  const [loadingGeocode, setLoadingGeocode] = useState(false);
  const [geocodeError, setGeocodeError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [mapConfig, setMapConfig] = useState<MapConfig | null>(null);
  const [searching, setSearching] = useState(false);

  // Fetch public map config (VietMap or OpenStreetMap)
  useEffect(() => {
    if (!isOpen || !token) return;
    authApi
      .getGeoConfig(token)
      .then((cfg) => setMapConfig(cfg))
      .catch((err) => {
        console.warn('Could not load dynamic map config, using default OSM:', err);
      });
  }, [isOpen, token]);

  // Reverse geocode a set of coordinates
  const triggerReverseGeocode = useCallback(
    async (lat: number, lng: number) => {
      if (!token) return;
      setLoadingGeocode(true);
      setGeocodeError(null);
      try {
        const res = await authApi.reverseGeocode(token, lat, lng);
        setResolvedAddress(res.address);
      } catch (err: unknown) {
        setGeocodeError(
          err instanceof Error ? err.message : 'Không thể xác định địa chỉ tại tọa độ này. Vui lòng chọn vị trí khác.',
        );
      } finally {
        setLoadingGeocode(false);
      }
    },
    [token],
  );

  // Initialize Leaflet Map
  useEffect(() => {
    if (!isOpen || !mapContainerRef.current) return;

    // Default center
    const centerLat = initialLat || mapConfig?.default_lat || 21.0285;
    const centerLng = initialLng || mapConfig?.default_lng || 105.7896;
    setCurrentCoords({ lat: centerLat, lng: centerLng });

    // Custom SVG Pin Icon
    const customPinIcon = L.divIcon({
      className: 'novelia-custom-map-pin',
      html: `
        <div style="position: relative; width: 36px; height: 36px; transform: translate(-18px, -36px); cursor: grab;">
          <svg viewBox="0 0 24 24" width="36" height="36" fill="#DC2626" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));">
            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>
            <circle cx="12" cy="10" r="3" fill="#FFFFFF"></circle>
          </svg>
        </div>
      `,
      iconSize: [36, 36],
      iconAnchor: [18, 36],
    });

    // Cleanup previous map if exists
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const tileUrl = mapConfig?.tile_url || 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    const attribution = mapConfig?.attribution || '&copy; OpenStreetMap contributors';

    const map = L.map(mapContainerRef.current, {
      center: [centerLat, centerLng],
      zoom: 16,
      zoomControl: true,
    });
    mapInstanceRef.current = map;

    L.tileLayer(tileUrl, {
      attribution: attribution,
      maxZoom: 19,
    }).addTo(map);

    const marker = L.marker([centerLat, centerLng], {
      icon: customPinIcon,
      draggable: true,
    }).addTo(map);
    markerRef.current = marker;

    marker.bindPopup(`<b>Vị trí của bạn</b><br/>${centerLat.toFixed(4)}, ${centerLng.toFixed(4)}`).openPopup();

    // Event: Marker dragged
    marker.on('dragend', () => {
      const pos = marker.getLatLng();
      setCurrentCoords({ lat: pos.lat, lng: pos.lng });
      marker.setPopupContent(`<b>Vị trí của bạn</b><br/>${pos.lat.toFixed(4)}, ${pos.lng.toFixed(4)}`).openPopup();
      triggerReverseGeocode(pos.lat, pos.lng);
    });

    // Event: Click on map to move marker
    map.on('click', (e: L.LeafletMouseEvent) => {
      marker.setLatLng(e.latlng);
      setCurrentCoords({ lat: e.latlng.lat, lng: e.latlng.lng });
      marker.setPopupContent(`<b>Vị trí của bạn</b><br/>${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`).openPopup();
      triggerReverseGeocode(e.latlng.lat, e.latlng.lng);
    });

    // Initial reverse geocode
    triggerReverseGeocode(centerLat, centerLng);

    // Invalidate size after modal animation
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 250);

    return () => {
      clearTimeout(timer);
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [isOpen, mapConfig, initialLat, initialLng, triggerReverseGeocode]);

  // Handle locate me action
  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      alert('Trình duyệt của bạn không hỗ trợ định vị vị trí.');
      return;
    }
    setLoadingGeocode(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setCurrentCoords({ lat: latitude, lng: longitude });
        if (mapInstanceRef.current && markerRef.current) {
          mapInstanceRef.current.setView([latitude, longitude], 16);
          markerRef.current.setLatLng([latitude, longitude]);
          markerRef.current.setPopupContent(`<b>Vị trí của bạn</b><br/>${latitude.toFixed(4)}, ${longitude.toFixed(4)}`).openPopup();
        }
        triggerReverseGeocode(latitude, longitude);
      },
      (err) => {
        setLoadingGeocode(false);
        alert(`Không thể lấy vị trí: ${err.message}`);
      },
      { timeout: 10000, enableHighAccuracy: true },
    );
  };

  // Search simple address simulation
  const handleSearchAddress = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    // Standard Vietnamese landmarks quick match
    const queryLower = searchQuery.toLowerCase();
    let target = { lat: 21.0285, lng: 105.7896 }; // Default Cầu Giấy

    if (queryLower.includes('tràng tiền') || queryLower.includes('hoàn kiếm')) {
      target = { lat: 21.0245, lng: 105.855 };
    } else if (queryLower.includes('bến nghé') || queryLower.includes('quận 1') || queryLower.includes('lê duẩn')) {
      target = { lat: 10.7769, lng: 106.7009 };
    } else if (queryLower.includes('bình thạnh') || queryLower.includes('nguyễn hữu cảnh')) {
      target = { lat: 10.795, lng: 106.7218 };
    } else if (queryLower.includes('đà nẵng') || queryLower.includes('hải châu') || queryLower.includes('bạch đằng')) {
      target = { lat: 16.0715, lng: 108.2208 };
    }

    setCurrentCoords(target);
    if (mapInstanceRef.current && markerRef.current) {
      mapInstanceRef.current.setView([target.lat, target.lng], 16);
      markerRef.current.setLatLng([target.lat, target.lng]);
      markerRef.current.setPopupContent(`<b>Vị trí tìm thấy</b><br/>${target.lat.toFixed(4)}, ${target.lng.toFixed(4)}`).openPopup();
    }
    triggerReverseGeocode(target.lat, target.lng);
    setSearching(false);
  };

  const handleConfirm = () => {
    if (resolvedAddress) {
      onConfirmLocation(resolvedAddress);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="smart-map-modal-backdrop">
      <div className="smart-map-modal-container">
        {/* Modal Header */}
        <div className="smart-map-modal-header">
          <div className="smart-map-modal-header-left">
            <div className="smart-map-modal-icon-badge">
              <MapPin size={20} />
            </div>
            <div>
              <h2 className="smart-map-modal-title">Chọn vị trí trên bản đồ</h2>
              <p className="smart-map-modal-subtitle">Di chuyển bản đồ hoặc kéo ghim đỏ đến đúng vị trí nhận sách</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="smart-map-modal-close-btn"
            title="Đóng bản đồ"
          >
            <X size={20} />
          </button>
        </div>

        {/* Search Bar & Controls */}
        <div className="smart-map-search-bar">
          <form onSubmit={handleSearchAddress} style={{ display: 'flex', width: '100%', gap: '0.65rem' }}>
            <div className="smart-map-search-input-box">
              <Search size={16} className="smart-map-search-icon" />
              <input
                type="text"
                className="smart-map-search-input"
                placeholder="Tìm kiếm địa điểm, địa chỉ (VD: Cầu Giấy, Tràng Tiền, Quận 1...)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={searching || !searchQuery.trim()}
              className="smart-map-search-btn"
            >
              {searching ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
              <span>Tìm</span>
            </button>
            <button
              type="button"
              onClick={handleLocateMe}
              className="smart-map-locate-btn"
              title="Lấy vị trí GPS hiện tại của tôi"
            >
              <Crosshair size={16} />
              <span className="hidden sm:inline">Vị trí của tôi</span>
            </button>
          </form>
        </div>

        {/* Map Canvas Container */}
        <div className="smart-map-canvas-container">
          <div ref={mapContainerRef} style={{ width: '100%', height: '100%', zIndex: 10 }} />

          {/* Provider Badge / Watermark */}
          <div className="smart-map-provider-watermark">
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
            <span>Bản đồ: {mapConfig?.provider || 'VIETMAP / OSM'}</span>
            {mapConfig?.is_mock && (
              <span style={{ background: '#fef3c7', color: '#92400e', fontSize: '10px', padding: '1px 5px', borderRadius: 4, fontWeight: 700 }}>
                MOCK TEST
              </span>
            )}
          </div>

          {/* Loading Indicator */}
          {loadingGeocode && (
            <div className="smart-map-loading-overlay">
              <div className="smart-map-loading-box">
                <Loader2 size={20} className="animate-spin text-amber-600" />
                <span>Đang nhận diện địa chỉ tại vị trí ghim...</span>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Address Confirmation Bar */}
        <div className="smart-map-modal-footer">
          {geocodeError ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 12, color: '#991b1b', width: '100%' }}>
              <AlertTriangle size={18} className="text-red-600 shrink-0" />
              <p style={{ margin: 0, fontSize: '0.875rem', fontWeight: 600 }}>{geocodeError}</p>
            </div>
          ) : resolvedAddress ? (
            <>
              <div className="smart-map-footer-address-info">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div className="smart-map-footer-badge">
                    <CheckCircle2 size={13} />
                    <span>Địa chỉ được xác định</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: '#78716c', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <Info size={12} />
                    Độ chính xác: {Math.round(resolvedAddress.confidence * 100)}%
                  </span>
                  {resolvedAddress.is_mock && (
                    <span style={{ fontSize: '10px', fontWeight: 700, color: '#b45309', background: '#fef3c7', padding: '1px 5px', borderRadius: 4 }}>
                      TEST FIXTURE
                    </span>
                  )}
                </div>

                <div className="smart-map-footer-text-row">
                  <MapPin size={17} style={{ color: '#d97706', flexShrink: 0, marginTop: 2 }} />
                  <p className="smart-map-footer-address-string">
                    {resolvedAddress.formatted_address}
                  </p>
                </div>

                <p className="smart-map-footer-subtext">
                  Tọa độ: {currentCoords.lat.toFixed(4)}, {currentCoords.lng.toFixed(4)} • Phường/Xã: {resolvedAddress.ward_name} • Tỉnh/TP: {resolvedAddress.province_name}
                </p>
              </div>

              <div className="smart-map-footer-actions">
                <button
                  type="button"
                  onClick={handleLocateMe}
                  className="smart-map-btn-retry"
                >
                  Thử lại
                </button>
                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={loadingGeocode}
                  className="smart-map-btn-confirm"
                >
                  Xác nhận địa chỉ
                </button>
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', width: '100%', padding: '0.5rem 0', fontSize: '0.875rem', color: '#78716c' }}>
              Chọn một vị trí trên bản đồ để xác định địa chỉ giao hàng
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
