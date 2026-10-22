from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.integrations.geo import (
    GeocodingConfigurationError,
    OutOfBoundsError,
    ReverseGeocodingError,
    get_reverse_geocoding_provider,
)
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
    MapConfigResponse,
    NormalizedAddressSchema,
    ReverseGeocodeRequest,
    ReverseGeocodeResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/addresses", tags=["Shipping Addresses"])


@router.get(
    "/geo/config",
    response_model=MapConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public map and geocoding configuration",
)
def get_geo_config(
    current_user: User = Depends(get_current_active_user),
) -> MapConfigResponse:
    """Retrieve map tile configurations and geocoding provider status for frontend map rendering."""
    provider = get_reverse_geocoding_provider()
    has_key = provider.is_configured() if provider.provider_name() == "VIETMAP" else False
    
    # Safe public tile URL (VietMap raster/vector if configured with key, otherwise standard OpenStreetMap)
    if has_key:
        tile_url = f"{settings.VIETMAP_API_URL}/tm/{{z}}/{{x}}/{{y}}@2x.png?apikey={settings.VIETMAP_API_KEY}"
        attribution = '&copy; <a href="https://maps.vietmap.vn">VIETMAP</a>'
    else:
        tile_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

    return MapConfigResponse(
        provider=provider.provider_name(),
        is_mock=not has_key,
        has_api_key=has_key,
        default_lat=21.0285,
        default_lng=105.7896,
        tile_url=tile_url,
        attribution=attribution,
    )


@router.post(
    "/reverse-geocode",
    response_model=ReverseGeocodeResponse,
    status_code=status.HTTP_200_OK,
    summary="Reverse geocode coordinates to normalized Vietnamese address",
)
async def reverse_geocode_coordinates(
    payload: ReverseGeocodeRequest,
    current_user: User = Depends(get_current_active_user),
) -> ReverseGeocodeResponse:
    """Resolve latitude and longitude to a verified shipping address with province, district, ward, and confidence."""
    provider = get_reverse_geocoding_provider()
    try:
        normalized = await provider.reverse_geocode(payload.lat, payload.lng)
        return ReverseGeocodeResponse(
            status="success",
            provider=provider.provider_name(),
            is_mock=normalized.is_mock,
            address=NormalizedAddressSchema(**normalized.to_dict()),
        )
    except OutOfBoundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except GeocodingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except ReverseGeocodingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý vị trí: {exc}",
        )


@router.get(
    "",
    response_model=List[AddressResponse],
    status_code=status.HTTP_200_OK,
    summary="List current customer shipping addresses",
)
def list_my_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[AddressResponse]:
    """Retrieve all shipping addresses owned by the authenticated customer."""
    return UserService.list_addresses(db, current_user.id)


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shipping address",
)
def create_address(
    data: AddressCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AddressResponse:
    """Create a new address strictly bound to the authenticated user's ID."""
    return UserService.add_address(db, current_user.id, data)


@router.put(
    "/{address_id}",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
    summary="Update existing shipping address",
)
def update_address(
    address_id: int,
    data: AddressUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AddressResponse:
    """Update address fields. Returns 404 if the address belongs to another customer."""
    return UserService.update_address(db, current_user.id, address_id, data)


@router.delete(
    "/{address_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete shipping address",
)
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Remove address record. Returns 404 if the address belongs to another customer."""
    UserService.delete_address(db, current_user.id, address_id)
    return MessageResponse(message="Address deleted successfully")

