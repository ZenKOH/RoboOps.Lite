# RoboOps Lite

**RoboOps Lite** is a local-first robot trial analytics and deployment reporting MVP for physical AI teams.

It helps robotics teams answer five practical questions:

1. What happened during this robot trial?
2. Why did the trial fail?
3. Which skill or model version improved?
4. Which robot behaviours are ready for field testing?
5. What evidence can we show customers, investors, operators, or internal reviewers?

The product direction comes from the shift visible in RoboCup and humanoid robotics: hardware platforms are becoming more standardised, while value is moving into perception, decision-making, coordination, testing, field validation, and deployment evidence.

## What the MVP does

- Register robots and hardware/firmware versions
- Register robot skills such as fall recovery, navigation, inspection, pick/place, or rehabilitation tasks
- Create robot trials and link them to robots, skills, environments, protocols, and model versions
- Upload `.csv` or `.json` trial logs
- Automatically calculate:
  - duration
  - success rate
  - failure count
  - intervention count
  - top failure causes
- Add manual annotations after trial review
- Export Markdown deployment reports
- Run entirely on your MacBook using SQLite

## Why this matters

Robotics is moving from hardware craftsmanship to software-defined embodied performance.

The missing layer is not another robot demo. It is deployment memory: the loop that helps teams simulate, deploy, observe, diagnose, improve, validate, and redeploy physical AI systems.

RoboOps Lite is the first small step toward that operating layer.

## Quick start on MacBook

```bash
git clone https://github.com/ZenKOH/RoboOps.Lite.git
cd RoboOps.Lite
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Try the sample log

1. Add a robot, for example `Booster T1 Alpha`.
2. Add a skill, for example `Walk to ball and recover from fall`.
3. Create a trial.
4. Upload `sample_data/robocup_trial.csv` into the trial.
5. Open the exported Markdown report.

## CSV log format

RoboOps Lite accepts CSV files with flexible columns. These are recommended:

```csv
timestamp,event_type,label,confidence,value
0,start,trial_started,,
1.2,detect_ball,ball_seen,0.91,
6.1,fall,turning_instability,,
15.2,task_success,goal_reached,,1
```

Recognised event types include:

- success events: `success`, `task_success`, `completed`, `goal_reached`
- failure events: `failure`, `fail`, `fall`, `collision`, `unsafe`, `timeout`, `lost_target`
- intervention events: `intervention`, `override`, `manual_override`, `operator_override`, `human_assist`

## JSON log format

```json
[
  {"timestamp": 0, "event_type": "start", "label": "trial_started"},
  {"timestamp": 4.5, "event_type": "fall", "label": "turning_instability"},
  {"timestamp": 10.2, "event_type": "task_success", "label": "goal_reached"}
]
```

Or:

```json
{
  "events": [
    {"timestamp": 0, "event_type": "start"},
    {"timestamp": 10.2, "event_type": "task_success"}
  ]
}
```

## Project structure

```text
app/
  main.py                 FastAPI app and routes
  database.py             SQLite schema and connection management
  schemas.py              Pydantic request models
  services/
    analytics.py          Log parsing and trial metrics
    reports.py            Markdown deployment reports
  templates/              HTML dashboard and trial pages
  static/                 CSS
sample_data/              Example robot trial log
tests/                    Unit and endpoint tests
.github/workflows/ci.yml  GitHub Actions test workflow
```

## Roadmap

### Phase 1: Local trial intelligence

- [x] Register robots
- [x] Register skills
- [x] Create trials
- [x] Upload CSV/JSON logs
- [x] Generate basic metrics
- [x] Export Markdown reports

### Phase 2: Better robotics integration

- [ ] ROS bag / MCAP parser
- [ ] Foxglove-compatible timeline export
- [ ] Video upload and event alignment
- [ ] Failure replay timeline
- [ ] Model-version comparison page

### Phase 3: Deployment evidence layer

- [ ] Skill readiness scoring
- [ ] Field-test protocol templates
- [ ] Customer-ready PDF reports
- [ ] Operator acceptance and workflow-fit surveys
- [ ] Safety incident register

### Phase 4: Physical AI operations platform

- [ ] Robot context layer
- [ ] Site maps and no-go zones
- [ ] Tool and action permissions
- [ ] Simulation-to-field regression tests
- [ ] Multi-site deployment dashboard

## Safety and scope

RoboOps Lite is an engineering and deployment intelligence tool. It is not a safety certification system, medical device, autonomous robot controller, or regulatory submission platform.

Do not use this software as the only source of truth for safety-critical robotics decisions.

## License

MIT
