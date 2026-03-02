"""Custom error classes for the portfolio service."""


class PortfolioError(Exception):
    """Base error for portfolio operations."""
    pass


class InsufficientFundsError(PortfolioError):
    """Raised when a user doesn't have enough funds for a transaction."""
    # BUG: typo in the default message
    def __init__(self, message: str = "Insufficent funds for this transaction"):
        self.message = message
        super().__init__(self.message)


class PortfolioNotFoundError(PortfolioError):
    """Raised when a portfolio is not found."""
    def __init__(self, portfolio_id: str):
        self.message = f"Portfolio {portfolio_id} not found"
        super().__init__(self.message)


class InvalidAllocationError(PortfolioError):
    """Raised when target allocations don't sum to 100%."""
    def __init__(self, total: float):
        self.message = f"Target allocations must sum to 100%, got {total}%"
        super().__init__(self.message)


class RebalanceError(PortfolioError):
    """Raised when rebalancing fails."""
    def __init__(self, reason: str):
        self.message = f"Rebalance failed: {reason}"
        super().__init__(self.message)


class HoldingNotFoundError(PortfolioError):
    """Raised when a holding is not found in the portfolio."""
    def __init__(self, symbol: str, portfolio_id: str):
        self.message = f"Holding {symbol} not found in portfolio {portfolio_id}"
        super().__init__(self.message)


class MarketDataUnavailableError(PortfolioError):
    """Raised when market data cannot be fetched."""
    def __init__(self, symbol: str):
        self.message = f"Market data unavailable for {symbol}"
        super().__init__(self.message)
