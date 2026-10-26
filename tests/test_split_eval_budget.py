import json
from decimal import Decimal

import pytest
from split_eval_v4 import (
    BudgetLedger,
    EvaluationStop,
    citation_diagnostic,
    restore_auth_attempt,
)


def policy():
    return {
        "max_usd": 1,
        "max_api_attempts": 3,
        "max_prompt_utf8_bytes": 32000,
        "input_token_safety_overhead": 1024,
        "max_output_tokens": 800,
        "rate_input_usd_per_million": 0.15,
        "rate_output_usd_per_million": 0.6,
    }


def test_stop_before_unaffordable_or_excess_attempt():
    p = policy()
    p["max_usd"] = 0.00001
    ledger = BudgetLedger(p)
    with pytest.raises(EvaluationStop, match="before API"):
        ledger.reserve("hello")
    assert ledger.attempts == []
    p["max_usd"] = 1
    p["max_api_attempts"] = 1
    ledger.reserve("hello")
    with pytest.raises(EvaluationStop, match="attempt cap"):
        ledger.reserve("next")


def test_unknown_usage_keeps_persisted_worst_case(tmp_path):
    ledger = BudgetLedger(policy(), tmp_path / "ledger.json")
    ledger.reserve("한글")
    saved = json.loads(ledger.path.read_text())
    assert saved["attempts"][0]["state"] == "reserved"
    assert saved["attempts"][0]["input_token_upper_bound"] == 1030
    assert ledger.charged == Decimal(saved["charged_upper_estimate_usd"])
    assert ledger.charged > 0


def test_usage_discount_only_after_verified_response():
    ledger = BudgetLedger(policy())
    i = ledger.reserve("hello")
    reserved = ledger.charged
    ledger.settle(i, 30, 10, "gpt-4o-mini-2024-07-18")
    assert ledger.charged == Decimal("0.0000105") < reserved
    with pytest.raises(EvaluationStop, match="already settled"):
        ledger.settle(i, 30, 10, "gpt-4o-mini-2024-07-18")


def test_out_of_bounds_usage_and_large_nontext_inputs_are_rejected():
    ledger = BudgetLedger(policy())
    i = ledger.reserve("hello")
    with pytest.raises(EvaluationStop, match="reserved bounds"):
        ledger.settle(i, 50, 801, "gpt-4o-mini")
    assert ledger.attempts[i]["state"] == "reserved"
    with pytest.raises(EvaluationStop, match="byte cap"):
        ledger.reserve("가" * 11000)
    with pytest.raises(EvaluationStop, match="nontext"):
        ledger.reserve([{"type": "image_url"}])


def previous_auth_failure():
    ledger = BudgetLedger(policy())
    i = ledger.reserve("hello")
    ledger.attempts[i]["state"] = "usage_unknown"
    return {
        "completion": "stopped",
        "stop_reason": "Provider failure: AuthenticationError",
        "rows": [],
        "freeze_commit": "frozen",
        "dataset_sha256": "sha",
        "commits": {},
        "protocol": {"budget": policy()},
        "budget": ledger.report(),
    }


def test_auth_resume_carries_unknown_cost_instead_of_resetting_budget():
    previous = previous_auth_failure()
    ledger = BudgetLedger(policy())
    restore_auth_attempt(previous, ledger, "frozen", "sha", {})
    old = ledger.charged
    ledger.reserve("new request")
    assert ledger.charged > old > 0
    assert len(ledger.attempts) == 2


def test_resume_rejects_replaying_answers_or_discarding_cost():
    previous = previous_auth_failure()
    previous["rows"] = [{"id": "already answered"}]
    with pytest.raises(ValueError, match="zero-answer"):
        restore_auth_attempt(previous, BudgetLedger(policy()), "frozen", "sha", {})
    previous["rows"] = []
    previous["budget"]["charged_upper_estimate_usd"] = "0"
    with pytest.raises(ValueError, match="budget accounting"):
        restore_auth_attempt(previous, BudgetLedger(policy()), "frozen", "sha", {})


@pytest.mark.parametrize(
    "text,sources,expected",
    [
        ("shown [1]", ["a", "b"], False),  # Citation2 cut off, source2 remains.
        ("shown [2]", ["b"], True),
        ("invalid [4]", ["a"], False),
        ("no evidence", [], True),
    ],
)
def test_visible_citations_must_match_final_sources(text, sources, expected):
    response = {
        "assistant_message": text,
        "status": "answered" if sources else "cannot_answer",
        "sources": [{"document_id": x} for x in sources],
    }
    assert (
        citation_diagnostic(response, ["a", "b"])["visible_citations_match_sources"]
        is expected
    )
