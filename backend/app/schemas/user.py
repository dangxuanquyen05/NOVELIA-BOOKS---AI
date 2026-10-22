"""User profile and shipping address schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    """User account details returned to client."""

    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    roles: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdateRequest(BaseModel):
    """Update profile attributes."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)


class AddressCreateRequest(BaseModel):
    """Shipping address creation payload."""

    recipient_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=8, max_length=20)
    province_code: str = Field(..., min_length=1, max_length=50)
    province_name: str = Field(..., min_length=1, max_length=100)
    district_code: str = Field(..., min_length=1, max_length=50)
    district_name: str = Field(..., min_length=1, max_length=100)
    ward_code: str = Field(..., min_length=1, max_length=50)
    ward_name: str = Field(..., min_length=1, max_length=100)
    street_address: str = Field(..., min_length=3, max_length=255)
    formatted_address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = Field(None, max_length=100)
    source_provider: Optional[str] = Field(None, max_length=50)
    confidence: Optional[float] = None
    is_default: bool = False


class AddressUpdateRequest(BaseModel):
    """Shipping address update payload."""

    recipient_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=8, max_length=20)
    province_code: Optional[str] = Field(None, max_length=50)
    province_name: Optional[str] = Field(None, max_length=100)
    district_code: Optional[str] = Field(None, max_length=50)
    district_name: Optional[str] = Field(None, max_length=100)
    ward_code: Optional[str] = Field(None, max_length=50)
    ward_name: Optional[str] = Field(None, max_length=100)
    street_address: Optional[str] = Field(None, min_length=3, max_length=255)
    formatted_address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = Field(None, max_length=100)
    source_provider: Optional[str] = Field(None, max_length=50)
    confidence: Optional[float] = None
    is_default: Optional[bool] = None


class AddressResponse(BaseModel):
    """Shipping address response."""

    id: int
    user_id: int
    recipient_name: str
    phone: str
    province_code: str
    province_name: str
    district_code: str
    district_name: str
    ward_code: str
    ward_name: str
    street_address: str
    formatted_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    source_provider: Optional[str] = None
    confidence: Optional[float] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReverseGeocodeRequest(BaseModel):
    """Reverse geocode request payload."""

    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude")


class NormalizedAddressSchema(BaseModel):
    """Normalized Vietnamese address payload."""

    province_name: str
    province_code: str
    district_name: str
    district_code: str
    ward_name: str
    ward_code: str
    street_address: str
    formatted_address: str
    latitude: float
    longitude: float
    place_id: Optional[str] = None
    confidence: float
    level: str
    source_provider: str
    is_mock: bool


class ReverseGeocodeResponse(BaseModel):
    """Reverse geocoding response payload."""

    status: str = "success"
    provider: str
    is_mock: bool
    address: NormalizedAddressSchema


class MapConfigResponse(BaseModel):
    """Map display and tile provider metadata for frontend rendering."""

    provider: str
    is_mock: bool
    has_api_key: bool
    default_lat: float = 21.0285
    default_lng: float = 105.7896
    tile_url: str
    attribution: str

