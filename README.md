# CivicAid Étudiant

CivicAid Étudiant is a voice-guided administrative roadmap assistant for non-EU students arriving in France.

The product uses an ElevenLabs conversational agent to collect a student's situation, a FastAPI backend to persist a structured profile, a deterministic roadmap engine to calculate blockers and next actions, a database-backed recommendation layer to add practical guidance, and a React dashboard to display the final roadmap in a way the student can understand after the call.

The goal is not to replace official French administrative portals. The goal is to help students understand what applies to them, what is blocking them, what to do next, and where to verify information.

## Product Overview

Non-EU students arriving in France often need to coordinate several administrative steps:

- VLS-TS validation
- CVEC and university registration
- Ameli health insurance registration
- French bank account and RIB setup
- Housing documents
- CAF housing-aid readiness
- Residence-renewal timing

These steps are connected. For example, CAF preparation can depend on housing proof, a RIB, valid residence documentation, and sometimes social-security registration. CivicAid Étudiant turns that dependency chain into a structured roadmap.

## Live Architecture

```text
React dashboard
  |
  | fetch profile + generated roadmap
  v
FastAPI backend
  |
  | persists profile, summaries, guidance cards
  v
PostgreSQL database
  |
  | feeds structured inputs into
  v
StudentProfile + roadmap engine
  ^
  |
ElevenLabs agent workflow
  |
  | calls backend server tools during the voice session
  v
Structured student profile updates
```

## Core Idea

The LLM and voice agent do not decide the final roadmap by themselves.

Instead, the ElevenLabs agent acts as an intake and orchestration layer. It asks questions, extracts structured facts, and calls backend tools. The backend owns the rules:

- which steps are done, blocked, ready, future, or unknown;
- which blockers exist;
- which step should be prioritized;
- which guidance cards should appear;
- which official source links should be attached;
- whether the roadmap is full-scope or CAF-focused.

This separation makes the system easier to test, safer to modify, and more predictable than asking the LLM to invent the entire roadmap in free text.

## Component Roles

### ElevenLabs Agent

The ElevenLabs agent is the voice interface. It guides the student through a structured intake and calls server tools when useful facts are collected.

Main responsibilities:

- welcome the student and explain the assistant's boundaries;
- check whether the student is in scope;
- ask one question at a time;
- collect arrival, visa, university, Ameli, bank, housing, CAF, and renewal information;
- call backend tools to update the profile;
- generate a roadmap through the backend;
- save a short call summary.

The workflow is intentionally tool-driven. The voice agent should not store sensitive data or make final eligibility decisions.

### FastAPI Backend

The backend exposes the tool endpoints used by ElevenLabs and the dashboard.

Main responsibilities:

- validate and normalize incoming tool payloads;
- prevent empty values from overwriting existing profile fields;
- persist profile data;
- generate roadmaps through deterministic business logic;
- calculate renewal timing;
- attach recommendation cards from the database;
- expose debug endpoints for local testing and dashboard refresh;
- optionally protect tool calls with `CIVICAID_TOOL_TOKEN`.

### PostgreSQL Database

The database stores the product's durable state.

Stored data includes:

- student profile fields;
- call summaries;
- recommendation or guidance cards;
- source links for official references.

The deployed app uses PostgreSQL on Render. Local development falls back to SQLite at `./data/civicaid.db`.

### Roadmap Engine

The roadmap engine is the decision layer.

It consumes a `StudentProfile` and produces:

- roadmap title and summary;
- ordered roadmap steps;
- status per step;
- blockers per step;
- next action per step;
- top priority step;
- unknown fields still worth resolving;
- safety disclaimer;
- optional scope, such as `full` or `caf`.

The engine is intentionally deterministic. This makes the product testable without needing ElevenLabs tokens.

### Guidance Card Layer

The guidance card layer adds practical value beyond a checklist.

For example, if the student does not have a French bank account or RIB, the roadmap can show:

- why the bank account matters;
- which documents to prepare;
- what actions to take before visiting a bank;
- where to verify the information officially.

Current seeded guidance cards cover:

- bank account and RIB preparation;
- CAF housing-aid prerequisites;
- housing proof;
- VLS-TS validation;
- Ameli registration.

Sources are attached per topic rather than using one generic link for everything.

