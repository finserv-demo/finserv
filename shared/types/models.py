"""Shared Pydantic models used across all FinServe services."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AccountType(str, Enum):
    GIA = "GIA"  # General Investment Account
    ISA = "ISA"  # Individual Savings Account
    SIPP = "SIPP"  # Self-Invested Personal Pension


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    FEE = "FEE"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class KYCStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    postcode: Optional[str] = None
    ni_number: Optional[str] = None
    risk_profile: Optional[str] = None  # BUG: should be RiskProfile, not str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notifications_enabled: bool = True
    email_opt_in: bool = True
    sms_opt_in: bool = True


class RiskProfile(BaseModel):
    user_id: str
    score: int = Field(ge=1, le=10)
    risk_level: RiskLevel
    answers: dict  # questionnaire answers
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    # NOTE: old field name was 'risk_category', some services still reference it


class Holding(BaseModel):
    id: str
    portfolio_id: str
    symbol: str
    name: str
    quantity: float  # BUG: should be Decimal for financial calculations
    average_cost: float
    current_price: Optional[float] = None
    currency: str = "GBP"


class Portfolio(BaseModel):
    id: str
    user_id: str
    account_type: AccountType
    holdings: list[Holding] = []
    target_allocations: dict[str, float] = {}  # symbol -> target %
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_rebalanced: Optional[datetime] = None


class Transaction(BaseModel):
    id: str
    portfolio_id: str
    symbol: str
    transaction_type: TransactionType
    quantity: float
    price: float
    total_amount: float
    currency: str = "GBP"
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    settled: bool = False


class ISAAccount(BaseModel):
    id: str
    user_id: str
    tax_year: str  # e.g. "2024/25"
    contributions_ytd: float = 0.0
    annual_allowance: float = 20000  # hardcoded — should come from config
    opened_at: datetime = Field(default_factory=datetime.utcnow)


class MarketPrice(BaseModel):
    symbol: str
    price: float
    change_pct: float
    volume: int
    timestamp: datetime
    # BUG: missing 'currency' field — consumers assume GBP but it's not explicit


class CGTEvent(BaseModel):
    """Capital Gains Tax event for a disposal."""
    user_id: str
    symbol: str
    disposal_date: date
    acquisition_date: date
    quantity: float
    proceeds: float
    cost_basis: float
    gain_or_loss: float  # positive = gain, negative = loss


class Notification(BaseModel):
    id: str
    user_id: str
    notification_type: NotificationType
    subject: str
    body: str
    sent_at: Optional[datetime] = None
    read: bool = False
    metadata: dict = {}


class OnboardingApplication(BaseModel):
    id: str
    user_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    postcode: str
    ni_number: str
    date_of_birth: date
    kyc_status: KYCStatus = KYCStatus.PENDING
    identity_verified: bool = False
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None


class PortfolioDrift(BaseModel):
    """Represents the drift of a portfolio from its target allocations."""
    portfolio_id: str
    total_drift_pct: float
    holdings_drift: dict[str, float]  # symbol -> drift %
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
