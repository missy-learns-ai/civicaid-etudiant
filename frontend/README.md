# CivicAid Étudiant Dashboard

CivicAid Étudiant helps non-EU students arriving in France generate a personalized administrative roadmap across VLS-TS validation, CVEC/university registration, Ameli health insurance, bank/RIB setup, housing, CAF readiness, and residence-renewal timing.

Local frontend for the Phase 1 product architecture:

```text
Streamlit dashboard
  ↓
FastAPI backend
  ↓
StudentProfile + roadmap engine
```

## Run locally

Start the backend:

```bash
./.venv/bin/python -m uvicorn backend.app:app --reload
```

Install frontend dependencies:

```bash
./.venv/bin/python -m pip install -r frontend/requirements.txt
```

Start the dashboard:

```bash
./.venv/bin/python -m streamlit run frontend/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

## Dashboard flow

1. Add an ElevenLabs agent ID in the sidebar to render the voice session widget.
2. Complete the voice intake so the backend captures student information.
3. Refresh the profile and generate the roadmap from the sidebar.
4. Review the interactive roadmap cards with statuses, blockers, next actions, and sources.

## Configuration

The dashboard calls `http://127.0.0.1:8000` by default.

To point at another backend:

```bash
CIVICAID_API_BASE_URL=https://YOUR_BACKEND_URL ./.venv/bin/python -m streamlit run frontend/streamlit_app.py
```

To prefill the ElevenLabs widget agent:

```bash
ELEVENLABS_AGENT_ID=agent_xxx ./.venv/bin/python -m streamlit run frontend/streamlit_app.py
```

The default local agent id is `agent_0301kqspeqntenb8stq8k9nnwc5q`.

If your deployed backend uses `CIVICAID_TOOL_TOKEN`, set the same environment variable on the Streamlit service. The dashboard sends it as `X-CivicAid-Tool-Token`.

## ElevenLabs widget

The widget area uses the ElevenLabs `elevenlabs-convai` web component with:

- `dynamic-variables` containing `student_id`, `api_base_url`, and product context
- an override first message for the CivicAid Étudiant intake

For the basic embed to work, your ElevenLabs agent must be public with authentication disabled. Configure allowed domains in the ElevenLabs security settings before sharing a deployed dashboard.
