# ElevenAgents Tool Integration Checklist

## Goal

Connect the ElevenAgents workflow to the CivicAid backend through Server Tools.

The backend owns the structured student profile, roadmap rules, blockers, priorities,
and renewal window calculation. The agent should collect facts conversationally, call
tools with structured fields, and summarize tool results in plain English.

## Public backend URL

Swagger can use:

```text
http://127.0.0.1:8000
```

ElevenAgents cloud cannot call your local `127.0.0.1` or `localhost`. For platform
testing, use a public HTTPS URL:

```text
https://YOUR_PUBLIC_BACKEND_URL
```

Examples:

- A deployed backend URL from Render, Railway, Fly.io, Heroku, etc.
- A tunnel URL from ngrok, Cloudflare Tunnel, or a similar tool.

Use that value as the base URL in every tool below.

## Recommended tools

For the visual workflow, prefer the smaller focused tools. They are easier for the
agent to call accurately than one very large update tool.

Use these first:

1. `update_scope_profile`
2. `update_arrival_visa_profile`
3. `update_university_profile`
4. `update_ameli_profile`
5. `update_bank_profile`
6. `update_housing_caf_profile`
7. `update_renewal_profile`
8. `generate_arrival_roadmap`
9. `save_call_summary`

Keep `calculate_renewal_window` optional. The roadmap generation already calculates
the renewal window when `visa_expiry_date` is saved.

## Shared configuration

For every tool:

```text
Tool type: Webhook / Server Tool
Method: POST
Content-Type: application/json
Authentication: none for local demo; add a secret header before production
```

Recommended production header:

```text
X-CivicAid-Tool-Token: <secret>
```

The backend does not enforce this yet, so add backend verification before exposing a
production URL.

## Tool: update_scope_profile

Call after identifying nationality scope and country.

```text
POST https://YOUR_PUBLIC_BACKEND_URL/tools/update-scope-profile
```

Body parameters:

```json
{
  "student_id": "demo_001",
  "nationality_category": "non_eu",
  "country": "India"
}
```

Parameter descriptions:

- `student_id`: Internal demo profile id. Use `demo_001` unless a real user id is available.
- `nationality_category`: One of `non_eu`, `eu_eea_swiss`, `french`, `unknown`.
- `country`: Student country of origin, if known.

## Tool: update_arrival_visa_profile

Call after collecting arrival and visa facts.

```text
POST https://YOUR_PUBLIC_BACKEND_URL/tools/update-arrival-visa-profile
```

Body parameters:

```json
{
  "student_id": "demo_001",
  "has_arrived": true,
  "arrival_date": "2026-09-10",
  "visa_type": "vls_ts_student",
  "visa_validated": false,
  "has_french_address": true
}
```

Parameter descriptions:

- `has_arrived`: Whether the student has arrived in France.
- `arrival_date`: Arrival date in `YYYY-MM-DD` format, if known.
- `visa_type`: One of `vls_ts_student`, `student_residence_permit`, `short_stay_visa`, `other`, `unknown`.
- `visa_validated`: Whether the VLS-TS has been validated online.
- `has_french_address`: Whether the student has a French address. Do not collect the address itself.

## Tool: update_university_profile

Call after CVEC and university registration intake.

```text
POST https://YOUR_PUBLIC_BACKEND_URL/tools/update-university-profile
```

Body parameters:

```json
{
  "student_id": "demo_001",
  "cvec_status": "not_done",
  "university_registration_status": "in_progress",
  "has_certificat_scolarite": false,
  "has_student_card": false
}
```

Parameter descriptions:

- `cvec_status`: One of `done`, `not_done`, `in_progress`, `exempt`, `unknown`.
- `university_registration_status`: One of `done`, `not_done`, `in_progress`, `exempt`, `unknown`.
- `has_certificat_scolarite`: Whether the student has a certificate of enrollment.
- `has_student_card`: Whether the student has a student card.

## Tool: update_ameli_profile

Call after asking about French health insurance registration.

```text
POST https://YOUR_PUBLIC_BACKEND_URL/tools/update-ameli-profile
```

Body parameters:

```json
{
  "student_id": "demo_001",
  "ameli_registered": false
}
```

## Tool: update_bank_profile

Call after asking about bank account and RIB.

