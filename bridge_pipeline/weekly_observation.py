"""Weekly six-axis observability contract for BRIDGE.

This module records whether each entity/axis was newly observed, validly
maintained, honestly referenced after a successful check, or not verified
because collection failed. It never manufactures an axis score.
"""
from __future__ import annotations

import datetime as dt
from typing import Iterable

AXES = ("B", "R", "I", "D", "G", "E")
STATE_LABELS = {
    "O": "observed",
    "M": "maintained",
    "R": "reference",
    "F": "failed",
}


def axis_week_state(observations: Iterable[dict], collection_status: str) -> dict:
    rows = list(observations)
    measured_days = len({str(row.get("as_of_date")) for row in rows
                         if row.get("status") == "measured" and row.get("score") is not None})
    maintained_days = len({str(row.get("as_of_date")) for row in rows
                           if row.get("status") == "carried" and row.get("score") is not None})
    reference_days = len({str(row.get("as_of_date")) for row in rows
                          if row.get("status") not in {"measured", "carried"} or row.get("score") is None})
    if measured_days:
        state = "O"
    elif maintained_days:
        state = "M"
    elif collection_status == "success":
        state = "R"
    else:
        state = "F"
    return {
        "state": state,
        "public_state": STATE_LABELS[state],
        "new_observation_days": measured_days,
        "maintained_days": maintained_days,
        "reference_days": reference_days,
        "collection_checked": state != "F",
    }


def weekly_entity_summary(by_axis: dict[str, list[dict]], collection_status: str) -> dict:
    states = {axis: axis_week_state(by_axis.get(axis, []), collection_status) for axis in AXES}
    codes = {axis: row["state"] for axis, row in states.items()}
    available = sum(code in {"O", "M"} for code in codes.values())
    return {
        "states": states,
        "state_codes": codes,
        "public_states": {axis: row["public_state"] for axis, row in states.items()},
        "available_axes": available,
        "reference_axes": [axis for axis, code in codes.items() if code == "R"],
        "failed_axes": [axis for axis, code in codes.items() if code == "F"],
        "collection_complete": all(code != "F" for code in codes.values()),
    }


def remediation_stage(reference_streak_weeks: int) -> str:
    if reference_streak_weeks >= 6:
        return "measurement_design_review"
    if reference_streak_weeks >= 4:
        return "operational_definition_review"
    if reference_streak_weeks >= 3:
        return "attribution_and_alias_review"
    if reference_streak_weeks >= 2:
        return "supplementary_source_search"
    return "normal_reference"


def week_bounds(value: dt.date) -> tuple[dt.date, dt.date]:
    monday = value - dt.timedelta(days=value.weekday())
    return monday, monday + dt.timedelta(days=6)
