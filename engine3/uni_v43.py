"""BRIDGE UNI v4.3 scoring and time aggregation.

The module keeps slow official baselines separate from daily observations.
Missing axes remain None; they are never imputed as neutral or perfect scores.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Iterable
import json
import math
import re

AXES = ("B", "R", "I", "D", "G", "E")
WEIGHTS = {"B": 0.15, "R": 0.25, "I": 0.15, "D": 0.10, "G": 0.20, "E": 0.15}

# Daily events should refine, not overwrite, the structural baseline.
DAILY_AXIS_CAP = {"B": 4.0, "R": 7.0, "I": 3.0, "D": 4.0, "G": 6.0, "E": 7.0}
SOURCE_QUALITY = {
    "regulated_official": 1.00,
    "public_official": 0.90,
    "university_owned": 0.65,
    "independent_media": 0.75,
    "expert_blog": 0.55,
    "public_community": 0.40,
    "unknown": 0.20,
}
EVENT_ACTIVITY = {
    "official_update": 1.00,
    "claim": 0.35,
    "response": 0.60,
    "experience": 0.70,
    "achievement": 0.85,
    "correction": 0.80,
    "sanction": 1.00,
}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def weighted_index(dims: dict[str, float | None]) -> float | None:
    observed = [(a, dims.get(a)) for a in AXES if dims.get(a) is not None]
    if len(observed) < 2:
        return None
    denominator = sum(WEIGHTS[a] for a, _ in observed)
    return round(sum(WEIGHTS[a] * float(v) for a, v in observed) / denominator, 1)


def canonical_text(value: str) -> str:
    value = re.sub(r"https?://\S+", "", value or "")
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value


def event_key(event: dict[str, Any]) -> str:
    stable = "|".join([
        str(event.get("university_id") or event.get("name") or ""),
        str(event.get("event_type") or ""),
        str(event.get("axis") or ""),
        canonical_text(str(event.get("title") or event.get("text") or ""))[:240],
        str(event.get("published_at") or "")[:10],
    ])
    return sha256(stable.encode("utf-8")).hexdigest()[:24]


def freshness(published_at: str | None, as_of: datetime, half_life_days: float = 7.0) -> float:
    if not published_at:
        return 0.5
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = max(0.0, (as_of.astimezone(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 86400)
        return math.pow(0.5, age / half_life_days)
    except (TypeError, ValueError):
        return 0.5


def _event_delta(event: dict[str, Any], as_of: datetime) -> tuple[str | None, float, float]:
    axis = str(event.get("axis") or "").upper()
    if axis not in AXES:
        return None, 0.0, 0.0
    source_class = str(event.get("source_class") or "unknown")
    quality = SOURCE_QUALITY.get(source_class, SOURCE_QUALITY["unknown"])
    verified = str(event.get("verification_status") or "unverified")
    verification = {"officially_confirmed": 1.0, "cross_confirmed": 0.85,
                    "single_source": 0.60, "unverified": 0.25}.get(verified, 0.25)
    direction = clamp(float(event.get("direction", 0.0)), -1.0, 1.0)
    severity = clamp(float(event.get("severity", 0.5)), 0.0, 1.0)
    fresh = freshness(event.get("published_at"), as_of,
                      float(event.get("half_life_days") or (28 if axis == "I" else 7)))
    delta = direction * severity * quality * verification * fresh * DAILY_AXIS_CAP[axis]
    event_type = str(event.get("event_type") or "response")
    activity = EVENT_ACTIVITY.get(event_type, 0.40) * quality * verification * fresh
    return axis, delta, activity


def apply_daily_events(baseline: dict[str, float | None], events: Iterable[dict[str, Any]],
                       as_of: datetime) -> dict[str, Any]:
    unique: dict[str, dict[str, Any]] = {}
    for event in events:
        unique.setdefault(event.get("event_key") or event_key(event), event)
    deltas = {a: 0.0 for a in AXES}
    activities = []
    source_classes = set()
    for event in unique.values():
        axis, delta, activity = _event_delta(event, as_of)
        if not axis:
            continue
        deltas[axis] += delta
        activities.append(activity)
        source_classes.add(str(event.get("source_class") or "unknown"))
    for axis in AXES:
        deltas[axis] = clamp(deltas[axis], -DAILY_AXIS_CAP[axis], DAILY_AXIS_CAP[axis])

    dims: dict[str, float | None] = {}
    for axis in AXES:
        base = baseline.get(axis)
        # A daily event may establish R or I when no structural baseline exists.
        if base is None and abs(deltas[axis]) > 0:
            base = 50.0
        dims[axis] = None if base is None else round(clamp(float(base) + deltas[axis]), 1)
    return {
        "dims": dims,
        "daily_index": weighted_index(dims),
        "activity_points": round(sum(activities), 2),
        "event_count": len(unique),
        "source_diversity": len(source_classes),
        "axis_delta": {a: round(v, 2) for a, v in deltas.items()},
    }


def weekly_rollup(days: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [d for d in days if d.get("daily_index") is not None]
    def q(d: dict[str, Any]) -> float:
        return max(0.10, min(1.0, float(d.get("quality", 0.5))))
    denominator = sum(q(d) for d in valid)
    weekly = None if not denominator else round(sum(float(d["daily_index"]) * q(d) for d in valid) / denominator, 1)
    axis_weekly = {}
    for axis in AXES:
        vals = [(d.get("dims", {}).get(axis), q(d)) for d in valid if d.get("dims", {}).get(axis) is not None]
        axis_weekly[axis] = None if not vals else round(sum(float(v) * w for v, w in vals) / sum(w for _, w in vals), 1)
    return {
        "weekly_index": weekly,
        "dims": axis_weekly,
        "activity_points": round(sum(float(d.get("activity_points", 0)) for d in days), 2),
        "observed_days": len(valid),
        "mention_days": sum(1 for d in days if int(d.get("event_count", 0)) > 0),
        "source_diversity": len({s for d in days for s in d.get("source_ids", [])}),
    }


def select_t100(records: list[dict[str, Any]], current_members: set[str] | None = None,
                margin: float = 1.0) -> dict[str, list[dict[str, Any]]]:
    """Return dynamic 60 four-year + 40 junior-college membership.

    A current member keeps its seat unless a challenger exceeds the cutoff by
    `margin`; this prevents one noisy day from causing avoidable churn.
    """
    current_members = current_members or set()
    eligible = [r for r in records if r.get("eligible") and r.get("score") is not None]

    def choose(kind: str, quota: int) -> list[dict[str, Any]]:
        pool = sorted((r for r in eligible if r.get("school_kind") == kind),
                      key=lambda r: (-float(r["score"]), str(r.get("name", ""))))
        if len(pool) <= quota or not current_members:
            return pool[:quota]
        incumbents = [r for r in pool if r.get("university_id") in current_members]
        challengers = [r for r in pool if r.get("university_id") not in current_members]
        selected = sorted(incumbents, key=lambda r: -float(r["score"]))[:quota]
        while len(selected) < quota and challengers:
            selected.append(challengers.pop(0))
        for challenger in challengers:
            weakest = min(selected, key=lambda r: float(r["score"]))
            if float(challenger["score"]) >= float(weakest["score"]) + margin:
                selected.remove(weakest)
                selected.append(challenger)
        return sorted(selected, key=lambda r: (-float(r["score"]), str(r.get("name", ""))))

    four = choose("대학", 60)
    two = choose("전문대학", 40)
    combined = sorted(four + two, key=lambda r: (-float(r["score"]), str(r.get("name", ""))))
    for rank, row in enumerate(combined, 1):
        row["t100_rank"] = rank
    for rank, row in enumerate(four, 1):
        row["cohort_rank"] = rank
    for rank, row in enumerate(two, 1):
        row["cohort_rank"] = rank
    return {"T100": combined, "U60": four, "C40": two}


def dump_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)