```text
POST https://YOUR_PUBLIC_BACKEND_URL/tools/update-bank-profile
```

Body parameters:

```json
{
  "student_id": "demo_001",
  "has_bank_account": false,
  "has_rib": false
}
```

Do not collect IBAN.

## Tool: update_housing_caf_profile

Call after housing and CAF intent intake.

```text
POST https://YOUR_PUBLIC_BACKEND_URL/tools/update-housing-caf-profile
```

Body parameters:

```json
{
  "student_id": "demo_001",
  "housing_status": "temporary",
  "has_permanent_housing": false,
  "has_rental_contract": false,
  "wants_caf": true
}
```

Parameter descriptions:

- `housing_status`: One of `permanent`, `temporary`, `searching`, `unknown`.
- `has_permanent_housing`: Whether the student has stable housing.
- `has_rental_contract`: Whether the student has a rental contract or housing certificate.
- `wants_caf`: Whether the student wants to prepare for CAF housing aid.

## Tool: update_renewal_profile

Call if the student knows the visa expiry date.

```text
POST https://YOUR_PUBLIC_BACKEND_URL/tools/update-renewal-profile
```

Body parameters:

```json
{
  "student_id": "demo_001",
  "visa_expiry_date": "2027-09-09"
}
```

## Tool: generate_arrival_roadmap

Call near the end of intake, after enough profile fields are saved.

```text
POST https://YOUR_PUBLIC_BACKEND_URL/tools/generate-arrival-roadmap
```

Body parameters:

```json
{
  "student_id": "demo_001"
}
```

Use the response fields:

- `top_priority`: The top roadmap priority.
- `voice_summary`: Short summary suitable for speech.
- `roadmap.unknowns_to_resolve`: Missing facts to mention briefly.
- `roadmap.steps`: Full dashboard data; do not read every step aloud by default.

## Tool: save_call_summary

Call at the end if the student profile exists.

```text
POST https://YOUR_PUBLIC_BACKEND_URL/tools/save-call-summary
```

Body parameters:

```json
{
  "student_id": "demo_001",
  "conversation_id": "elevenagents_conversation_id_if_available",
  "summary": "The student is a non-EU student from India who arrived in France with a VLS-TS student visa. VLS-TS is not validated yet. CVEC is not done, university registration is in progress, and the student wants CAF later."
}
```

## Agent orchestration prompt add-on

Add this to the agent system prompt after the existing Tool Use section:

```text
Tool orchestration:

- Use the focused update tools as soon as a small group of facts is known.
- Do not wait until the end to save everything.
- Use `demo_001` as `student_id` for this demo unless a dynamic user id is provided.
- If the user says "I don't know", either omit that field or set the related status to `unknown`.
- Never send passport number, visa number, full address, IBAN, social security number, passwords, or uploaded documents to tools.
- After all intake sections are complete, call `generate_arrival_roadmap`.
- Treat the backend roadmap response as the source of truth for statuses, blockers, priorities, and renewal timing.
- In the final spoken answer, summarize only the top priority, major blockers, and next action. Do not read the entire roadmap unless the user asks.
- If a tool returns a validation error, ask a short clarification question for the rejected field, then retry once with corrected values.
```

## End-to-end test script

Use this test conversation in the ElevenAgents simulator:

```text
I am an Indian student. I arrived in Paris on September 10, 2026 for my master's.
I have a VLS-TS student visa, but I have not validated it yet.
I have a French address.
I have not done CVEC yet.
My university registration is in progress.
I do not have my certificat de scolarite or student card yet.
I have not registered for Ameli.
I do not have a French bank account or RIB.
I am in temporary housing, I do not have a rental contract, and I want CAF later.
My visa expires on September 9, 2027.
```

Expected tool sequence:

1. `update_scope_profile`
2. `update_arrival_visa_profile`
3. `update_university_profile`
4. `update_ameli_profile`
5. `update_bank_profile`
6. `update_housing_caf_profile`
7. `update_renewal_profile`
8. `generate_arrival_roadmap`
9. `save_call_summary`

Expected final summary:

- Top priority is VLS-TS validation.
- University registration is blocked or waiting on CVEC.
- Ameli is blocked until visa/university items are ready.
- CAF is blocked until RIB and housing proof are ready.
- Renewal is a future step.
