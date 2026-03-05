"""Shared Pydantic models used across all FinServ services."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AccountType(str, Enum):
    """Type of investment account."""
    GIA = "GIA"  # General Investment Account
    ISA = "ISA"  # Individual Savings Account
    SIPP = "SIPP"  # Self-Invested Personal Pension


class TransactionType(str, Enum):
    """Type of portfolio transaction."""
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    FEE = "FEE"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class RiskLevel(str, Enum):
    """Risk tolerance level assigned after questionnaire scoring."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class NotificationType(str, Enum):
    """Delivery channel for a notification."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class KYCStatus(str, Enum):
    """Know Your Customer verification status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(BaseModel):
    """A registered platform user."""
    id: str = Field(description="Unique user identifier", examples=["usr_001"])
    email: str = Field(description="User email address", examples=["jane.doe@example.com"])
    first_name: str = Field(description="User first name", examples=["Jane"])
    last_name: str = Field(description="User last name", examples=["Doe"])
    phone: Optional[str] = Field(default=None, description="UK phone number", examples=["+447700900123"])
    postcode: Optional[str] = Field(default=None, description="UK postcode", examples=["SW1A 1AA"])
    ni_number: Optional[str] = Field(default=None, description="National Insurance number", examples=["QQ 12 34 56 C"])
    risk_profile: Optional[str] = None  # BUG: should be RiskProfile, not str
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    notifications_enabled: bool = Field(default=True, description="Whether notifications are enabled globally")
    email_opt_in: bool = Field(default=True, description="Whether the user opted in to email notifications")
    sms_opt_in: bool = Field(default=True, description="Whether the user opted in to SMS notifications")


class RiskProfile(BaseModel):
    """Risk profile calculated from the risk questionnaire."""
    user_id: str = Field(description="ID of the user this profile belongs to", examples=["usr_001"])
    score: int = Field(ge=1, le=10, description="Risk score from 1 (conservative) to 10 (aggressive)", examples=[7])
    risk_level: RiskLevel = Field(description="Categorised risk tolerance level", examples=["moderate"])
    answers: dict = Field(description="Raw questionnaire answers keyed by question ID")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="When the profile was last calculated")
    # NOTE: old field name was 'risk_category', some services still reference it


class Holding(BaseModel):
    """A single holding within a portfolio."""
    id: str = Field(description="Unique holding identifier", examples=["hld_001"])
    portfolio_id: str = Field(description="ID of the parent portfolio", examples=["pf_001"])
    symbol: str = Field(description="Ticker symbol (LSE format)", examples=["VWRL.L"])
    name: str = Field(description="Instrument display name", examples=["Vanguard FTSE All-World UCITS ETF"])
    # BUG: should be Decimal for financial calculations
    quantity: float = Field(description="Number of units held", examples=[150.0])
    average_cost: float = Field(description="Average acquisition cost per unit in GBP", examples=[78.50])
    current_price: Optional[float] = Field(
        default=None, description="Latest market price per unit in GBP", examples=[82.30]
    )
    currency: str = Field(default="GBP", description="Currency code", examples=["GBP"])


