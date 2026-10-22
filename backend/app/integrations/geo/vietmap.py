"""VIETMAP Reverse Geocoding & Map provider adapter for Vietnam e-commerce delivery."""

import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.integrations.geo.base import (
    GeocodingConfigurationError,
    NormalizedAddress,
    OutOfBoundsError,
    ReverseGeocodingError,
    ReverseGeocodingProvider,
)
from app.integrations.geo.normalization import AddressNormalizationService

logger = logging.getLogger("novelia.geo.vietmap")


class VietMapGeocodingProvider(ReverseGeocodingProvider):
    """Production adapter for VietMap Reverse Geocoding APIs (v2 / v3)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 6.0,
    ) -> None:
        self.api_key = (api_key or settings.VIETMAP_API_KEY or "").strip()
        self.base_url = (base_url or settings.VIETMAP_API_URL or "https://maps.vietmap.vn/api").rstrip("/")
        self.timeout = timeout

    def is_configured(self) -> bool:
        """Returns True only when a non-empty, non-placeholder API key is set."""
        return bool(self.api_key and len(self.api_key) > 5 and not self.api_key.startswith("your_"))

    def provider_name(self) -> str:
        return "VIETMAP"

    async def reverse_geocode(self, lat: float, lng: float) -> NormalizedAddress:
        """Query VietMap Reverse Geocoding API to resolve coordinates to normalized address."""
        if not self.is_configured():
            raise GeocodingConfigurationError(
                "VIETMAP_API_KEY is not configured. Register at https://maps.vietmap.vn to obtain a live key, "
                "or configure GEOCODING_PROVIDER=mock for development/testing."
            )

        # Coordinate sanity check for Vietnam territory bounding box
        # Latitude ~ 8.0 to 24.0, Longitude ~ 102.0 to 110.0
        if not (8.0 <= lat <= 24.0 and 102.0 <= lng <= 110.0):
            raise OutOfBoundsError(
                f"Coordinates ({lat}, {lng}) appear to be outside of Vietnam territory bounds."
            )

        url = f"{self.base_url}/reverse/v3"
        params = {
            "apikey": self.api_key,
            "lat": lat,
            "lng": lng,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
        except httpx.TimeoutException:
            logger.error("VietMap API call timed out after %s seconds for (%s, %s)", self.timeout, lat, lng)
            raise ReverseGeocodingError("Dịch vụ định vị VietMap phản hồi quá chậm (timeout). Vui lòng thử lại sau.")
        except Exception as exc:
            logger.error("VietMap connection error: %s", exc)
            raise ReverseGeocodingError(f"Không thể kết nối đến máy chủ VietMap: {exc}")

        if response.status_code == 401 or response.status_code == 403:
            raise GeocodingConfigurationError(
                f"VietMap API key bị từ chối hoặc hết hạn (HTTP {response.status_code}). Vui lòng kiểm tra VIETMAP_API_KEY."
            )

        if response.status_code != 200:
            raise ReverseGeocodingError(
                f"VietMap trả về mã lỗi HTTP {response.status_code}: {response.text[:200]}"
            )

        try:
            payload = response.json()
        except Exception as exc:
            raise ReverseGeocodingError(f"Không thể đọc kết quả JSON từ VietMap: {exc}")

        return self._parse_vietmap_response(payload, lat, lng)

    def _parse_vietmap_response(self, payload: Any, lat: float, lng: float) -> NormalizedAddress:
        """Parse VietMap's v3/v2 payload into a strict NormalizedAddress instance."""
        results: List[Dict[str, Any]] = []
        if isinstance(payload, list):
            results = payload
        elif isinstance(payload, dict):
            if "data" in payload and isinstance(payload["data"], list):
                results = payload["data"]
            elif "results" in payload and isinstance(payload["results"], list):
                results = payload["results"]
            else:
                results = [payload]

        if not results:
            raise ReverseGeocodingError("VietMap không tìm thấy địa chỉ tại tọa độ này.")

        top = results[0]
        ref_id = top.get("ref_id") or top.get("id") or f"vm_{lat}_{lng}"
        full_address = top.get("address") or top.get("display") or top.get("name") or ""
        street_address = top.get("name") or ""

        province_name = ""
        province_code = "00"
        district_name = ""
        district_code = "000"
        ward_name = ""
        ward_code = "00000"

        # Parse boundaries if available (VietMap standard: type 1=Province, 2=District, 3=Ward)
        boundaries = top.get("boundaries", [])
        for b in boundaries:
            b_type = b.get("type")
            b_name = b.get("name", "").strip()
            prefix = b.get("prefix", "").strip()
            display_name = f"{prefix} {b_name}".strip() if prefix else b_name

            if b_type == 1:
                province_name = display_name
                province_code, province_name = AddressNormalizationService.resolve_province_code(b_name)
            elif b_type == 2:
                district_name = display_name
                district_code = str(b.get("id", "000"))
            elif b_type == 3:
                ward_name = display_name
                ward_code = str(b.get("id", "00000"))

        # Fallback if boundaries array is empty: split from formatted address
        if not province_name and full_address:
            parts = [p.strip() for p in full_address.split(",") if p.strip()]
            if len(parts) >= 1:
                province_code, province_name = AddressNormalizationService.resolve_province_code(parts[-1])
            if len(parts) >= 2:
                district_name = parts[-2]
            if len(parts) >= 3:
                ward_name = parts[-3]
            if len(parts) >= 4:
                street_address = ", ".join(parts[:-3])

        # If street address is empty or identical to full address, fallback
        if not street_address or street_address == full_address:
            # Strip ward, district, province from full_address
            cleaned = full_address
            for token in [province_name, district_name, ward_name]:
                if token and token in cleaned:
                    cleaned = cleaned.replace(token, "").strip(", ")
            street_address = cleaned or "Khu vực lân cận"

        formatted_address = AddressNormalizationService.assemble_formatted_address(
            street_address=street_address,
            ward_name=ward_name,
            district_name=district_name,
            province_name=province_name,
        ) or full_address

        confidence, level = AddressNormalizationService.calculate_confidence(
            street_address=street_address,
            ward_name=ward_name,
            district_name=district_name,
        )

        return NormalizedAddress(
            province_name=province_name or "Hà Nội",
            province_code=province_code,
            district_name=district_name or "Cầu Giấy",
            district_code=district_code,
            ward_name=ward_name or "Dịch Vọng",
            ward_code=ward_code,
            street_address=street_address,
            formatted_address=formatted_address,
            latitude=lat,
            longitude=lng,
            place_id=str(ref_id),
            confidence=confidence,
            level=level,
            source_provider="VIETMAP",
            is_mock=False,
            raw_data=top,
        )
