from __future__ import annotations

from typing import Any

from psycopg import Connection

from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.product_specification_repository import ProductSpecificationRepository
from app.repositories.product_warranty_repository import ProductWarrantyRepository


class ProductService:

    @staticmethod
    def search_products(conn: Connection, query: str) -> list[dict[str, Any]]:
        all_products = ProductRepository.list_all(conn)
        if not query.strip():
            results = all_products
        else:
            query_lower = query.lower()
            results = [
                p for p in all_products
                if query_lower in p.name.lower()
                or query_lower in p.description.lower()
            ]

        return [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "price": str(p.price),
                "sku": p.sku,
            }
            for p in results
        ]

    @staticmethod
    def get_product_specs(conn: Connection, product_id: str) -> list[dict[str, Any]]:
        specs = ProductSpecificationRepository.list_by_product(conn, product_id)
        return [
            {
                "key": s.key,
                "value": s.value,
            }
            for s in specs
        ]

    @staticmethod
    def get_product_warranty(conn: Connection, product_id: str) -> dict[str, Any]:
        warranty = ProductWarrantyRepository.get_by_product(conn, product_id)
        if warranty is None:
            return {}
        return {
            "duration_months": warranty.duration_months,
            "terms": warranty.terms,
        }

    @staticmethod
    def get_inventory_status(conn: Connection, product_id: str) -> dict[str, Any]:
        inv = InventoryRepository.get_by_product(conn, product_id)
        if inv is None:
            return {}
        return {
            "stock_count": inv.stock_count,
            "low_stock": inv.low_stock,
        }
