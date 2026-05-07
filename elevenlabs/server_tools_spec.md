# Server Tools Specification

## Purpose

Server tools allow the ElevenLabs agent to call the backend roadmap system.

The agent should not decide the final roadmap itself.

The backend owns:

- student profile state;
- roadmap rules;
- blocker calculation;
- priority ordering;
- renewal window calculation;
- dashboard data.

## Base URL

Development:

`http://localhost:8000`

Production later:

`https://YOUR_BACKEND_DOMAIN`

## Tool 1: update_student_profile

### Purpose

Update the student profile as facts are collected during the conversation.

### When to call

Call this after the student gives useful structured information, such as:

- nationality category;
- arrival date;
- visa type;
- visa validation status;
- CVEC status;
- Ameli status;
- bank/RIB status;
- housing status;
- CAF intent.

### Endpoint

`POST /tools/update-student-profile`

### Request body

```json
{
  "student_id": "demo_001",
  "patch": {
    "nationality_category": "non_eu",
    "country": "India",
    "has_arrived": true,
    "arrival_date": "2026-09-10",
    "visa_type": "vls_ts_student",
    "visa_validated": false
  },
  "source": "elevenlabs_agent"
}