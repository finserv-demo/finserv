"""Tax-loss harvesting logic for UK portfolios.

Identifies holdings with unrealised losses that could be sold to offset gains,
while respecting the UK bed-and-breakfasting rule.
"""

from datetime import date, timedelta
from typing import Optional

from services.tax.constants import BED_AND_BREAKFAST_DAYS, CGT_ANNUAL_EXEMPT_AMOUNT
from services.tax.cgt import check_bed_and_breakfast


def identify_harvesting_opportunities(
    holdings: list[dict],
    cgt_events: list[dict],
    user_id: str,
) -> list[dict]:
    """Identify holdings with unrealised losses suitable for tax-loss harvesting.

    Returns a list of suggested sell orders, sorted by loss magnitude (largest first).

    BUG: This function does NOT check the bed-and-breakfasting rule before
    suggesting a sell. If the user recently bought more of the same share
    within the last 30 days, selling now would trigger the B&B rule and the
    loss would be matched against the recent purchase cost, potentially
    eliminating the tax benefit entirely.
    """
    opportunities = []

    for holding in holdings:
        if holding.get("current_price") is None:
            continue

        current_value = holding["quantity"] * holding["current_price"]
        cost_basis = holding["quantity"] * holding["average_cost"]
        unrealised_pnl = current_value - cost_basis

        if unrealised_pnl < 0:
            # This is a loss position — potential harvesting candidate
            opportunities.append({
                "symbol": holding["symbol"],
                "name": holding.get("name", holding["symbol"]),
                "quantity": holding["quantity"],
                "current_price": holding["current_price"],
                "average_cost": holding["average_cost"],
                "current_value": round(current_value, 2),
                "cost_basis": round(cost_basis, 2),
                "unrealised_loss": round(abs(unrealised_pnl), 2),
                "loss_pct": round((unrealised_pnl / cost_basis) * 100, 2) if cost_basis != 0 else 0.0,
                # BUG: doesn't check B&B rule — should flag if user bought
                # this stock in the last 30 days
                "bed_and_breakfast_risk": False,
            })

    # Sort by largest loss first
    opportunities.sort(key=lambda x: x["unrealised_loss"], reverse=True)

    return opportunities


def calculate_harvesting_benefit(
    opportunities: list[dict],
    realised_gains_ytd: float,
    tax_rate: float = 10.0,  # BUG: defaults to basic rate — should check user's band
) -> dict:
    """Calculate the potential tax benefit from harvesting all identified opportunities.

    BUG: Uses a flat tax rate instead of checking the user's actual income tax band.
    Higher rate taxpayers pay 20% CGT, not 10%.
    """
    total_harvestable_loss = sum(o["unrealised_loss"] for o in opportunities)

    # Calculate how much of the gain is above the annual exempt amount
    taxable_gains = max(0, realised_gains_ytd - CGT_ANNUAL_EXEMPT_AMOUNT)

    # Losses can offset gains
    gains_after_harvesting = max(0, taxable_gains - total_harvestable_loss)

    tax_saved = (taxable_gains - gains_after_harvesting) * (tax_rate / 100)

    return {
        "total_harvestable_loss": round(total_harvestable_loss, 2),
        "realised_gains_ytd": round(realised_gains_ytd, 2),
        "taxable_gains_before": round(taxable_gains, 2),
        "taxable_gains_after": round(gains_after_harvesting, 2),
        "estimated_tax_saved": round(tax_saved, 2),
        "opportunities_count": len(opportunities),
        "tax_rate_used": tax_rate,
        "currency": "GBP",
    }


def create_harvesting_plan(
    holdings: list[dict],
    cgt_events: list[dict],
    user_id: str,
    target_loss: Optional[float] = None,
) -> dict:
    """Create a tax-loss harvesting plan.

    If target_loss is specified, only harvest enough to reach that amount.
    Otherwise, harvest all available losses.
    """
    opportunities = identify_harvesting_opportunities(holdings, cgt_events, user_id)

    if not opportunities:
        return {
            "user_id": user_id,
            "status": "no_opportunities",
            "message": "No holdings with unrealised losses found",
            "trades": [],
        }

    trades = []
    total_loss_harvested = 0.0

    for opp in opportunities:
        if target_loss and total_loss_harvested >= target_loss:
            break

        if target_loss:
            remaining_target = target_loss - total_loss_harvested
            if opp["unrealised_loss"] > remaining_target:
                # Partial sell — only sell enough to hit target
                # BUG: calculates partial quantity but doesn't account for
                # minimum trade sizes or lot constraints
                partial_pct = remaining_target / opp["unrealised_loss"]
                sell_quantity = opp["quantity"] * partial_pct
            else:
                sell_quantity = opp["quantity"]
        else:
            sell_quantity = opp["quantity"]

        trade = {
            "symbol": opp["symbol"],
            "action": "SELL",
            "quantity": round(sell_quantity, 4),
            "estimated_price": opp["current_price"],
            "estimated_loss": round(
                sell_quantity * (opp["average_cost"] - opp["current_price"]), 2
            ),
            "bed_and_breakfast_warning": (
                f"Do not repurchase {opp['symbol']} within {BED_AND_BREAKFAST_DAYS} days "
                "to avoid the bed-and-breakfasting rule"
            ),
        }
        trades.append(trade)
        total_loss_harvested += trade["estimated_loss"]

    return {
        "user_id": user_id,
        "status": "plan_ready",
        "trades": trades,
        "total_estimated_loss": round(total_loss_harvested, 2),
        "important_note": (
            "After executing these trades, do NOT repurchase the same shares "
            f"within {BED_AND_BREAKFAST_DAYS} days to comply with HMRC's "
            "bed-and-breakfasting rule."
        ),
    }
