"""User profile and address management service with strict tenancy isolation."""

import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserAddress
from app.repositories.user_repo import UserRepository
from app.schemas.user import (
    AddressCreateRequest,
    AddressUpdateRequest,
    UserProfileUpdateRequest,
)

logger = logging.getLogger("novelia.users")


class UserService:
    """Business operations for user profile and shipping addresses."""

    @staticmethod
    def update_profile(
        db: Session,
        user: User,
        data: UserProfileUpdateRequest,
    ) -> User:
        """Update user profile information."""
        updated_user = UserRepository.update_profile(
            db=db,
            user=user,
            full_name=data.full_name,
            phone=data.phone,
        )
        db.commit()
        db.refresh(updated_user)
        return updated_user

    @staticmethod
    def list_addresses(db: Session, user_id: int) -> List[UserAddress]:
        """List all addresses belonging strictly to authenticated user."""
        return UserRepository.get_addresses(db, user_id)

    @staticmethod
    def add_address(db: Session, user_id: int, data: AddressCreateRequest) -> UserAddress:
        """Add new shipping address for user."""
        address = UserRepository.create_address(db, user_id, data)
        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def update_address(
        db: Session,
        user_id: int,
        address_id: int,
        data: AddressUpdateRequest,
    ) -> UserAddress:
        """Update address verifying strict ownership."""
        address = UserRepository.get_address_by_id(db, address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping address not found or access denied",
            )
        updated = UserRepository.update_address(db, address, data)
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def delete_address(db: Session, user_id: int, address_id: int) -> None:
        """Delete shipping address verifying strict ownership."""
        address = UserRepository.get_address_by_id(db, address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping address not found or access denied",
            )
        UserRepository.delete_address(db, address)
        db.commit()