### React Dashboard

The dashboard is the student's post-call view.

Main responsibilities:

- embed the ElevenLabs voice widget;
- show the roadmap after the voice session;
- display each step with status, blockers, next action, and guidance;
- show student profile data;
- refresh when profile data changes;
- avoid repeatedly regenerating the roadmap unless the profile changes.

The dashboard is built with React, Vite, Framer Motion, and Lucide icons.

## Data Flow

```text
1. Student opens the dashboard.
2. Student starts the ElevenLabs voice session.
3. ElevenLabs asks intake questions.
4. ElevenLabs calls FastAPI server tools after collecting structured facts.
5. FastAPI updates the student profile in PostgreSQL.
6. ElevenLabs calls generate_arrival_roadmap.
7. The backend roadmap engine calculates steps, blockers, and priorities.
8. The backend attaches database guidance cards.
9. The dashboard fetches the profile and generated roadmap.
10. The student reviews the roadmap without needing to replay the call.
```

## ElevenLabs Agentic Workflow

The agent workflow is designed around routing and tool calls.

High-level node flow:

```text
N01_Disclaimer
  |
  v
N02_Intent_And_Scope
  |-- out of scope --> N03_Out_Of_Scope --> End
  |
  v
N04_Arrival_Status
  |-- not arrived --> N05_Pre_Arrival_Message --> N05_Pre_Arrival_Choice
  |                                                       |
  |                                                       v
  |                                                optional light intake
  v
N06_Visa_Intake
  |
  v
N07_University_Intake
  |
  v
N08_Ameli_Intake
  |
  v
N09_Bank_RIB_Intake
  |
  v
N10_Housing_CAF_Intake
  |
  v
N11_Visa_Expiry_Intake
  |
  v
Generate roadmap tool
  |
  v
N13_Final_Summary
  |
  v
Save call summary tool
  |
  v
End
```

The workflow can also support intent-aware routing. For example, if a student says, "I only care about CAF," the agent should still collect prerequisite information needed for CAF, but it should avoid unrelated future topics unless the user asks for them.

In that case, the agent should generate:

```json
{
  "student_id": "{{student_id}}",
  "roadmap_scope": "caf"
}
```

This avoids overloading the user with unrelated steps like residence-renewal tracking when the immediate goal is CAF readiness.

## Backend Tool Endpoints

The ElevenLabs agent calls these backend tools.

Base URL in production:

```text
https://civicaid-etudiant-api.onrender.com
```

### Health

```http
GET /health
```

Returns service status.

### Scope Profile

```http
POST /tools/update-scope-profile
```

Captures scope fields:

```json
{
  "student_id": "{{student_id}}",
  "nationality_category": "non_eu",
  "country": "Nepal"
}
```

### Arrival and Visa Profile

```http
POST /tools/update-arrival-visa-profile
```

Captures arrival and visa information:

```json
{
  "student_id": "{{student_id}}",
  "has_arrived": true,
  "arrival_date": "2025-10-25",
  "visa_type": "vls_ts_student",
  "visa_validated": true,
  "has_french_address": true
}
```

### University Profile

```http
POST /tools/update-university-profile
```

Captures CVEC and registration state:

```json
{
  "student_id": "{{student_id}}",
  "cvec_status": "done",
  "university_registration_status": "done",
  "has_certificat_scolarite": true,
  "has_student_card": true
}
```

### Ameli Profile

```http
POST /tools/update-ameli-profile
```

Captures health-insurance registration state:

```json
{
  "student_id": "{{student_id}}",
  "ameli_registered": false
}
```

### Bank and RIB Profile

```http
POST /tools/update-bank-profile
```

Captures banking readiness:

```json
{
  "student_id": "{{student_id}}",
  "has_bank_account": false,
  "has_rib": false
}
```

### Housing and CAF Profile

```http
POST /tools/update-housing-caf-profile
```

Captures housing and CAF intent:

```json
{
  "student_id": "{{student_id}}",
  "housing_status": "temporary",
  "has_permanent_housing": false,
  "has_rental_contract": false,
  "wants_caf": true
}
```

### Renewal Profile

```http
POST /tools/update-renewal-profile
```

Captures visa or residence-document expiry:

```json
{
  "student_id": "{{student_id}}",
  "visa_expiry_date": "2027-09-09"
}
```

