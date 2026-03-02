"""UK tax constants and configuration.

NOTE: Many of these should be configurable via environment variables
or a config service, but are currently hardcoded.
"""

# ISA Annual Allowance
# BUG: hardcoded instead of configurable via env var
ISA_ANNUAL_ALLOWANCE = 20000  # £20,000 for 2024/25

# Capital Gains Tax
CGT_ANNUAL_EXEMPT_AMOUNT = 3000  # £3,000 for 2024/25 onwards (was £6,000 in 2023/24)
CGT_BASIC_RATE = 10  # % for basic rate taxpayers
CGT_HIGHER_RATE = 20  # % for higher rate taxpayers

# Bed and Breakfasting Rule
BED_AND_BREAKFAST_DAYS = 30  # 30-day rule for share repurchase

# UK Tax Year
TAX_YEAR_START_MONTH = 4  # April
TAX_YEAR_START_DAY = 6  # 6th April

# Stamp Duty Reserve Tax (on share purchases)
SDRT_RATE = 0.5  # 0.5% on most UK share purchases

# Annual Dividend Allowance
DIVIDEND_ALLOWANCE = 500  # £500 for 2024/25

# Personal Allowance
PERSONAL_ALLOWANCE = 12570  # £12,570

# Income Tax Bands
BASIC_RATE_THRESHOLD = 50270  # £50,270
HIGHER_RATE_THRESHOLD = 125140  # £125,140

# Platform fee
PLATFORM_FEE_PCT = 0.25  # 0.25% annual platform fee

# Minimum trade amount
MIN_TRADE_AMOUNT = 1.00  # £1.00 minimum

# Maximum ISA providers per tax year
MAX_ISA_PROVIDERS_PER_YEAR = 1  # can only contribute to one S&S ISA per year
