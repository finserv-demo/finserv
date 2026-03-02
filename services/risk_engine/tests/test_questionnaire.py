"""Tests for risk questionnaire and scoring."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services.risk_engine.questionnaire import (
    calculate_risk_score,
    get_questionnaire,
    get_recommended_allocation,
)


class TestQuestionnaire:
    def test_questionnaire_has_questions(self):
        q = get_questionnaire()
        assert len(q["questions"]) == 7

    def test_all_questions_have_options(self):
        q = get_questionnaire()
        for question in q["questions"]:
            assert len(question["options"]) == 4
            assert question["type"] == "single_choice"


class TestRiskScoring:
    def test_conservative_score(self):
        answers = {f"q{i}": "a" for i in range(1, 8)}
        result = calculate_risk_score(answers)
        assert result["risk_level"] == "conservative"
        assert result["score"] <= 3

    def test_aggressive_score(self):
        answers = {f"q{i}": "d" for i in range(1, 8)}
        result = calculate_risk_score(answers)
        assert result["risk_level"] == "aggressive"
        assert result["score"] >= 7

    def test_moderate_score(self):
        answers = {f"q{i}": "b" for i in range(1, 8)}
        result = calculate_risk_score(answers)
        assert result["risk_level"] in ("conservative", "moderate")

    def test_partial_answers(self):
        """Tests the bug: partial answers still produce a score."""
        answers = {"q1": "c", "q2": "c"}
        result = calculate_risk_score(answers)
        assert result["questions_answered"] == 2
        assert result["total_questions"] == 7

    def test_empty_answers(self):
        result = calculate_risk_score({})
        assert result["score"] == 1
        assert result["questions_answered"] == 0


class TestRecommendedAllocation:
    def test_conservative_allocation(self):
        alloc = get_recommended_allocation("conservative")
        assert alloc["allocation"]["uk_government_bonds"] == 50
        assert alloc["total_pct"] == 100

    def test_aggressive_allocation(self):
        alloc = get_recommended_allocation("aggressive")
        assert alloc["allocation"]["global_equities"] == 45
        assert alloc["total_pct"] == 100

    def test_unknown_level_defaults_to_moderate(self):
        alloc = get_recommended_allocation("unknown")
        assert alloc["risk_level"] == "unknown"
        assert alloc["total_pct"] == 100