### Generate Roadmap

```http
POST /tools/generate-arrival-roadmap
```

Generate the full roadmap:

```json
{
  "student_id": "{{student_id}}",
  "roadmap_scope": "full"
}
```

Generate a CAF-focused roadmap:

```json
{
  "student_id": "{{student_id}}",
  "roadmap_scope": "caf"
}
```

### Save Call Summary

```http
POST /tools/save-call-summary
```

Stores a short, non-sensitive summary:

```json
{
  "student_id": "{{student_id}}",
  "conversation_id": "conv_123",
  "summary": "The student is a non-EU student from Nepal who wants CAF guidance and needs bank/RIB and permanent housing steps."
}
```

## Roadmap Step Model

Each roadmap step can include:

- `step_id`
- `title`
- `status`
- `priority`
- `explanation`
- `next_action`
- `blocking_items`
- `dependencies`
- `source_ids`
- `guidance_cards`
- `confidence`

Example status values:

- `done`
- `ready`
- `in_progress`
- `blocked`
- `urgent`
- `future`
- `unknown`
- `not_relevant`

Example blocker values:

- `bank_account_missing`
- `rib_missing`
- `permanent_housing_missing`
- `rental_contract_missing`
- `visa_not_validated`
- `certificat_scolarite_missing`
- `visa_expiry_date_unknown`

## Recommendation Cards

Recommendation cards are stored in the database and attached to roadmap steps by:

- roadmap step ID;
- blocker key;
- roadmap scope;
- locale;
- priority.

Example recommendation card for a missing bank account:

```json
{
  "step_id": "bank_rib",
  "blocker_key": "bank_account_missing",
  "scope": "caf",
  "title": "Prepare for a French bank appointment",
  "why_it_matters": "A French bank account and RIB are often needed for rent, subscriptions, health reimbursements, wages, and CAF-related payments.",
  "documents": [
    "Passport or identity document",
    "Proof of residence",
    "Certificate of enrolment or student card"
  ],
  "suggested_actions": [
    "Ask your university international office whether it has partner banks or onboarding days.",
    "Prepare the required documents before booking or visiting a bank branch.",
    "Compare account fees before choosing a bank."
  ],
  "source_title": "Campus France - Getting a bank account",
  "source_url": "https://www.campusfrance.org/en/getting-a-bank-account"
}
```

This is what moves the product from a voice checklist toward a practical guidance system.

## Official Source Strategy

The app avoids pointing every recommendation to one generic source. Guidance cards use topic-specific official sources where possible.

Current source examples:

- Bank account / RIB: Campus France
- CAF housing aid: CAF
- Ameli health insurance: Ameli
- VLS-TS validation: Service-Public

The roadmap text is still a simplification. Students should always verify critical administrative details on official websites.

## Frontend Behavior

The dashboard has two main states:

1. Landing state
   - explains the product;
   - embeds the ElevenLabs widget;
   - shows what the assistant will cover.

2. Populated state
   - shows the generated roadmap;
   - shows the student profile;
   - expands each roadmap step;
   - shows practical guidance and blockers.

The frontend polls lightly for profile changes. It does not regenerate the roadmap continuously. It checks the profile periodically and only requests a new roadmap when the profile has changed.

## Local Development

