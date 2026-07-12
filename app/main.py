from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import UPLOAD_DIR
from .database import get_db, init_db
from .schemas import RobotCreate, SkillCreate, TrialAnnotation, TrialCreate
from .services.analytics import load_events, summarise_events
from .services.reports import build_markdown_report

app = FastAPI(
    title="RoboOps Lite",
    description="Local-first robot trial analytics and deployment reporting for physical AI teams.",
    version="0.1.0",
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def startup() -> None:
    init_db()


def fetch_dashboard_data() -> dict[str, Any]:
    with get_db() as conn:
        robots = conn.execute("SELECT * FROM robots ORDER BY created_at DESC").fetchall()
        skills = conn.execute("SELECT * FROM skills ORDER BY created_at DESC").fetchall()
        trials = conn.execute(
            """
            SELECT trials.*, robots.name AS robot_name, skills.name AS skill_name
            FROM trials
            LEFT JOIN robots ON trials.robot_id = robots.id
            LEFT JOIN skills ON trials.skill_id = skills.id
            ORDER BY trials.created_at DESC
            """
        ).fetchall()
        totals = conn.execute(
            """
            SELECT
              COUNT(*) AS trial_count,
              COALESCE(AVG(success_rate), 0) AS avg_success_rate,
              COALESCE(SUM(failure_count), 0) AS total_failures,
              COALESCE(SUM(intervention_count), 0) AS total_interventions
            FROM trials
            """
        ).fetchone()
    return {"robots": robots, "skills": skills, "trials": trials, "totals": totals}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"request": request, **fetch_dashboard_data()})


@app.post("/robots")
def create_robot(
    name: str = Form(...),
    platform: str = Form(...),
    hardware_version: str = Form(""),
    firmware_version: str = Form(""),
    notes: str = Form(""),
) -> RedirectResponse:
    payload = RobotCreate(
        name=name,
        platform=platform,
        hardware_version=hardware_version,
        firmware_version=firmware_version,
        notes=notes,
    )
    with get_db() as conn:
        conn.execute(
            "INSERT INTO robots (name, platform, hardware_version, firmware_version, notes) VALUES (?, ?, ?, ?, ?)",
            (payload.name, payload.platform, payload.hardware_version, payload.firmware_version, payload.notes),
        )
    return RedirectResponse("/", status_code=303)


@app.post("/skills")
def create_skill(
    name: str = Form(...),
    category: str = Form("general"),
    description: str = Form(""),
    compatible_platforms: str = Form(""),
    status: str = Form("lab"),
    safety_boundary: str = Form(""),
) -> RedirectResponse:
    payload = SkillCreate(
        name=name,
        category=category,
        description=description,
        compatible_platforms=compatible_platforms,
        status=status,
        safety_boundary=safety_boundary,
    )
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO skills (name, category, description, compatible_platforms, status, safety_boundary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.category,
                payload.description,
                payload.compatible_platforms,
                payload.status,
                payload.safety_boundary,
            ),
        )
    return RedirectResponse("/", status_code=303)


@app.post("/trials")
def create_trial(
    title: str = Form(...),
    robot_id: int | None = Form(None),
    skill_id: int | None = Form(None),
    environment: str = Form(""),
    model_version: str = Form(""),
    protocol: str = Form(""),
    status: str = Form("unknown"),
    notes: str = Form(""),
) -> RedirectResponse:
    payload = TrialCreate(
        title=title,
        robot_id=robot_id,
        skill_id=skill_id,
        environment=environment,
        model_version=model_version,
        protocol=protocol,
        status=status,
        notes=notes,
    )
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO trials (title, robot_id, skill_id, environment, model_version, protocol, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title,
                payload.robot_id,
                payload.skill_id,
                payload.environment,
                payload.model_version,
                payload.protocol,
                payload.status,
                payload.notes,
            ),
        )
    return RedirectResponse("/", status_code=303)


