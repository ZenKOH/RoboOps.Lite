from pathlib import Path

from app.services.analytics import load_events, summarise_events


def test_load_events_from_csv_sample() -> None:
    events = load_events(Path("sample_data/robocup_trial.csv"))
    assert len(events) == 8
    assert events[0]["event_type"] == "start"
    assert events[-1]["event_type"] == "task_success"


def test_summarise_events_counts_failures_and_interventions() -> None:
    events = load_events(Path("sample_data/robocup_trial.csv"))
    summary = summarise_events(events)
    assert summary["failure_count"] == 1
    assert summary["intervention_count"] == 1
    assert summary["success_count"] == 1
    assert summary["success_rate"] == 0.5
    assert summary["duration_seconds"] == 15.2
