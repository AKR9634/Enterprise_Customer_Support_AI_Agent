"""
Customer account endpoints: view profile, saved addresses, and
account metadata (2FA, verification status). All endpoints return
data for the authenticated user only.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from app.api.auth import get_current_user
from app.api.deps import DbDep
from app.api.schemas import (
    AccountMetadataOut,
    AddressOut,
    CustomerProfileOut,
)
from app.repositories.account_metadata_repository import AccountMetadataRepository
from app.repositories.customer_address_repository import CustomerAddressRepository

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/me", response_model=CustomerProfileOut)
def get_my_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return CustomerProfileOut(**current_user)


@router.get("/me/addresses", response_model=list[AddressOut])
def get_my_addresses(
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    addresses = CustomerAddressRepository.list_by_customer(db, current_user["id"])
    return [
        AddressOut(
            id=str(a.id),
            label=a.label,
            street=a.street,
            city=a.city,
            state=a.state,
            zip=a.zip,
            country=a.country,
            is_default=a.is_default,
        )
        for a in addresses
    ]


@router.get("/me/metadata", response_model=AccountMetadataOut)
def get_my_metadata(
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    meta = AccountMetadataRepository.get_by_customer(db, current_user["id"])
    if meta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account metadata not found",
        )
    return AccountMetadataOut(
        email_verified=meta.email_verified,
        phone_verified=meta.phone_verified,
        two_factor_enabled=meta.two_factor_enabled,
        account_locked=meta.account_locked,
        last_login_at=meta.last_login_at,
    )
