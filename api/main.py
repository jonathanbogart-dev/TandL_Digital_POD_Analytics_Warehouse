"""
FastAPI application entry point for the POD Analytics backend.

Serves three endpoints consumed by the static dashboard site:
  GET /api/kpis            → KPI summary for the Business Overview cards
  GET /api/orders/recent   → Latest N orders for the orders table
  GET /api/revenue/by-source → Aggregated revenue split by source channel
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import kpis, orders, revenue

logger = logging.getLogger(__name__)

app = FastAPI(
    title="T&L Digital POD Analytics API",
    description="Backend API for the POD Analytics Warehouse dashboard.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow the GitHub Pages site and local dev server
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:8080,http://localhost:3000,https://jonathanbogart-dev.github.io",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(kpis.router,    prefix="/api")
app.include_router(orders.router,  prefix="/api")
app.include_router(revenue.router, prefix="/api")


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}
