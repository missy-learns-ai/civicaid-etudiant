# CivicAid Étudiant

CivicAid Étudiant is a voice-guided assistant for non-EU students arriving in France. It captures a student's situation through an ElevenLabs voice session, stores a structured profile, and generates an administrative roadmap across VLS-TS validation, CVEC/university registration, Ameli, bank/RIB setup, housing, CAF readiness, and residence-renewal timing.

## Architecture

```text
Streamlit dashboard
  ↓
FastAPI backend
  ↓
StudentProfile + roadmap engine
```

## Local Run

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
./.venv/bin/python -m pip install -r backend/requirements.txt
./.venv/bin/python -m pip install -r frontend/requirements.txt
```

Start the backend:

```bash
./.venv/bin/python -m uvicorn backend.app:app --reload
```

Start the dashboard:

```bash
./.venv/bin/python -m streamlit run frontend/streamlit_app.py
```

Open `http://127.0.0.1:8501`.

## Deployment

This repo includes a `render.yaml` Blueprint for deploying two Render web services:

- `civicaid-etudiant-api`: FastAPI backend
- `civicaid-etudiant-dashboard`: Streamlit dashboard

In Render, create a new Blueprint from this GitHub repo. The dashboard receives the backend private host and port through environment variables, so the Streamlit server can call the API without exposing an internal URL to the browser.

After deployment, configure your ElevenLabs agent server tools to call the public backend URL shown by Render, for example:

```text
https://YOUR_BACKEND_SERVICE.onrender.com/tools/update-student-profile
https://YOUR_BACKEND_SERVICE.onrender.com/tools/generate-arrival-roadmap
```

## Environment Variables

Do not commit real secrets. Use your hosting provider's environment-variable settings.

```text
ELEVENLABS_AGENT_ID=agent_...
CIVICAID_API_BASE_URL=https://YOUR_BACKEND_SERVICE.onrender.com
CIVICAID_TOOL_TOKEN=your-random-secret
```

`CIVICAID_TOOL_TOKEN` is optional. If set on the backend, all `/tools/*` and `/debug/*` calls must include:

```text
X-CivicAid-Tool-Token: your-random-secret
```

Set the same token in the Streamlit service environment so the dashboard can refresh profiles and generate roadmaps. Add the same header in ElevenLabs server tool configuration.

## Privacy

The profile model intentionally avoids storing passport numbers, visa numbers, full addresses, IBANs, social-security numbers, uploaded documents, passwords, and API keys.

## Tests

```bash
./.venv/bin/python -m pytest -q
```
