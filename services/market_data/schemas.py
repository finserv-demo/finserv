"""Pydantic schemas for market data API responses.

BUG: The PriceResponse schema is missing the 'currency' field.
Consumers of this API assume all prices are in GBP, but the schema
doesn't enforce or communicate this.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PriceResponse(BaseModel):
    """Response schema for a single price quote.

    BUG: Missing 'currency' field — consumers have to assume GBP.
    """
    symbol: str
    price: float
    change_pct: float
    volume: int
    timestamp: str
    # BUG: should include: currency: str = "GBP"


class PricesResponse(BaseModel):
    """Response schema for multiple price quotes."""
    prices: list[PriceResponse]
    count: int


class HistoricalPricePoint(BaseModel):
    symbol: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoricalPricesResponse(BaseModel):
    symbol: str
    interval: str
    data: list[HistoricalPricePoint]
    count: int


class SymbolInfo(BaseModel):
    symbol: str
    base_price: float
    exchange: str
    currency: str
