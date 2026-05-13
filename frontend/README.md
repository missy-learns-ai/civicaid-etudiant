# CivicAid Étudiant React Dashboard

CivicAid Étudiant helps non-EU students arriving in France generate a personalized administrative roadmap across VLS-TS validation, CVEC/university registration, Ameli health insurance, bank/RIB setup, housing, CAF readiness, and residence-renewal timing.

Local frontend for the Phase 1 product architecture:

```text
React dashboard
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
npm install
```

Start the dashboard:

```bash
npm run dev
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
VITE_CIVICAID_API_BASE_URL=https://YOUR_BACKEND_URL npm run dev
```

To prefill the ElevenLabs widget agent:

```bash
VITE_ELEVENLABS_AGENT_ID=agent_xxx npm run dev
```

No agent id is hardcoded in the dashboard. Set `VITE_ELEVENLABS_AGENT_ID` locally or in your hosting provider.

The dashboard creates a browser-local student id by default. Set `VITE_CIVICAID_STUDENT_ID=demo_001` only when you intentionally want to test against a fixed profile. To reset the current browser to a fresh generated profile, open the dashboard with `?new_student=1`.

Do not put private API keys or tokens in `VITE_*` variables. Vite embeds those values into the browser bundle.

## ElevenLabs widget

The widget area uses the ElevenLabs `elevenlabs-convai` web component with:

- `dynamic-variables` containing `student_id`, `api_base_url`, and product context
- an override first message for the CivicAid Étudiant intake

For the basic embed to work, your ElevenLabs agent must be public with authentication disabled. Configure allowed domains in the ElevenLabs security settings before sharing a deployed dashboard.
