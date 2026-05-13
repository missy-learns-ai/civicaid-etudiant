# Workflow Logic — CivicAid Étudiant Phase 1

## Purpose

This workflow guides a non-EU student through a structured post-arrival intake and prepares the data needed to generate a personalized administrative roadmap.

The workflow is designed for:

- non-EU students;
- recently arrived in France;
- studying in higher education;
- usually holding a VLS-TS étudiant.

The workflow should feel like guided triage, not a rigid Q&A form.

## High-Level Flow

```text
Start
  ↓
N01_Disclaimer
  ↓
N02_Intent_And_Scope
  ├── out of scope → N03_Out_Of_Scope → End
  ├── CAF intent → N20_CAF_Prerequisite_Router
  ├── full roadmap intent → N04_Arrival_Status
  └── unclear intent → ask one clarification → route
```

## CAF-Focused Flow

If the user says they care about CAF, housing aid, rent support, or APL, the agent should not force the full linear intake.

It should say something like:

> Got it, you want help with CAF. I’ll ask a few prerequisite questions because CAF can depend on housing proof, a RIB, and your student or residence situation.

Then collect only the facts needed for CAF readiness:

```text
N20_CAF_Prerequisite_Router
  ↓
Confirm non-EU student + country
  ↓
Arrival status
  ↓
High-level visa/student residence status
  ↓
University proof / student status
  ↓
Ameli status if relevant
  ↓
Bank account + RIB
  ↓
Permanent housing + rental contract/housing certificate
  ↓
Confirm CAF intent
  ↓
generate_arrival_roadmap with roadmap_scope = "caf"
  ↓
N13_Final_Summary
  ↓
save_call_summary
  ↓
End
```

Do not ask for visa expiry or residence-renewal timing in the CAF-focused flow unless the user explicitly asks about renewal.

## Full Roadmap Flow

If the user asks for the full administrative journey, use the complete intake:

```text
N04_Arrival_Status
  ├── Not arrived yet → N05_Pre_Arrival_Message → N05_Pre_Arrival_Choice
  └── Already arrived → Continue
        ↓
N06_Visa_Intake
        ↓
N07_University_Intake
        ↓
N08_Ameli_Intake
        ↓
N09_Bank_RIB_Intake
        ↓
N10_Housing_CAF_Intake
        ↓
N11_Visa_Expiry_Intake
        ↓
generate_arrival_roadmap with roadmap_scope = "full"
        ↓
N13_Final_Summary
        ↓
save_call_summary
        ↓
End
```

## Tool Configuration Requirement

Every ElevenLabs server tool must pass the dashboard-provided student id:

```json
{
  "student_id": "{{student_id}}"
}
```

Do not hardcode `demo_001` in production.

The React dashboard creates a browser-local student id and passes it to the ElevenLabs widget as a dynamic variable. If the workflow tools save data under a different id, the dashboard will keep waiting and no roadmap will appear after the call.

For CAF-focused intent, call:

```json
{
  "student_id": "{{student_id}}",
  "roadmap_scope": "caf"
}
```

For full-roadmap intent, call:

```json
{
  "student_id": "{{student_id}}",
  "roadmap_scope": "full"
}
```

## Error Recovery

If a tool fails while saving an optional field, especially `visa_expiry_date`, the agent should not repeat the same question in a loop.

Use this recovery behavior:

1. Acknowledge briefly: "No problem, I’ll leave that as unknown for now."
2. Continue to roadmap generation.
3. Mention the unknown field in the final summary only if relevant.

Unknown visa expiry should not block CAF roadmap generation.
