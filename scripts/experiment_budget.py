"""Offline, locked experiment budget ledger. Never performs or retries API calls.

All workers must use the SAME local ledger before each billable attempt. This is
not a distributed lock and must not be copied between GitHub Actions runners.
Unreconciled prior cost blocks reservations, even if an estimate is available.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import fcntl
import json
import os
from pathlib import Path
import tempfile


def money(value) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("Money cannot be boolean")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid USD amount") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("USD must be finite and nonnegative")
    return result


def summary(data: dict) -> dict:
    cap = money(data["limit_usd"])
    committed = Decimal(0)
    unknown = []
    bound_overruns = []
    for entry in data["entries"]:
        actual, bound = entry.get("actual_usd"), entry.get("worst_case_usd")
        if actual is None and entry["status"] != "reserved":
            unknown.append(entry["id"])
        if actual is None and bound is None:
            unknown.append(entry["id"])
        if actual is not None and bound is not None and money(actual) > money(bound):
            bound_overruns.append(entry["id"])
        # An overrun must remain visible instead of being clipped to its bound.
        committed += money(actual if actual is not None else (bound or "0"))
    overrun = bool(bound_overruns) or committed > cap
    blocked = bool(unknown) or overrun
    return {"limit_usd": str(cap), "committed_or_bounded_usd": str(committed),
            "unreconciled_ids": sorted(set(unknown)),
            "remaining_usd": None if unknown else str(max(Decimal(0), cap - committed)),
            "paid_execution_allowed": not blocked, "overrun": overrun,
            "reservation_overrun_ids": bound_overruns}


def save(path: Path, data: dict) -> None:
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n"); tmp.flush(); os.fsync(tmp.fileno())
    os.replace(tmp.name, path)


@contextmanager
def locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix + ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def initialize(path: Path, limit_usd, prior: list[dict]) -> dict:
    with locked(path):
        if path.exists():
            raise ValueError("Do not overwrite a budget ledger")
        if money(limit_usd) <= 0:
            raise ValueError("Positive limit required")
        if len({e["id"] for e in prior}) != len(prior):
            raise ValueError("Prior entry ids must be unique")
        for entry in prior:
            if entry["status"] not in {"settled", "prior_unreconciled", "unknown"} or not entry.get("evidence"):
                raise ValueError("Prior costs require status and evidence")
            if entry["status"] == "settled" and entry.get("actual_usd") is None:
                raise ValueError("Settled entry requires an actual amount including fees")
            for field in ("actual_usd", "estimated_usd", "worst_case_usd"):
                if entry.get(field) is not None:
                    money(entry[field])
        data = {"version": 1, "limit_usd": str(money(limit_usd)), "entries": prior}
        result = summary(data)
        save(path, data)
        return result


def reserve(path: Path, request_id: str, worst_case_usd, evidence: str) -> dict:
    bound = money(worst_case_usd)
    if not request_id.strip() or not evidence.strip() or bound <= 0:
        raise ValueError("Reservation requires id, positive worst case, and bound evidence")
    with locked(path):
        data = json.loads(path.read_text())
        state = summary(data)
        if not state["paid_execution_allowed"]:
            raise ValueError("Paid execution blocked: prior cost unknown or budget overrun")
        if any(e["id"] == request_id for e in data["entries"]):
            raise ValueError("Duplicate or uncertain request; never retry with the same id")
        if money(state["committed_or_bounded_usd"]) + bound > money(data["limit_usd"]):
            raise ValueError("Budget exhausted before billable I/O")
        data["entries"].append({"id": request_id, "status": "reserved",
                                "worst_case_usd": str(bound), "actual_usd": None,
                                "evidence": evidence})
        save(path, data)
        return summary(data)


def settle(path: Path, request_id: str, actual_usd, evidence: str) -> dict:
    actual = money(actual_usd)
    if not evidence.strip():
        raise ValueError("Billing/usage evidence is required")
    with locked(path):
        data = json.loads(path.read_text())
        entry = next(e for e in data["entries"] if e["id"] == request_id)
        if entry["status"] == "settled":
            raise ValueError("Do not overwrite settled cost evidence")
        entry.update(status="settled", actual_usd=str(actual), settlement_evidence=evidence)
        save(path, data)
        return summary(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("init"); p.add_argument("--limit-usd", required=True); p.add_argument("--prior", type=Path, required=True)
    p = sub.add_parser("reserve"); p.add_argument("--id", required=True); p.add_argument("--worst-case-usd", required=True); p.add_argument("--evidence", required=True)
    p = sub.add_parser("settle"); p.add_argument("--id", required=True); p.add_argument("--actual-usd", required=True); p.add_argument("--evidence", required=True)
    sub.add_parser("status")
    a = parser.parse_args()
    if a.action == "init": result = initialize(a.ledger, a.limit_usd, json.loads(a.prior.read_text()))
    elif a.action == "reserve": result = reserve(a.ledger, a.id, a.worst_case_usd, a.evidence)
    elif a.action == "settle": result = settle(a.ledger, a.id, a.actual_usd, a.evidence)
    else:
        with locked(a.ledger): result = summary(json.loads(a.ledger.read_text()))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
