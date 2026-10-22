"""User and Address data access repository."""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.user import Role, User, UserAddress, UserRole
from app.schemas.user import AddressCreateRequest, AddressUpdateRequest


class UserRepository:
    """Encapsulates all database operations for Users, Roles, and Addresses."""

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Query user by email with eager loading of roles."""
        return (
            db.query(User)
            .options(joinedload(User.roles).joinedload(UserRole.role))
            .filter(User.email == email.strip().lower())
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Query user by ID with eager loading of roles."""
        return (
            db.query(User)
            .options(joinedload(User.roles).joinedload(UserRole.role))
            .filter(User.id == user_id)
            .first()
        )

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        hashed_password: str,
        full_name: str,
        phone: Optional[str] = None,
    ) -> User:
        """Create new user entity."""
        user = User(
            email=email.strip().lower(),
            hashed_password=hashed_password,
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            is_active=True,
        )
        db.add(user)
        db.flush()
        return user

    @staticmethod
    def assign_role(db: Session, user_id: int, role_name: str) -> None:
        """Assign an RBAC role to a user. Creates role if not found."""
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=f"Role {role_name}")
            db.add(role)
            db.flush()

        existing_user_role = (
            db.query(UserRole)
            .filter(UserRole.user_id == user_id, UserRole.role_id == role.id)
            .first()
        )
        if not existing_user_role:
            user_role = UserRole(user_id=user_id, role_id=role.id)
            db.add(user_role)
            db.flush()

    @staticmethod
    def get_user_role_names(user: User) -> List[str]:
        """Extract role names from user entity, normalizing any legacy ROLE_ prefix."""
        if not user or not user.roles:
            return ["CUSTOMER"]
        extracted = []
        for ur in user.roles:
            if ur.role and ur.role.name:
                role_name = ur.role.name
                if role_name.startswith("ROLE_"):
                    role_name = role_name[5:]
                extracted.append(role_name)
        return extracted if extracted else ["CUSTOMER"]

    @staticmethod
    def update_profile(
        db: Session,
        user: User,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> User:
        """Update mutable user profile fields."""
        if full_name is not None:
            user.full_name = full_name.strip()
        if phone is not None:
            user.phone = phone.strip() if phone else None
        db.flush()
        return user

    @staticmethod
    def update_password(db: Session, user: User, hashed_password: str) -> None:
        """Update user hashed password."""
        user.hashed_password = hashed_password
        db.flush()

    # -------------------------------------------------------------
    # Address Management (Strict Cross-Tenant Isolation)
    # -------------------------------------------------------------
    @staticmethod
    def get_addresses(db: Session, user_id: int) -> List[UserAddress]:
        """Fetch all shipping addresses owned by user."""
        return (
            db.query(UserAddress)
            .filter(UserAddress.user_id == user_id)
            .order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
            .all()
        )

    @staticmethod
    def get_address_by_id(db: Session, address_id: int, user_id: int) -> Optional[UserAddress]:
        """Fetch specific address strictly verifying owner matches user_id."""
        return (
            db.query(UserAddress)
            .filter(UserAddress.id == address_id, UserAddress.user_id == user_id)
            .first()
        )

    @staticmethod
    def create_address(db: Session, user_id: int, data: AddressCreateRequest) -> UserAddress:
        """Create new shipping address. If marked is_default, unmark previous defaults."""
        if data.is_default:
            db.query(UserAddress).filter(UserAddress.user_id == user_id).update({"is_default": False})

        # If user has no existing addresses, force first address to be default
        existing_count = db.query(UserAddress).filter(UserAddress.user_id == user_id).count()
        is_default = data.is_default or (existing_count == 0)

        address = UserAddress(
            user_id=user_id,
            recipient_name=data.recipient_name.strip(),
            phone=data.phone.strip(),
            province_code=data.province_code.strip(),
            province_name=data.province_name.strip(),
            district_code=data.district_code.strip(),
            district_name=data.district_name.strip(),
            ward_code=data.ward_code.strip(),
            ward_name=data.ward_name.strip(),
            street_address=data.street_address.strip(),
            formatted_address=data.formatted_address.strip() if data.formatted_address else None,
            latitude=data.latitude,
            longitude=data.longitude,
            place_id=data.place_id.strip() if data.place_id else None,
            source_provider=data.source_provider.strip() if data.source_provider else None,
            confidence=data.confidence,
            is_default=is_default,
        )
        db.add(address)
        db.flush()
        return address

    @staticmethod
    def update_address(
        db: Session,
        address: UserAddress,
        data: AddressUpdateRequest,
    ) -> UserAddress:
        """Update address fields."""
        if data.is_default:
            db.query(UserAddress).filter(UserAddress.user_id == address.user_id).update({"is_default": False})
            address.is_default = True
        elif data.is_default is False:
            address.is_default = False

        if data.recipient_name is not None:
            address.recipient_name = data.recipient_name.strip()
        if data.phone is not None:
            address.phone = data.phone.strip()
        if data.province_code is not None:
            address.province_code = data.province_code.strip()
        if data.province_name is not None:
            address.province_name = data.province_name.strip()
        if data.district_code is not None:
            address.district_code = data.district_code.strip()
        if data.district_name is not None:
            address.district_name = data.district_name.strip()
        if data.ward_code is not None:
            address.ward_code = data.ward_code.strip()
        if data.ward_name is not None:
            address.ward_name = data.ward_name.strip()
        if data.street_address is not None:
            address.street_address = data.street_address.strip()
        if data.formatted_address is not None:
            address.formatted_address = data.formatted_address.strip() if data.formatted_address else None
        if data.latitude is not None:
            address.latitude = data.latitude
        if data.longitude is not None:
            address.longitude = data.longitude
        if data.place_id is not None:
            address.place_id = data.place_id.strip() if data.place_id else None
        if data.source_provider is not None:
            address.source_provider = data.source_provider.strip() if data.source_provider else None
        if data.confidence is not None:
            address.confidence = data.confidence

        db.flush()
        return address

    @staticmethod
    def delete_address(db: Session, address: UserAddress) -> None:
        """Delete shipping address."""
        db.delete(address)
        db.flush()
