"""Pydantic schemas for market data API responses.

BUG: The PriceResponse schema is missing the 'currency' field.
Consumers of this API assume all prices are in GBP, but the schema
doesn't enforce or communicate this.
"""


from pydantic import BaseModel, Field


class PriceResponse(BaseModel):
    """Response schema for a single price quote.

    BUG: Missing 'currency' field — consumers have to assume GBP.
    """
    symbol: str = Field(description="Ticker symbol", examples=["VWRL.L"])
    price: float = Field(description="Current price in GBP", examples=[82.30])
    change_pct: float = Field(description="Percentage change from previous close", examples=[1.25])
    volume: int = Field(description="Trading volume", examples=[1250000])
    timestamp: str = Field(description="ISO-8601 quote timestamp", examples=["2024-11-15T14:30:00"])
    # BUG: should include: currency: str = "GBP"


class PricesResponse(BaseModel):
    """Response schema for multiple price quotes."""
    prices: list[PriceResponse] = Field(description="List of price quotes")
    count: int = Field(description="Number of prices returned", examples=[5])


class HistoricalPricePoint(BaseModel):
    """A single OHLCV data point for historical price data."""
    symbol: str = Field(description="Ticker symbol", examples=["VWRL.L"])
    date: str = Field(description="Date of the data point", examples=["2024-11-15"])
    open: float = Field(description="Opening price in GBP", examples=[81.00])
    high: float = Field(description="Highest price in GBP", examples=[83.50])
    low: float = Field(description="Lowest price in GBP", examples=[80.50])
    close: float = Field(description="Closing price in GBP", examples=[82.30])
    volume: int = Field(description="Trading volume", examples=[1250000])


class HistoricalPricesResponse(BaseModel):
    """Response schema for historical price data."""
    symbol: str = Field(description="Ticker symbol", examples=["VWRL.L"])
    interval: str = Field(description="Data interval", examples=["daily"])
    data: list[HistoricalPricePoint] = Field(description="List of OHLCV data points")
    count: int = Field(description="Number of data points returned", examples=[30])


class SymbolInfo(BaseModel):
    """Information about a tradeable symbol."""
    symbol: str = Field(description="Ticker symbol", examples=["VWRL.L"])
    base_price: float = Field(description="Base reference price in local currency", examples=[82.30])
    exchange: str = Field(description="Exchange the symbol trades on", examples=["LSE"])
    currency: str = Field(description="Currency code", examples=["GBP"])