### Backend

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
./.venv/bin/python -m pip install -r backend/requirements.txt
```

Start the backend:

```bash
./.venv/bin/python -m uvicorn backend.app:app --reload
```

Backend docs:

```text
http://127.0.0.1:8000/docs
```

Backend health:

```text
http://127.0.0.1:8000/health
```

### Frontend

Install frontend dependencies:

```bash
cd frontend
npm install
```

Start the dashboard:

```bash
npm run dev
```

Open:

```text
http://127.0.0.1:8501
```

## Environment Variables

Use environment variables for deployment. Do not commit real secrets.

Backend:

```text
DATABASE_URL=postgresql://...
CIVICAID_TOOL_TOKEN=your-random-secret
```

Frontend:

```text
VITE_CIVICAID_API_BASE_URL=https://civicaid-etudiant-api.onrender.com
VITE_ELEVENLABS_AGENT_ID=agent_...
```

Optional local/demo controls:

```text
VITE_CIVICAID_STUDENT_ID=demo_001 # optional fixed test profile; omit in production for per-browser student ids
VITE_DEMO_PRELOADED=false
VITE_FORCE_LANDING_PAGE=false
```

If `VITE_CIVICAID_STUDENT_ID` is omitted, the dashboard creates a browser-local student id and passes it to the ElevenLabs widget as a dynamic variable. This prevents public visitors from all loading the shared `demo_001` profile. For manual QA, open the dashboard with `?new_student=1` to reset the current browser to a fresh generated student id.

Important note:

Do not put private API keys or backend secrets in `VITE_*` variables. Vite embeds those values into the browser bundle.

## ElevenLabs Configuration Notes

In ElevenLabs, the agent needs:

- the deployed frontend host added to the agent security allowlist;
- server tools pointing to the FastAPI backend;
- optional `X-CivicAid-Tool-Token` header if `CIVICAID_TOOL_TOKEN` is enabled;
- a system prompt that tells the agent to ask one question at a time;
- tool descriptions that map conversation facts to structured fields;
- a workflow that routes out-of-scope users away from the full intake;
- a final tool call to generate the roadmap.

The frontend embeds the widget with:

```html
<elevenlabs-convai agent-id="agent_..."></elevenlabs-convai>
<script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async type="text/javascript"></script>
```

In this project, the React app loads the widget script and passes dynamic variables such as:

```json
{
  "student_id": "{{student_id}}",
  "api_base_url": "https://civicaid-etudiant-api.onrender.com",
  "product_context": "CivicAid Étudiant student dashboard"
}
```

## Deployment

This repo includes a Render Blueprint in `render.yaml`.

It provisions:

- `civicaid-etudiant-api`: FastAPI backend;
- `civicaid-etudiant-dashboard`: React static site;
- `civicaid-etudiant-db`: PostgreSQL database.

Deployment flow:

1. Push the repo to GitHub.
2. Create a Render Blueprint from the repo.
3. Set backend environment variables.
4. Set frontend environment variables.
5. Configure ElevenLabs agent tools to call the backend Render URL.
6. Add the frontend Render domain to the ElevenLabs security allowlist.
7. Test the workflow in ElevenLabs and then test the public dashboard.

## Testing Without ElevenLabs Tokens

The project can be tested without using voice minutes by simulating tool calls in Swagger.

Open:

```text
https://civicaid-etudiant-api.onrender.com/docs
```

Then call:

```text
POST /tools/update-scope-profile
POST /tools/update-arrival-visa-profile
POST /tools/update-university-profile
POST /tools/update-ameli-profile
POST /tools/update-bank-profile
POST /tools/update-housing-caf-profile
POST /tools/update-renewal-profile
POST /tools/generate-arrival-roadmap
```

Then refresh the dashboard:

```text
https://civicaid-etudiant.onrender.com
```

This validates:

- backend validation;
- database persistence;
- roadmap rules;
- recommendation cards;
- frontend rendering.

The only part not covered is the live voice conversation itself.

## Automated Tests

Run backend tests:

```bash
./.venv/bin/python -m pytest -q
```

Build frontend:

```bash
cd frontend
npm run build
```

Current test coverage focuses on:

- tool endpoint payload validation;
- profile update behavior;
- roadmap generation;
- CAF-scoped roadmap behavior;
- blocker handling;
- guidance-card attachment.

## Privacy and Data Boundaries

The project intentionally avoids storing highly sensitive fields.

It does not store:

- passport numbers;
- visa numbers;
- full addresses;
- IBANs;
- bank credentials;
- social-security numbers;
- uploaded documents;
- ElevenLabs API keys.

The system stores high-level administrative readiness fields, such as whether a student has a RIB, not the RIB itself.

## Key Engineering Decisions

### Backend-owned roadmap logic

The LLM collects information, but the backend decides the roadmap. This reduces hallucination risk and makes behavior testable.

### Structured tool endpoints

Instead of one large prompt-only workflow, the agent calls typed backend endpoints. This makes each part of the intake easier to debug.

### Partial profile updates

Each tool call updates only the fields it knows. Empty values do not erase existing data.

### Scope-aware roadmap generation

The roadmap can be generated as `full` or `caf`. This matters because a student who asks about CAF should not be forced through unrelated future steps.

### Database-backed guidance

Recommendations are stored in the database rather than hardcoded only in the frontend. This makes it easier to update guidance content without redesigning the dashboard.

### Official source links

Each guidance card can point to a relevant official source. This is important because administrative advice changes over time.

### Lightweight frontend refresh

The dashboard checks for profile changes and only regenerates the roadmap when needed. This avoids excessive backend calls.

## Challenges and Learnings

### 1. Voice workflows need stricter structure than chat workflows

Voice conversations are less forgiving than text forms. If the agent repeats itself, asks too many unrelated questions, or fails to recover from tool errors, the experience breaks quickly.

The solution was to keep nodes focused, ask one question at a time, and let the backend own structured state.

### 2. Tool validation needs to tolerate real agent behavior

Early tool calls produced `422` validation errors because voice agents may send partial fields, empty strings, or extra metadata.

The backend now uses tolerant request models for ElevenLabs tool calls:

- ignore unknown fields;
- convert empty strings to `None`;
- preserve existing data when a field is omitted.

### 3. A roadmap is more useful than a checklist only if it explains dependencies

Simply saying "Create a bank account" is not enough. The useful part is explaining why it matters, what documents to prepare, and how it affects other steps like CAF.

This led to the guidance-card layer.

### 4. Scope matters

If a student asks about CAF, they still need prerequisite questions about housing, RIB, and residence/insurance readiness. But the system should avoid unrelated future topics unless the student asks for them.

This led to `roadmap_scope`.

### 5. Frontend polling can become noisy

The first dashboard version refreshed too aggressively and generated repeated backend calls. The current version polls more lightly and only regenerates the roadmap when the profile changes.

### 6. Source quality matters

Not every topic should point to Campus France. CAF guidance should point to CAF, Ameli guidance should point to Ameli, and VLS-TS validation should point to an official government/service page.

## Current Limitations

This is still a prototype and should not be treated as an official administrative system.

Current limitations:

- The assistant does not submit official applications.
- It does not guarantee CAF, Ameli, university, or immigration eligibility.
- It does not calculate exact CAF benefit amounts.
- It does not inspect uploaded documents.
- It does not handle every visa/residence situation.
- It currently focuses on English-language guidance.
- It uses a simple polling strategy rather than real-time push updates.
- It depends on correct ElevenLabs workflow configuration.
- Recommendation content must be maintained as official rules and sources change.

## Future Improvements

Possible next steps:

- Add user authentication and per-user profiles.
- Replace polling with a webhook or real-time event after the voice call ends.
- Add an admin interface to edit guidance cards.
- Add source versioning and review dates.
- Add richer CAF-specific eligibility guidance.
- Add multilingual support for French and other languages.
- Add document checklist export.
- Add calendar reminders for deadlines.
- Add better failure recovery for voice tool calls.
- Add observability for agent tool-call failures.
- Add stricter production CORS settings.

## Repository Structure

```text
backend/
  app.py                         FastAPI app and tool endpoints
  storage.py                     SQLite/PostgreSQL persistence and guidance seeding
  models/
    student_profile.py           Student profile schema
    roadmap.py                   Roadmap and guidance schemas
  services/
    roadmap_engine.py            Roadmap rules and blocker logic
    deadline_calculator.py       Renewal timing calculation
  tests/                         Backend tests

frontend/
  src/
    civicaid.jsx                 Main React dashboard
    styles.css                   Dashboard styling
  package.json                   Frontend dependencies and scripts

elevenlabs/
  agent_prompt.md                Agent prompt notes
  workflow_logic.md              Workflow design
  workflow_node_specs.md         Node-level blueprint
  server_tools_spec.md           Tool configuration notes
  test_scenarios.md              Manual voice testing cases

docs/
  product_spec.md
  data_model.md
  scope_boundaries.md
  user_persona.md

render.yaml                      Render deployment blueprint
```

## Status

CivicAid Étudiant is a working prototype that demonstrates:

- voice-agent intake;
- agentic workflow design;
- server-tool integration;
- structured backend state;
- database persistence;
- deterministic roadmap generation;
- recommendation cards with official sources;
- React dashboard visualization;
- cloud deployment with frontend, backend, and database services.

It is designed as a portfolio project and proof of concept for voice-driven administrative guidance workflows.
