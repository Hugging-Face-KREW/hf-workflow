import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import experiment_budget as budget


def test_unknown_prior_cost_blocks_even_with_small_estimate(tmp_path):
    path = tmp_path / "ledger.json"
    state = budget.initialize(path, "10", [{"id": "remote-review", "status": "prior_unreconciled",
        "actual_usd": None, "estimated_usd": "0.01", "evidence": "No billing usage emitted"}])
    assert state["remaining_usd"] is None
    assert not state["paid_execution_allowed"]
    with pytest.raises(ValueError, match="prior cost unknown"):
        budget.reserve(path, "next", "0.01", "bounded request")
    assert len(json.loads(path.read_text())["entries"]) == 1


def test_parallel_reservations_cannot_exceed_shared_cap(tmp_path):
    path = tmp_path / "ledger.json"
    budget.initialize(path, "1", [])

    def attempt(i):
        try:
            budget.reserve(path, str(i), "0.2", "full attempt including retries and fees")
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=12) as pool:
        assert sum(pool.map(attempt, range(20))) == 5
    assert budget.summary(json.loads(path.read_text()))["remaining_usd"] == "0"


def test_failed_or_uncertain_attempt_retains_reservation_and_no_duplicate(tmp_path):
    path = tmp_path / "ledger.json"
    budget.initialize(path, "1", [])
    budget.reserve(path, "attempt-1", "0.9", "worst-case text-only attempt")
    with pytest.raises(ValueError, match="Duplicate"):
        budget.reserve(path, "attempt-1", "0.01", "retry")
    with pytest.raises(ValueError, match="Budget exhausted"):
        budget.reserve(path, "attempt-2", "0.2", "new attempt")


def test_settle_releases_only_with_actual_evidence_and_preserves_overrun(tmp_path):
    path = tmp_path / "ledger.json"
    budget.initialize(path, "1", [])
    budget.reserve(path, "first", "0.8", "bound")
    state = budget.settle(path, "first", "1.2", "billing usage plus fee")
    assert state["overrun"] and not state["paid_execution_allowed"]
    with pytest.raises(ValueError, match="overrun"):
        budget.reserve(path, "next", "0.01", "bound")
    with pytest.raises(ValueError, match="overwrite"):
        budget.settle(path, "first", "0", "attempt to clear")


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1", True])
def test_invalid_amounts_rejected(tmp_path, value):
    with pytest.raises(ValueError):
        budget.initialize(tmp_path / "ledger.json", value, [])


def test_reconciliation_is_required_before_resume(tmp_path):
    path = tmp_path / "ledger.json"
    budget.initialize(path, "10", [{"id": "prior", "status": "unknown", "evidence": "timeout"}])
    budget.settle(path, "prior", "2.3", "provider receipt including fees")
    state = budget.reserve(path, "new", "0.7", "all-attempt worst case")
    assert state["remaining_usd"] == "7.0"


def test_underestimated_single_attempt_stops_even_below_daily_cap(tmp_path):
    path = tmp_path / "ledger.json"
    budget.initialize(path, "10", [])
    budget.reserve(path, "first", "0.2", "assumed upper bound")
    state = budget.settle(path, "first", "0.3", "provider reported cost")
    assert state["reservation_overrun_ids"] == ["first"]
    assert not state["paid_execution_allowed"]
