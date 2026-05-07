---
source_id: ameli_foreign_students
title: "The French social security registration process for foreign students"
publisher: "Ameli"
url: "https://www.ameli.fr/assure/droits-demarches/etudes-stages/etudiant/french-social-security-registration-process-foreign-students"
last_checked: "2026-05-04"
topics: ["ameli", "health_insurance", "foreign_students", "non_eu_students"]
authority: "official"
phase: "1"
---

# Ameli Registration for Foreign Students

## Summary

Non-EU students usually need to register for French health insurance through the dedicated foreign-student Ameli portal.

For the Phase 1 roadmap, Ameli should be treated as a step that depends on university registration and residence-status documentation.

## Key facts

- Foreign students register online through the dedicated Ameli foreign-student portal.
- Non-European students arriving in France must register for the French general social security system.
- Registration is free.
- Campus France indicates that non-European students should complete this after registration at their institution and after visa validation.
- Non-EU/EEA students may need to submit a residence permit or residence-status document.
- Once enrolled, students can download a provisional certificate from their personal space.
- Once the social security number is certified, students can download a final certificate and request a Vitale card.

## Roadmap implication

If `ameli_registered = true`, mark Ameli as done.

If `visa_validated = false`, mark Ameli as blocked by visa validation or residence-status documentation.

If `has_certificat_scolarite = false`, mark Ameli as blocked by university registration.

If visa validation and university registration are done, mark Ameli as ready.

## Agent phrasing

"Your Ameli registration looks blocked until your university registration and residence-status documentation are ready. Once those are ready, you can use the dedicated foreign-student Ameli portal."

## Do not say

- "You are covered right now."
- "You do not need health insurance."
- "I can register you for Ameli."
- "You definitely have all documents required."

## User questions this document should answer

- How do foreign students register for French health insurance?
- What blocks Ameli registration?
- Do I need university registration before Ameli?
- Do I need residence-status documentation?
- What happens after registration?