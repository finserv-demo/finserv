# FinServ

**FinServ** is a UK-based robo-advisor platform — think Wealthfront, but for the UK market. We handle ISA management, portfolio rebalancing, tax-loss harvesting (with proper bed-and-breakfasting compliance), and automated risk profiling.

## Architecture

This is a Python + TypeScript monorepo:

- **`services/portfolio/`** — FastAPI service handling portfolio management, rebalancing, and holdings
- **`services/tax/`** — UK tax calculations: ISA allowances, CGT, bed-and-breakfasting rule
- **`services/risk-engine/`** — Risk profiling questionnaires and scoring
- **`services/market-data/`** — Market price feeds, caching, and retries
- **`services/onboarding/`** — KYC, identity verification, NI number and postcode validation
- **`services/notifications/`** — Email/SMS triggers and threshold alerts
- **`web/`** — React + Vite dashboard
- **`shared/`** — Shared Pydantic models, TypeScript interfaces, and auth utilities

## Quick Start

### Backend Services

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Run individual services
cd services/portfolio && uvicorn main:app --reload --port 8000
cd services/tax && uvicorn main:app --reload --port 8001
cd services/risk-engine && uvicorn main:app --reload --port 8002
cd services/market-data && uvicorn main:app --reload --port 8003
cd services/onboarding && uvicorn main:app --reload --port 8004
cd services/notifications && uvicorn main:app --reload --port 8005
```

### Frontend

```bash
cd web
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

## UK Domain Notes

- Tax year runs **April 6 → April 5** (not calendar year)
- ISA annual allowance: **£20,000**
- CGT annual exempt amount: **£3,000** (2024/25 onwards)
- Bed-and-breakfasting rule: 30-day share repurchase restriction
- All amounts in **GBP (£)**
- Dates displayed in **BST/GMT** (not UTC)

## Running Tests

```bash
# Python tests
pytest services/

# Frontend tests
cd web && npm test
```

## Team

Built by the FinServ engineering team in London.