class Portfolio(BaseModel):
    """An investment portfolio belonging to a user."""
    id: str = Field(description="Unique portfolio identifier", examples=["pf_001"])
    user_id: str = Field(description="Owner user ID", examples=["usr_001"])
    account_type: AccountType = Field(description="Type of investment account", examples=["ISA"])
    holdings: list[Holding] = Field(default=[], description="List of holdings in the portfolio")
    target_allocations: dict[str, float] = Field(
        default={}, description="Target allocation percentages keyed by symbol"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Portfolio creation timestamp")
    last_rebalanced: Optional[datetime] = Field(default=None, description="When the portfolio was last rebalanced")


class Transaction(BaseModel):
    """A portfolio transaction (buy, sell, dividend, etc.)."""
    id: str = Field(description="Unique transaction identifier", examples=["txn_001"])
    portfolio_id: str = Field(description="ID of the portfolio this transaction belongs to", examples=["pf_001"])
    symbol: str = Field(description="Ticker symbol", examples=["VWRL.L"])
    transaction_type: TransactionType = Field(description="Type of transaction", examples=["BUY"])
    quantity: float = Field(description="Number of units transacted", examples=[50.0])
    price: float = Field(description="Price per unit at execution in GBP", examples=[80.25])
    total_amount: float = Field(description="Total transaction value in GBP", examples=[4012.50])
    currency: str = Field(default="GBP", description="Currency code", examples=["GBP"])
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    settled: bool = Field(default=False, description="Whether the transaction has settled")


class ISAAccount(BaseModel):
    """Individual Savings Account details for a tax year."""
    id: str = Field(description="Unique ISA account identifier", examples=["isa_001"])
    user_id: str = Field(description="Owner user ID", examples=["usr_001"])
    tax_year: str = Field(description="UK tax year string", examples=["2024/25"])
    contributions_ytd: float = Field(
        default=0.0, description="Total contributions in the current tax year (GBP)", examples=[5000.0]
    )
    # hardcoded — should come from config
    annual_allowance: float = Field(default=20000, description="Annual ISA allowance (GBP)")
    opened_at: datetime = Field(default_factory=datetime.utcnow, description="When the ISA was opened")


class MarketPrice(BaseModel):
    """A real-time market price quote."""
    symbol: str = Field(description="Ticker symbol", examples=["VWRL.L"])
    price: float = Field(description="Current price in GBP", examples=[82.30])
    change_pct: float = Field(description="Percentage change from previous close", examples=[1.25])
    volume: int = Field(description="Trading volume", examples=[1250000])
    timestamp: datetime = Field(description="Quote timestamp")
    # BUG: missing 'currency' field — consumers assume GBP but it's not explicit


class CGTEvent(BaseModel):
    """Capital Gains Tax event for a disposal."""
    user_id: str = Field(description="ID of the user who disposed", examples=["usr_001"])
    symbol: str = Field(description="Ticker symbol of the disposed asset", examples=["VOD.L"])
    disposal_date: date = Field(description="Date the asset was sold", examples=["2024-11-15"])
    acquisition_date: date = Field(description="Date the asset was originally purchased", examples=["2023-03-10"])
    quantity: float = Field(description="Number of units disposed", examples=[500.0])
    proceeds: float = Field(description="Total disposal proceeds in GBP", examples=[2500.0])
    cost_basis: float = Field(description="Total acquisition cost in GBP", examples=[2000.0])
    gain_or_loss: float = Field(description="Capital gain (positive) or loss (negative) in GBP", examples=[500.0])


class Notification(BaseModel):
    """A notification sent to a user."""
    id: str = Field(description="Unique notification identifier", examples=["notif_001"])
    user_id: str = Field(description="Recipient user ID", examples=["usr_001"])
    notification_type: NotificationType = Field(description="Delivery channel", examples=["email"])
    subject: str = Field(description="Notification subject line", examples=["Portfolio drift alert"])
    body: str = Field(description="Notification body text", examples=["Your portfolio has drifted 5.2% from target."])
    sent_at: Optional[datetime] = Field(default=None, description="When the notification was sent")
    read: bool = Field(default=False, description="Whether the user has read this notification")
    metadata: dict = Field(default={}, description="Additional key-value metadata")


class OnboardingApplication(BaseModel):
    """A KYC onboarding application."""
    id: str = Field(description="Unique application identifier", examples=["app_001"])
    user_id: str = Field(description="Applicant user ID", examples=["usr_001"])
    first_name: str = Field(description="Applicant first name", examples=["Jane"])
    last_name: str = Field(description="Applicant last name", examples=["Doe"])
    email: str = Field(description="Applicant email address", examples=["jane.doe@example.com"])
    phone: str = Field(description="UK phone number", examples=["+447700900123"])
    postcode: str = Field(description="UK postcode", examples=["SW1A 1AA"])
    ni_number: str = Field(description="National Insurance number", examples=["QQ 12 34 56 C"])
    date_of_birth: date = Field(description="Date of birth", examples=["1990-05-15"])
    kyc_status: KYCStatus = Field(default=KYCStatus.PENDING, description="Current KYC verification status")
    identity_verified: bool = Field(default=False, description="Whether identity has been verified")
    submitted_at: datetime = Field(default_factory=datetime.utcnow, description="Application submission timestamp")
    reviewed_at: Optional[datetime] = Field(default=None, description="When the application was last reviewed")


class PortfolioDrift(BaseModel):
    """Represents the drift of a portfolio from its target allocations."""
    portfolio_id: str = Field(description="ID of the portfolio", examples=["pf_001"])
    total_drift_pct: float = Field(description="Total portfolio drift as a percentage", examples=[3.5])
    holdings_drift: dict[str, float] = Field(description="Per-holding drift percentages keyed by symbol")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="When drift was calculated")
