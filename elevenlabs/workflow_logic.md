# Workflow Logic — CivicAid Étudiant Phase 1

## Purpose

This workflow guides a non-EU student through a structured post-arrival intake and prepares the data needed to generate a personalized arrival roadmap.

The workflow is designed for:

- non-EU students;
- recently arrived in France;
- studying in higher education;
- usually holding a VLS-TS étudiant.

## High-level flow

```text
Start
  ↓
Disclaimer + consent to continue
  ↓
Scope check: non-EU student?
  ├── No / EU / French → Out-of-scope response → End
  └── Yes / unsure → Continue
        ↓
Arrival status
  ├── Not arrived yet → Pre-arrival version → End or continue lightly
  └── Already arrived → Continue
        ↓
VLS-TS intake
        ↓
CVEC + university registration intake
        ↓
Ameli intake
        ↓
Bank / RIB intake
        ↓
Housing + CAF intent intake
        ↓
Visa expiry intake
        ↓
Generate roadmap tool
        ↓
Final voice summary
        ↓
End