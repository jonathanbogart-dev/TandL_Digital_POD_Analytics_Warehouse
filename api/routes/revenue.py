"""
GET /api/revenue/by-source — revenue aggregated by source channel.

Response shape must match docs/data/revenue.json for static fallback parity.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from api.db import query

router = APIRouter(tags=["revenue"])


class RevenueBySource(BaseModel):
    source: str
    gross_revenue_usd: float
    refunds_usd: float
    net_revenue_usd: float


@router.get("/revenue/by-source", response_model=list[RevenueBySource])
def get_revenue_by_source(
    period: str = Query(
        default="mtd",
        pattern="^(mtd|ytd|last_30|last_90|all)$",
        description="Time window: mtd, ytd, last_30, last_90, or all",
    ),
) -> list[RevenueBySource]:
    """Return net revenue aggregated by source for the requested period."""
    period_filter = {
        "mtd":    "revenue_date >= date_trunc('month', current_date)",
        "ytd":    "revenue_date >= date_trunc('year',  current_date)",
        "last_30": "revenue_date >= current_date - interval '30 days'",
        "last_90": "revenue_date >= current_date - interval '90 days'",
        "all":    "1=1",
    }[period]

    rows = query(
        f"""
        select
            source,
            coalesce(sum(gross_revenue_usd), 0) as gross_revenue_usd,
            coalesce(sum(refunds_usd), 0)       as refunds_usd,
            coalesce(sum(net_revenue_usd), 0)   as net_revenue_usd
        from marts.fct_revenue
        where {period_filter}
        group by source
        order by net_revenue_usd desc
        """
    )

    return [
        RevenueBySource(
            source=r["source"],
            gross_revenue_usd=float(r["gross_revenue_usd"]),
            refunds_usd=float(r["refunds_usd"]),
            net_revenue_usd=float(r["net_revenue_usd"]),
        )
        for r in rows
    ]
