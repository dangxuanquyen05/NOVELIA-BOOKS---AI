"""Mock Reverse Geocoding provider with realistic Vietnamese administrative test fixtures."""

import math
from typing import Dict, List, Optional
from app.integrations.geo.base import (
    NormalizedAddress,
    OutOfBoundsError,
    ReverseGeocodingError,
    ReverseGeocodingProvider,
)
from app.integrations.geo.normalization import AddressNormalizationService


MOCK_GEO_FIXTURES: List[Dict] = [
    {
        "lat": 21.0285,
        "lng": 105.7896,
        "street_address": "Số 12, ngõ 158 Đường Cầu Giấy",
        "ward_name": "Phường Dịch Vọng",
        "ward_code": "00184",
        "district_name": "Quận Cầu Giấy",
        "district_code": "005",
        "province_name": "Hà Nội",
        "province_code": "01",
        "confidence": 0.95,
        "level": "house_number",
        "place_id": "MOCK_VN_HN_01",
    },
    {
        "lat": 21.0245,
        "lng": 105.8550,
        "street_address": "Số 24 Tràng Tiền",
        "ward_name": "Phường Tràng Tiền",
        "ward_code": "00025",
        "district_name": "Quận Hoàn Kiếm",
        "district_code": "001",
        "province_name": "Hà Nội",
        "province_code": "01",
        "confidence": 0.95,
        "level": "house_number",
        "place_id": "MOCK_VN_HN_02",
    },
    {
        "lat": 10.7769,
        "lng": 106.7009,
        "street_address": "Số 68 Lê Duẩn",
        "ward_name": "Phường Bến Nghé",
        "ward_code": "26734",
        "district_name": "Quận 1",
        "district_code": "760",
        "province_name": "TP. Hồ Chí Minh",
        "province_code": "79",
        "confidence": 0.95,
        "level": "house_number",
        "place_id": "MOCK_VN_HCM_01",
    },
    {
        "lat": 10.7950,
        "lng": 106.7218,
        "street_address": "Số 208 Nguyễn Hữu Cảnh",
        "ward_name": "Phường 22",
        "ward_code": "26830",
        "district_name": "Quận Bình Thạnh",
        "district_code": "765",
        "province_name": "TP. Hồ Chí Minh",
        "province_code": "79",
        "confidence": 0.95,
        "level": "house_number",
        "place_id": "MOCK_VN_HCM_02",
    },
    {
        "lat": 16.0715,
        "lng": 108.2208,
        "street_address": "Số 42 Bạch Đằng",
        "ward_name": "Phường Thạch Thang",
        "ward_code": "20203",
        "district_name": "Quận Hải Châu",
        "district_code": "492",
        "province_name": "Đà Nẵng",
        "province_code": "48",
        "confidence": 0.95,
        "level": "house_number",
        "place_id": "MOCK_VN_DN_01",
    },
]


class MockReverseGeocodingProvider(ReverseGeocodingProvider):
    """Deterministic and resilient mock provider for unit tests and local sandbox development."""

    def __init__(self, is_fallback: bool = False) -> None:
        self.is_fallback = is_fallback

    def is_configured(self) -> bool:
        return True

    def provider_name(self) -> str:
        return "MOCK_GEOCODER"

    async def reverse_geocode(self, lat: float, lng: float) -> NormalizedAddress:
        # Check simulated test error triggers
        if math.isclose(lat, 99.99, abs_tol=1e-2) and math.isclose(lng, 99.99, abs_tol=1e-2):
            raise ReverseGeocodingError("Simulated Mock Geocoding Provider Failure for Testing.")

        # Coordinate bounds check for Vietnam
        if not (8.0 <= lat <= 24.5 and 102.0 <= lng <= 111.0):
            raise OutOfBoundsError(
                f"Tọa độ ({lat:.4f}, {lng:.4f}) nằm ngoài lãnh thổ Việt Nam. Hệ thống NOVELIA BOOKS chỉ hỗ trợ giao hàng nội địa."
            )

        # Find closest fixture by Euclidean distance
        closest_fixture = None
        min_dist = float("inf")
        for fix in MOCK_GEO_FIXTURES:
            dist = math.hypot(lat - fix["lat"], lng - fix["lng"])
            if dist < min_dist:
                min_dist = dist
                closest_fixture = fix

        # If very close (within ~2km / 0.02 deg), return exact fixture
        if closest_fixture and min_dist < 0.025:
            matched = closest_fixture
            formatted_address = AddressNormalizationService.assemble_formatted_address(
                street_address=matched["street_address"],
                ward_name=matched["ward_name"],
                district_name=matched["district_name"],
                province_name=matched["province_name"],
            )
            return NormalizedAddress(
                province_name=matched["province_name"],
                province_code=matched["province_code"],
                district_name=matched["district_name"],
                district_code=matched["district_code"],
                ward_name=matched["ward_name"],
                ward_code=matched["ward_code"],
                street_address=matched["street_address"],
                formatted_address=formatted_address,
                latitude=lat,
                longitude=lng,
                place_id=matched["place_id"],
                confidence=matched["confidence"],
                level=matched["level"],
                source_provider="MOCK_GEOCODER",
                is_mock=True,
                raw_data={"matched_fixture": matched["place_id"], "distance_deg": min_dist},
            )

        # Otherwise interpolate region realistically based on latitude
        if lat >= 19.0:
            prov = "Hà Nội"
            prov_code = "01"
            dist = "Quận Cầu Giấy"
            dist_code = "005"
            ward = "Phường Dịch Vọng"
            ward_code = "00184"
        elif lat >= 14.0:
            prov = "Đà Nẵng"
            prov_code = "48"
            dist = "Quận Hải Châu"
            dist_code = "492"
            ward = "Phường Thạch Thang"
            ward_code = "20203"
        else:
            prov = "TP. Hồ Chí Minh"
            prov_code = "79"
            dist = "Quận 1"
            dist_code = "760"
            ward = "Phường Bến Nghé"
            ward_code = "26734"

        street = f"Khu vực tọa độ [{lat:.4f}, {lng:.4f}]"
        formatted_address = AddressNormalizationService.assemble_formatted_address(
            street_address=street,
            ward_name=ward,
            district_name=dist,
            province_name=prov,
        )

        return NormalizedAddress(
            province_name=prov,
            province_code=prov_code,
            district_name=dist,
            district_code=dist_code,
            ward_name=ward,
            ward_code=ward_code,
            street_address=street,
            formatted_address=formatted_address,
            latitude=lat,
            longitude=lng,
            place_id=f"MOCK_LOC_{int(lat*1000)}_{int(lng*1000)}",
            confidence=0.80,
            level="street",
            source_provider="MOCK_GEOCODER",
            is_mock=True,
            raw_data={"interpolated": True},
        )
