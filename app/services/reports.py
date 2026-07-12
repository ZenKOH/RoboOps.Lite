from __future__ import annotations

from datetime import datetime, timezone
from sqlite3 import Row
from typing import Iterable


def row_to_dict(row: Row | None) -> dict:
    return dict(row) if row is not None else {}


def build_markdown_report(trial: Row, robot: Row | None, skill: Row | None, events: Iterable[Row]) -> str:
    trial_d = row_to_dict(trial)
    robot_d = row_to_dict(robot)
    skill_d = row_to_dict(skill)
    event_rows = [row_to_dict(event) for event in events]

    lines = [
        f"# RoboOps Lite Deployment Report: {trial_d.get('title', 'Untitled Trial')}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## Trial Summary",
        f"- Status: {trial_d.get('status', 'unknown')}",
        f"- Environment: {trial_d.get('environment') or 'Not specified'}",
        f"- Model version: {trial_d.get('model_version') or 'Not specified'}",
        f"- Protocol: {trial_d.get('protocol') or 'Not specified'}",
        f"- Duration: {trial_d.get('duration_seconds', 0)} seconds",
        f"- Success rate: {trial_d.get('success_rate', 0)}",
        f"- Failure count: {trial_d.get('failure_count', 0)}",
        f"- Intervention count: {trial_d.get('intervention_count', 0)}",
        f"- Failure summary: {trial_d.get('failure_summary') or 'None recorded'}",
        "",
        "## Robot",
        f"- Name: {robot_d.get('name', 'Not linked')}",
        f"- Platform: {robot_d.get('platform', 'Not linked')}",
        f"- Hardware version: {robot_d.get('hardware_version', '')}",
        f"- Firmware version: {robot_d.get('firmware_version', '')}",
        "",
        "## Skill",
        f"- Name: {skill_d.get('name', 'Not linked')}",
        f"- Category: {skill_d.get('category', '')}",
        f"- Status: {skill_d.get('status', '')}",
        f"- Safety boundary: {skill_d.get('safety_boundary', '')}",
        "",
        "## Event Log Snapshot",
    ]

    if not event_rows:
        lines.append("No events recorded.")
    else:
        lines.extend([
            "| Timestamp | Event | Label | Confidence | Value |",
            "|---:|---|---|---:|---:|",
        ])
        for event in event_rows[:50]:
            lines.append(
                f"| {event.get('timestamp') if event.get('timestamp') is not None else ''} "
                f"| {event.get('event_type', '')} "
                f"| {event.get('label', '')} "
                f"| {event.get('confidence') if event.get('confidence') is not None else ''} "
                f"| {event.get('value') if event.get('value') is not None else ''} |"
            )

    lines.extend([
        "",
        "## Notes",
        trial_d.get("notes") or "No notes recorded.",
        "",
        "## Deployment Interpretation",
        "This report is a lightweight operational artifact. It is intended to support engineering review, customer-facing validation, investor updates, and internal post-trial learning. It is not a safety certification or regulatory submission.",
    ])
    return "\n".join(lines)
