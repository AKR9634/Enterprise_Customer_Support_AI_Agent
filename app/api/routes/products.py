"""
Product catalog endpoints: list/search products, view detailed specs,
warranty info, and inventory status. Open to all authenticated users
(customer and agent roles).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from app.api.auth import get_current_user
from app.api.deps import DbDep
from app.api.schemas import (
    InventoryOut,
    ProductDetailOut,
    ProductSpecOut,
    ProductWarrantyOut,
)
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.product_specification_repository import ProductSpecificationRepository
from app.repositories.product_warranty_repository import ProductWarrantyRepository

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductDetailOut])
def list_products(
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
    query: str = "",
):
    products = ProductRepository.list_all(db)
    if query:
        q = query.lower()
        products = [p for p in products if q in p.name.lower() or q in p.description.lower()]

    result = []
    for p in products:
        specs = ProductSpecificationRepository.list_by_product(db, str(p.id))
        warranty = ProductWarrantyRepository.get_by_product(db, str(p.id))
        inventory = InventoryRepository.get_by_product(db, str(p.id))
        result.append(_product_to_detail(p, specs, warranty, inventory))
    return result


@router.get("/{product_id}", response_model=ProductDetailOut)
def get_product(
    product_id: str,
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    product = ProductRepository.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    specs = ProductSpecificationRepository.list_by_product(db, product_id)
    warranty = ProductWarrantyRepository.get_by_product(db, product_id)
    inventory = InventoryRepository.get_by_product(db, product_id)
    return _product_to_detail(product, specs, warranty, inventory)


@router.get("/{product_id}/specs", response_model=list[ProductSpecOut])
def get_product_specs(
    product_id: str,
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    product = ProductRepository.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    specs = ProductSpecificationRepository.list_by_product(db, product_id)
    return [ProductSpecOut(key=s.key, value=s.value) for s in specs]


@router.get("/{product_id}/warranty", response_model=ProductWarrantyOut)
def get_product_warranty(
    product_id: str,
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    product = ProductRepository.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    warranty = ProductWarrantyRepository.get_by_product(db, product_id)
    if warranty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warranty info not found for this product",
        )
    return ProductWarrantyOut(
        duration_months=warranty.duration_months,
        terms=warranty.terms,
    )


@router.get("/{product_id}/inventory", response_model=InventoryOut)
def get_product_inventory(
    product_id: str,
    db: DbDep,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    product = ProductRepository.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    inv = InventoryRepository.get_by_product(db, product_id)
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory info not found for this product",
        )
    return InventoryOut(
        stock_count=inv.stock_count,
        low_stock=inv.low_stock,
    )


# ── Helpers ──────────────────────────────────────────────────────────────


def _product_to_detail(product, specs, warranty, inventory) -> ProductDetailOut:
    return ProductDetailOut(
        id=str(product.id),
        name=product.name,
        description=product.description,
        price=product.price,
        sku=product.sku,
        specifications=[ProductSpecOut(key=s.key, value=s.value) for s in specs],
        warranty=ProductWarrantyOut(
            duration_months=warranty.duration_months,
            terms=warranty.terms,
        ) if warranty else None,
        inventory=InventoryOut(
            stock_count=inventory.stock_count,
            low_stock=inventory.low_stock,
        ) if inventory else None,
    )
