"""Comprehensive test suite for Smart Address Auto-Detection, Reverse Geocoding, and VietMap integration."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.integrations.geo import (
    AddressNormalizationService,
    GeocodingConfigurationError,
    MockReverseGeocodingProvider,
    NormalizedAddress,
    OutOfBoundsError,
    ReverseGeocodingError,
    VietMapGeocodingProvider,
    get_reverse_geocoding_provider,
)
from app.main import app
from app.models.user import User, UserAddress
from app.repositories.user_repo import UserRepository
from app.schemas.user import AddressCreateRequest, AddressUpdateRequest
from app.services.user_service import UserService


# Fixture for a standard authenticated customer
@pytest.fixture
def mock_customer():
    return User(
        id=10,
        email="reader@novelia.vn",
        full_name="Nguyễn Văn An",
        phone="0987654321",
        is_active=True,
    )


# -----------------------------------------------------------------------------
# 1. AddressNormalizationService Unit Tests
# -----------------------------------------------------------------------------
class TestAddressNormalizationService:
    def test_resolve_province_code(self):
        code, name = AddressNormalizationService.resolve_province_code("Thành phố Hà Nội")
        assert code == "01"
        assert name == "Hà Nội"

        code_hcm, name_hcm = AddressNormalizationService.resolve_province_code("TP. Hồ Chí Minh")
        assert code_hcm == "79"
        assert name_hcm == "TP. Hồ Chí Minh"

        code_dn, name_dn = AddressNormalizationService.resolve_province_code("Đà Nẵng")
        assert code_dn == "48"
        assert name_dn == "Đà Nẵng"

    def test_calculate_confidence_with_house_number(self):
        confidence, level = AddressNormalizationService.calculate_confidence(
            street_address="Số 12, ngõ 158 Đường Cầu Giấy",
            ward_name="Dịch Vọng",
            district_name="Cầu Giấy",
        )
        assert confidence == 0.95
        assert level == "house_number"

    def test_calculate_confidence_street_level_only(self):
        confidence, level = AddressNormalizationService.calculate_confidence(
            street_address="Đường Duy Tân",
            ward_name="Dịch Vọng Hậu",
            district_name="Cầu Giấy",
        )
        assert confidence == 0.85
        assert level == "street"

    def test_calculate_confidence_no_street_address(self):
        confidence, level = AddressNormalizationService.calculate_confidence(
            street_address="",
            ward_name="Dịch Vọng Hậu",
            district_name="Cầu Giấy",
        )
        assert confidence == 0.70
        assert level == "ward"

    def test_assemble_formatted_address_deduplication(self):
        formatted = AddressNormalizationService.assemble_formatted_address(
            street_address="Số 12 Đường Cầu Giấy",
            ward_name="Dịch Vọng",
            district_name="Cầu Giấy",
            province_name="Hà Nội",
        )
        assert "Số 12 Đường Cầu Giấy" in formatted
        assert "Phường Dịch Vọng" in formatted
        assert "Quận Cầu Giấy" in formatted
        assert "Hà Nội" in formatted


# -----------------------------------------------------------------------------
# 2. MockReverseGeocodingProvider Unit Tests
# -----------------------------------------------------------------------------
class TestMockReverseGeocodingProvider:
    @pytest.mark.asyncio
    async def test_reverse_geocode_known_hanoi_fixture(self):
        provider = MockReverseGeocodingProvider()
        result = await provider.reverse_geocode(21.0285, 105.7896)
        assert isinstance(result, NormalizedAddress)
        assert result.province_name == "Hà Nội"
        assert "Cầu Giấy" in result.district_name
        assert "Dịch Vọng" in result.ward_name
        assert result.confidence == 0.95
        assert result.is_mock is True
        assert result.source_provider == "MOCK_GEOCODER"

    @pytest.mark.asyncio
    async def test_reverse_geocode_out_of_bounds_raises(self):
        provider = MockReverseGeocodingProvider()
        with pytest.raises(OutOfBoundsError):
            await provider.reverse_geocode(0.0, 0.0)

    @pytest.mark.asyncio
    async def test_reverse_geocode_simulated_error(self):
        provider = MockReverseGeocodingProvider()
        with pytest.raises(ReverseGeocodingError):
            await provider.reverse_geocode(99.99, 99.99)


# -----------------------------------------------------------------------------
# 3. VietMapGeocodingProvider Unit Tests
# -----------------------------------------------------------------------------
class TestVietMapGeocodingProvider:
    def test_is_configured_false_when_empty_key(self):
        provider = VietMapGeocodingProvider(api_key="")
        assert provider.is_configured() is False

    @pytest.mark.asyncio
    async def test_reverse_geocode_unconfigured_raises_error(self):
        provider = VietMapGeocodingProvider(api_key="")
        with pytest.raises(GeocodingConfigurationError) as exc:
            await provider.reverse_geocode(21.0285, 105.7896)
        assert "VIETMAP_API_KEY is not configured" in str(exc.value)

    @pytest.mark.asyncio
    async def test_reverse_geocode_with_mocked_http_success(self):
        fake_vietmap_response = [
            {
                "ref_id": "VM_123456",
                "distance": 0.0,
                "address": "Số 12, Ngõ 158 Cầu Giấy, Phường Dịch Vọng, Quận Cầu Giấy, Hà Nội",
                "name": "12 Ngõ 158 Cầu Giấy",
                "display": "Số 12, Ngõ 158 Cầu Giấy, Phường Dịch Vọng, Quận Cầu Giấy, Hà Nội",
                "boundaries": [
                    {"id": 1, "name": "Hà Nội", "prefix": "Thành phố", "type": 1},
                    {"id": 2, "name": "Cầu Giấy", "prefix": "Quận", "type": 2},
                    {"id": 3, "name": "Dịch Vọng", "prefix": "Phường", "type": 3},
                ],
            }
        ]

        provider = VietMapGeocodingProvider(api_key="valid-test-key-12345")
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = fake_vietmap_response

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await provider.reverse_geocode(21.0285, 105.7896)
            assert result.source_provider == "VIETMAP"
            assert result.is_mock is False
            assert result.province_name == "Hà Nội"
            assert result.district_name == "Quận Cầu Giấy"
            assert result.ward_name == "Phường Dịch Vọng"
            assert result.place_id == "VM_123456"
            assert result.confidence == 0.95


# -----------------------------------------------------------------------------
# 4. Provider Factory Unit Tests
# -----------------------------------------------------------------------------
class TestGeocodingFactory:
    def test_factory_fallback_to_mock_when_no_key(self):
        with patch.object(settings, "VIETMAP_API_KEY", ""):
            provider = get_reverse_geocoding_provider(provider_name="auto")
            assert isinstance(provider, MockReverseGeocodingProvider)
            assert provider.is_fallback is True

    def test_factory_returns_vietmap_when_key_present(self):
        with patch.object(settings, "VIETMAP_API_KEY", "real-vietmap-live-key-xyz"):
            provider = get_reverse_geocoding_provider(provider_name="auto")
            assert isinstance(provider, VietMapGeocodingProvider)


# -----------------------------------------------------------------------------
# 5. API Endpoints Integration Tests
# -----------------------------------------------------------------------------
class TestSmartAddressEndpoints:
    @pytest.fixture(autouse=True)
    def setup_client(self, mock_customer):
        app.dependency_overrides[get_current_active_user] = lambda: mock_customer
        app.dependency_overrides[get_db] = lambda: MagicMock()
        yield
        app.dependency_overrides.clear()

    def test_get_geo_config(self):
        client = TestClient(app)
        res = client.get("/api/v1/addresses/geo/config")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "provider" in data
        assert "tile_url" in data
        assert "attribution" in data
        assert "default_lat" in data
        assert "default_lng" in data

    def test_post_reverse_geocode_valid_coords(self):
        client = TestClient(app)
        payload = {"lat": 21.0285, "lng": 105.7896}
        res = client.post("/api/v1/addresses/reverse-geocode", json=payload)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["status"] == "success"
        addr = data["address"]
        assert addr["province_name"] == "Hà Nội"
        assert "Cầu Giấy" in addr["district_name"]
        assert "Dịch Vọng" in addr["ward_name"]
        assert addr["latitude"] == 21.0285
        assert addr["longitude"] == 105.7896
        assert addr["confidence"] >= 0.8

    def test_post_reverse_geocode_out_of_bounds(self):
        client = TestClient(app)
        payload = {"lat": 0.0, "lng": 0.0}
        res = client.post("/api/v1/addresses/reverse-geocode", json=payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_and_update_address_with_geo_fields(self, mock_customer):
        mock_db = MagicMock()
        create_payload = AddressCreateRequest(
            recipient_name="Nguyễn Văn An",
            phone="0987654321",
            province_name="Hà Nội",
            province_code="01",
            district_name="Quận Cầu Giấy",
            district_code="005",
            ward_name="Phường Dịch Vọng",
            ward_code="00184",
            street_address="Số 12, ngõ 158 Đường Cầu Giấy",
            formatted_address="Số 12, ngõ 158 Đường Cầu Giấy, Phường Dịch Vọng, Quận Cầu Giấy, Hà Nội",
            latitude=21.0285,
            longitude=105.7896,
            place_id="MOCK_VN_HN_01",
            source_provider="VIETMAP",
            confidence=0.95,
            is_default=True,
        )

        with patch("app.repositories.user_repo.UserRepository.create_address") as mock_create:
            mock_addr = UserAddress(
                id=1,
                user_id=mock_customer.id,
                recipient_name=create_payload.recipient_name,
                phone=create_payload.phone,
                province_name=create_payload.province_name,
                province_code=create_payload.province_code,
                district_name=create_payload.district_name,
                district_code=create_payload.district_code,
                ward_name=create_payload.ward_name,
                ward_code=create_payload.ward_code,
                street_address=create_payload.street_address,
                formatted_address=create_payload.formatted_address,
                latitude=create_payload.latitude,
                longitude=create_payload.longitude,
                place_id=create_payload.place_id,
                source_provider=create_payload.source_provider,
                confidence=create_payload.confidence,
                is_default=True,
            )
            mock_create.return_value = mock_addr

            addr = UserService.add_address(mock_db, mock_customer.id, create_payload)
            assert addr.latitude == 21.0285
            assert addr.longitude == 105.7896
            assert addr.formatted_address == create_payload.formatted_address
            assert addr.source_provider == "VIETMAP"
