"""Address normalization service for Vietnamese administrative hierarchies."""

import re
from typing import Dict, Optional, Tuple
from app.integrations.geo.base import NormalizedAddress


# Standard Top Province Mappings (Code and Standard Names)
PROVINCE_REGISTRY: Dict[str, Tuple[str, str]] = {
    "ha noi": ("01", "Hà Nội"),
    "hanoi": ("01", "Hà Nội"),
    "ho chi minh": ("79", "TP. Hồ Chí Minh"),
    "tp ho chi minh": ("79", "TP. Hồ Chí Minh"),
    "tp. ho chi minh": ("79", "TP. Hồ Chí Minh"),
    "sai gon": ("79", "TP. Hồ Chí Minh"),
    "da nang": ("48", "Đà Nẵng"),
    "hai phong": ("31", "Hải Phòng"),
    "can tho": ("92", "Cần Thơ"),
    "binh duong": ("74", "Bình Dương"),
    "dong nai": ("75", "Đồng Nai"),
    "khanh hoa": ("56", "Khánh Hòa"),
    "thua thien hue": ("46", "Thừa Thiên Huế"),
    "quang ninh": ("22", "Quảng Ninh"),
}


class AddressNormalizationService:
    """Provides parsing, deduplication, administrative code mapping, and confidence assessment."""

    @staticmethod
    def strip_accents_simple(text: str) -> str:
        """Helper to lowercase and normalize standard search tokens."""
        text = text.lower().strip()
        trans = str.maketrans(
            "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ",
            "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"
        )
        return text.translate(trans)

    @classmethod
    def resolve_province_code(cls, province_name: str) -> Tuple[str, str]:
        """Map raw province name to standard administrative code and display name."""
        key = cls.strip_accents_simple(province_name)
        key = re.sub(r"^(thanh pho|tp\.|tp|tinh)\s+", "", key).strip()
        if key in PROVINCE_REGISTRY:
            return PROVINCE_REGISTRY[key]
        return ("00", province_name)

    @classmethod
    def calculate_confidence(cls, street_address: str, ward_name: str, district_name: str) -> Tuple[float, str]:
        """Assess the accuracy score and granular resolution level of the address."""
        if not street_address or street_address.strip() == "":
            if ward_name:
                return (0.70, "ward")
            if district_name:
                return (0.50, "district")
            return (0.30, "province")

        # Check for house number indicators (e.g. 'Số 12', '12/4', 'Ngõ 158', 'Hẻm')
        has_number = bool(re.search(r"(\bso\s+\d+|\b\d+[a-zA-Z]?(\/\d+)*|\bngo\s+\d+|\bhem\s+\d+)", cls.strip_accents_simple(street_address)))
        if has_number:
            return (0.95, "house_number")
        return (0.85, "street")

    @classmethod
    def assemble_formatted_address(
        cls,
        street_address: str,
        ward_name: str,
        district_name: str,
        province_name: str,
    ) -> str:
        """Compose human-readable single-line full address without redundancy."""
        components = []
        clean_street = street_address.strip() if street_address else ""
        if clean_street:
            components.append(clean_street)

        if ward_name and ward_name.strip():
            w = ward_name.strip()
            display_ward = w if w.startswith(("Phường", "Xã", "Thị trấn", "TT.")) else f"Phường {w}"
            if display_ward.lower() not in clean_street.lower():
                components.append(display_ward)

        if district_name and district_name.strip():
            d = district_name.strip()
            display_district = d if d.startswith(("Quận", "Huyện", "Thị xã", "TP.", "Thành phố")) else f"Quận {d}"
            if display_district.lower() not in clean_street.lower():
                components.append(display_district)

        if province_name and province_name.strip():
            p = province_name.strip()
            display_province = p if p.startswith(("Tỉnh", "Thành phố", "TP.")) else p
            if display_province.lower() not in clean_street.lower():
                components.append(display_province)

        return ", ".join(components)
