from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

EVENT_SUCCESS = {"success", "task_success", "completed", "goal_reached"}
EVENT_FAILURE = {"failure", "fail", "fall", "collision", "unsafe", "timeout", "lost_target"}
EVENT_INTERVENTION = {"intervention", "override", "manual_override", "operator_override", "human_assist"}


def _coerce_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalise_event(row: dict[str, Any]) -> dict[str, Any]:
    """Normalise common robot-log columns into a compact event record."""
    event_type = str(
        row.get("event_type")
        or row.get("event")
        or row.get("type")
        or row.get("label")
        or "unknown"
    ).strip().lower()

    label = str(row.get("label") or row.get("failure_cause") or row.get("cause") or "").strip()
    metadata = {k: v for k, v in row.items() if k not in {"timestamp", "time", "t", "event_type", "event", "type", "label", "confidence", "value"}}

    return {
        "timestamp": _coerce_float(row.get("timestamp") or row.get("time") or row.get("t")),
        "event_type": event_type,
        "label": label,
        "confidence": _coerce_float(row.get("confidence")),
        "value": _coerce_float(row.get("value")),
        "metadata": json.dumps(metadata, ensure_ascii=False),
    }


def load_events(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return [normalise_event(row) for row in csv.DictReader(f)]
    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = raw.get("events", [])
        if not isinstance(raw, list):
            raise ValueError("JSON log must be a list of event objects or an object with an events list.")
        return [normalise_event(dict(row)) for row in raw]
    raise ValueError("Unsupported log format. Upload .csv or .json files.")


def summarise_events(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    events = list(events)
    timestamps = [event["timestamp"] for event in events if event.get("timestamp") is not None]
    duration = max(timestamps) - min(timestamps) if len(timestamps) >= 2 else 0.0

    event_counter = Counter(event.get("event_type", "unknown") for event in events)
    failure_events = [event for event in events if event.get("event_type") in EVENT_FAILURE]
    success_events = [event for event in events if event.get("event_type") in EVENT_SUCCESS]
    intervention_events = [event for event in events if event.get("event_type") in EVENT_INTERVENTION]

    labelled_failures = [event.get("label") or event.get("event_type") for event in failure_events]
    top_failures = Counter(labelled_failures).most_common(5)
    attempts = max(len(success_events) + len(failure_events), 1)
    success_rate = round(len(success_events) / attempts, 3)

    return {
        "event_count": len(events),
        "duration_seconds": round(duration, 2),
        "success_count": len(success_events),
        "failure_count": len(failure_events),
        "intervention_count": len(intervention_events),
        "success_rate": success_rate,
        "failure_summary": ", ".join(f"{label} ({count})" for label, count in top_failures),
        "event_breakdown": dict(event_counter),
    }
