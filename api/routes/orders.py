"""
GET /api/orders/recent — recent orders for the dashboard orders table.

Response shape must match docs/data/orders.json for static fallback parity.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from api.db import query

router = APIRouter(tags=["orders"])


class Order(BaseModel):
    order_id: str
    source: str
    order_date: str
    order_status: str
    order_total_usd: float
    customer_email: str | None = None
    fulfillment_status: str | None = None


@router.get("/orders/recent", response_model=list[Order])
def get_recent_orders(
    limit: int = Query(default=25, ge=1, le=200, description="Max rows to return"),
) -> list[Order]:
    """Return the most recent POD orders across all sources."""
    rows = query(
        """
        select
            order_key,
            order_id,
            source,
            order_date::text        as order_date,
            order_status,
            order_total_usd,
            customer_email,
            fulfillment_status
        from marts.fct_orders
        order by created_at desc
        limit :limit
        """,
        {"limit": limit},
    )

    return [
        Order(
            order_id=r["order_id"],
            source=r["source"],
            order_date=r["order_date"],
            order_status=r["order_status"],
            order_total_usd=float(r["order_total_usd"] or 0),
            customer_email=r.get("customer_email"),
            fulfillment_status=r.get("fulfillment_status"),
        )
        for r in rows
    ]
