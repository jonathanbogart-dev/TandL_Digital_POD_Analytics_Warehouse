"""
GET /api/kpis — KPI summary consumed by the dashboard Business Overview cards.

Response shape must match docs/data/kpis.json for the static fallback to work.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from api.db import query

router = APIRouter(tags=["kpis"])


class KPIResponse(BaseModel):
    total_orders: int
    total_revenue_usd: float
    fulfillment_rate_pct: float
    avg_order_value_usd: float
    orders_mtd: int
    revenue_mtd_usd: float


@router.get("/kpis", response_model=KPIResponse)
def get_kpis() -> KPIResponse:
    """Return top-level KPI metrics for the dashboard overview cards."""
    rows = query(
        """
        select
            count(*)                                                    as total_orders,
            coalesce(sum(order_total_usd), 0)                          as total_revenue_usd,
            round(
                100.0 * count(*) filter (where order_status = 'fulfilled')
                / nullif(count(*), 0),
                1
            )                                                           as fulfillment_rate_pct,
            coalesce(avg(order_total_usd), 0)                          as avg_order_value_usd,
            count(*) filter (
                where order_date >= date_trunc('month', current_date)
            )                                                           as orders_mtd,
            coalesce(sum(order_total_usd) filter (
                where order_date >= date_trunc('month', current_date)
            ), 0)                                                       as revenue_mtd_usd
        from marts.fct_orders
        """
    )

    row = rows[0] if rows else {}
    return KPIResponse(
        total_orders=int(row.get("total_orders") or 0),
        total_revenue_usd=float(row.get("total_revenue_usd") or 0),
        fulfillment_rate_pct=float(row.get("fulfillment_rate_pct") or 0),
        avg_order_value_usd=float(row.get("avg_order_value_usd") or 0),
        orders_mtd=int(row.get("orders_mtd") or 0),
        revenue_mtd_usd=float(row.get("revenue_mtd_usd") or 0),
    )