@app.post("/trials/{trial_id}/upload-log")
def upload_log(trial_id: int, log_file: UploadFile = File(...)) -> RedirectResponse:
    if not log_file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    suffix = Path(log_file.filename).suffix.lower()
    if suffix not in {".csv", ".json"}:
        raise HTTPException(status_code=400, detail="Only .csv and .json logs are supported.")

    saved_path = UPLOAD_DIR / f"trial_{trial_id}_{uuid.uuid4().hex}{suffix}"
    with saved_path.open("wb") as f:
        shutil.copyfileobj(log_file.file, f)

    try:
        events = load_events(saved_path)
        summary = summarise_events(events)
    except Exception as exc:  # noqa: BLE001 - convert parsing errors to HTTP response
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    with get_db() as conn:
        trial = conn.execute("SELECT id FROM trials WHERE id = ?", (trial_id,)).fetchone()
        if not trial:
            raise HTTPException(status_code=404, detail="Trial not found.")
        conn.execute("DELETE FROM trial_events WHERE trial_id = ?", (trial_id,))
        conn.executemany(
            """
            INSERT INTO trial_events (trial_id, timestamp, event_type, label, confidence, value, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    trial_id,
                    event.get("timestamp"),
                    event.get("event_type"),
                    event.get("label"),
                    event.get("confidence"),
                    event.get("value"),
                    event.get("metadata", ""),
                )
                for event in events
            ],
        )
        conn.execute(
            """
            UPDATE trials
            SET success_rate = ?, duration_seconds = ?, intervention_count = ?, failure_count = ?, failure_summary = ?, log_path = ?
            WHERE id = ?
            """,
            (
                summary["success_rate"],
                summary["duration_seconds"],
                summary["intervention_count"],
                summary["failure_count"],
                summary["failure_summary"],
                str(saved_path),
                trial_id,
            ),
        )
    return RedirectResponse("/", status_code=303)


@app.post("/trials/{trial_id}/annotate")
def annotate_trial(
    trial_id: int,
    timestamp: float | None = Form(None),
    event_type: str = Form(...),
    label: str = Form(""),
    confidence: float | None = Form(None),
    value: float | None = Form(None),
    metadata: str = Form(""),
) -> RedirectResponse:
    payload = TrialAnnotation(
        timestamp=timestamp,
        event_type=event_type,
        label=label,
        confidence=confidence,
        value=value,
        metadata=metadata,
    )
    with get_db() as conn:
        trial = conn.execute("SELECT id FROM trials WHERE id = ?", (trial_id,)).fetchone()
        if not trial:
            raise HTTPException(status_code=404, detail="Trial not found.")
        conn.execute(
            """
            INSERT INTO trial_events (trial_id, timestamp, event_type, label, confidence, value, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (trial_id, payload.timestamp, payload.event_type, payload.label, payload.confidence, payload.value, payload.metadata),
        )
    return RedirectResponse(f"/trials/{trial_id}", status_code=303)


@app.get("/trials/{trial_id}", response_class=HTMLResponse)
def trial_detail(request: Request, trial_id: int) -> HTMLResponse:
    with get_db() as conn:
        trial = conn.execute(
            """
            SELECT trials.*, robots.name AS robot_name, skills.name AS skill_name
            FROM trials
            LEFT JOIN robots ON trials.robot_id = robots.id
            LEFT JOIN skills ON trials.skill_id = skills.id
            WHERE trials.id = ?
            """,
            (trial_id,),
        ).fetchone()
        if not trial:
            raise HTTPException(status_code=404, detail="Trial not found.")
        events = conn.execute("SELECT * FROM trial_events WHERE trial_id = ? ORDER BY timestamp", (trial_id,)).fetchall()
    return templates.TemplateResponse(request=request, name="trial.html", context={"request": request, "trial": trial, "events": events})


@app.get("/trials/{trial_id}/report.md", response_class=PlainTextResponse)
def trial_report(trial_id: int) -> str:
    with get_db() as conn:
        trial = conn.execute("SELECT * FROM trials WHERE id = ?", (trial_id,)).fetchone()
        if not trial:
            raise HTTPException(status_code=404, detail="Trial not found.")
        robot = conn.execute("SELECT * FROM robots WHERE id = ?", (trial["robot_id"],)).fetchone() if trial["robot_id"] else None
        skill = conn.execute("SELECT * FROM skills WHERE id = ?", (trial["skill_id"],)).fetchone() if trial["skill_id"] else None
        events = conn.execute("SELECT * FROM trial_events WHERE trial_id = ? ORDER BY timestamp", (trial_id,)).fetchall()
    return build_markdown_report(trial, robot, skill, events)
