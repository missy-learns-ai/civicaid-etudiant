---
source_id: caf_student_housing
title: "Étudiants : tout savoir sur l'aide au logement"
publisher: "CAF"
url: "https://caf.fr/allocataires/actualites/actualites-nationales/etudiants-tout-savoir-sur-l-aide-au-logement-0"
last_checked: "2026-05-04"
topics: ["caf", "housing_aid", "student_housing", "readiness"]
authority: "official"
phase: "1"
---

# CAF Housing Aid — High-Level Readiness

## Summary

CAF housing aid is included in Phase 1 only as a high-level roadmap dependency.

The Phase 1 agent should not calculate CAF benefit amounts or run a full CAF eligibility check.

The agent should only identify whether CAF preparation appears blocked by missing basic items such as housing, rental contract, or RIB.

## Key facts

- CAF provides a housing-aid simulator.
- Before starting a student housing-aid application, the student should prepare a valid email address.
- The student should prepare the rental contract or lease.
- The student should prepare a RIB with BIC/IBAN.
- The student should prepare landlord or agency contact details.
- If the landlord is a company, the student may need the SIRET number.
- The CAF app or account can be used to follow the file after submission.

## Roadmap implication

If `wants_caf = false`, mark CAF as not relevant for now.

If `wants_caf = true` and `has_permanent_housing = false`, mark CAF as blocked by housing.

If `wants_caf = true` and `has_rental_contract = false`, mark CAF as blocked by rental contract.

If `wants_caf = true` and `has_rib = false`, mark CAF as blocked by RIB.

If the student has housing, rental contract, and RIB, mark CAF as ready for deeper Phase 2 CAF readiness.

## Agent phrasing

"CAF looks relevant, but for Phase 1 I’ll only check whether you have the basic items: housing, rental contract, and RIB. A deeper CAF readiness check will be a later module."

## Do not say

- "You are eligible for CAF."
- "You will receive a specific amount."
- "I can submit your CAF application."
- "CAF will approve your case."

## User questions this document should answer

- Why is CAF blocked by RIB?
- Why is CAF blocked by rental contract?
- What basic documents should I prepare?
- Can I calculate my CAF amount here?
- What will Phase 2 cover?