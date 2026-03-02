"""Risk questionnaire definitions and scoring logic.

The questionnaire follows FCA guidelines for assessing client risk tolerance
and investment experience.
"""

from datetime import datetime
from typing import Optional


# Risk questionnaire definition
RISK_QUESTIONNAIRE = {
    "id": "risk_q_v1",
    "version": "1.0",
    "title": "Investment Risk Assessment",
    "description": "Help us understand your risk tolerance and investment goals",
    "questions": [
        {
            "id": "q1",
            "text": "What is your primary investment goal?",
            "type": "single_choice",
            "options": [
                {"value": "a", "label": "Preserve my capital with minimal risk", "score": 1},
                {"value": "b", "label": "Generate steady income with moderate growth", "score": 2},
                {"value": "c", "label": "Grow my wealth over the long term", "score": 3},
                {"value": "d", "label": "Maximise returns, accepting higher volatility", "score": 4},
            ],
        },
        {
            "id": "q2",
            "text": "How long do you plan to keep your investments before needing the money?",
            "type": "single_choice",
            "options": [
                {"value": "a", "label": "Less than 2 years", "score": 1},
                {"value": "b", "label": "2 to 5 years", "score": 2},
                {"value": "c", "label": "5 to 10 years", "score": 3},
                {"value": "d", "label": "More than 10 years", "score": 4},
            ],
        },
        {
            "id": "q3",
            "text": "If your portfolio dropped 20% in value over a month, what would you do?",
            "type": "single_choice",
            "options": [
                {"value": "a", "label": "Sell everything immediately", "score": 1},
                {"value": "b", "label": "Sell some investments to reduce risk", "score": 2},
                {"value": "c", "label": "Hold and wait for recovery", "score": 3},
                {"value": "d", "label": "Buy more while prices are low", "score": 4},
            ],
        },
        {
            "id": "q4",
            "text": "How much investment experience do you have?",
            "type": "single_choice",
            "options": [
                {"value": "a", "label": "None — this is my first time", "score": 1},
                {"value": "b", "label": "Some — I've had a Cash ISA or savings account", "score": 2},
                {"value": "c", "label": "Moderate — I've invested in funds or shares before", "score": 3},
                {"value": "d", "label": "Extensive — I actively manage my own portfolio", "score": 4},
            ],
        },
        {
            "id": "q5",
            "text": "What percentage of your total savings would this investment represent?",
            "type": "single_choice",
            "options": [
                {"value": "a", "label": "More than 75%", "score": 1},
                {"value": "b", "label": "50% to 75%", "score": 2},
                {"value": "c", "label": "25% to 50%", "score": 3},
                {"value": "d", "label": "Less than 25%", "score": 4},
            ],
        },
        {
            "id": "q6",
            "text": "How would you describe your attitude to financial risk?",
            "type": "single_choice",
            "options": [
                {"value": "a", "label": "I can't afford to lose any money", "score": 1},
                {"value": "b", "label": "I'm willing to accept small losses for better returns", "score": 2},
                {"value": "c", "label": "I understand investments can go down as well as up", "score": 3},
                {"value": "d", "label": "I'm comfortable with significant short-term losses for long-term gains", "score": 4},
            ],
        },
        {
            "id": "q7",
            "text": "Do you have an emergency fund covering at least 3 months of expenses?",
            "type": "single_choice",
            "options": [
                {"value": "a", "label": "No", "score": 1},
                {"value": "b", "label": "I have some savings but less than 3 months", "score": 2},
                {"value": "c", "label": "Yes, 3 to 6 months", "score": 3},
                {"value": "d", "label": "Yes, more than 6 months", "score": 4},
            ],
        },
    ],
}


def get_questionnaire() -> dict:
    """Return the current risk questionnaire."""
    return RISK_QUESTIONNAIRE


def calculate_risk_score(answers: dict) -> dict:
    """Calculate a risk score from questionnaire answers.

    Args:
        answers: dict mapping question_id to selected option value (e.g. {"q1": "b", "q2": "c"})

    Returns:
        dict with score (1-10), risk_level, and breakdown.

    BUG: The score calculation doesn't weight questions differently.
    In practice, questions about time horizon (q2) and emergency fund (q7)
    should carry more weight than attitude questions.
    """
    questions = RISK_QUESTIONNAIRE["questions"]
    total_score = 0
    max_score = 0
    breakdown = []

    for question in questions:
        q_id = question["id"]
        max_score += 4  # max per question

        if q_id not in answers:
            # BUG: missing answers are silently skipped instead of flagged
            # This means a partial questionnaire can still produce a score
            continue

        selected = answers[q_id]
        option = next(
            (o for o in question["options"] if o["value"] == selected),
            None,
        )

        if option:
            total_score += option["score"]
            breakdown.append({
                "question_id": q_id,
                "question": question["text"],
                "answer": option["label"],
                "score": option["score"],
            })

    # Normalize to 1-10 scale
    if max_score == 0:
        normalized_score = 1
    else:
        # BUG: using max_score (28) instead of actual answered questions' max
        # so partial questionnaires get artificially low scores
        normalized_score = round((total_score / max_score) * 10)
        normalized_score = max(1, min(10, normalized_score))

    # Determine risk level
    if normalized_score <= 3:
        risk_level = "conservative"
    elif normalized_score <= 6:
        risk_level = "moderate"
    else:
        risk_level = "aggressive"

    return {
        "score": normalized_score,
        "risk_level": risk_level,
        "total_raw_score": total_score,
        "max_possible_score": max_score,
        "questions_answered": len(breakdown),
        "total_questions": len(questions),
        "breakdown": breakdown,
    }


def get_recommended_allocation(risk_level: str) -> dict:
    """Get the recommended portfolio allocation for a risk level."""
    allocations = {
        "conservative": {
            "uk_government_bonds": 50,
            "corporate_bonds": 20,
            "uk_equities": 15,
            "global_equities": 10,
            "cash": 5,
        },
        "moderate": {
            "uk_government_bonds": 20,
            "corporate_bonds": 15,
            "uk_equities": 30,
            "global_equities": 25,
            "cash": 10,
        },
        "aggressive": {
            "uk_government_bonds": 5,
            "corporate_bonds": 5,
            "uk_equities": 35,
            "global_equities": 45,
            "cash": 10,
        },
    }

    allocation = allocations.get(risk_level)
    if not allocation:
        allocation = allocations["moderate"]

    return {
        "risk_level": risk_level,
        "allocation": allocation,
        "total_pct": sum(allocation.values()),
    }
