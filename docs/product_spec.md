# CivicAid Étudiant — Product Specification

## Phase

Phase 1: Non-EU Student Arrival Roadmap Agent

## One-sentence product promise

CivicAid Étudiant helps non-EU students arriving in France generate a personalized administrative roadmap across VLS-TS validation, CVEC/university registration, Ameli health insurance, bank/RIB setup, housing, CAF readiness, and residence-renewal timing.

## Problem statement

Non-EU students arriving in France face a fragmented administrative journey. They often need to validate their visa, complete university registration, handle CVEC, register for health insurance, open a bank account, secure housing, prepare for CAF, and remember future residence-renewal deadlines.

The problem is not only that information is hard to find. The bigger problem is that students do not know:

- which steps apply to them;
- what order to complete them in;
- which steps are blocked by missing documents;
- what is urgent versus future;
- which official portal or source to trust;
- what to do next.

CivicAid Étudiant solves this by turning a voice conversation into a structured, personalized roadmap.

## Target user

The Phase 1 target user is a non-EU student who has recently arrived in France for higher education, usually with a VLS-TS étudiant visa.

The user may be confused about post-arrival administrative tasks and wants a clear action plan.

## Product goal

The goal of Phase 1 is to help the student answer:

> “I just arrived in France. What administrative steps do I need to complete, in what order, and what is blocking me?”

## Core workflow

1. The student starts a voice conversation.
2. The agent explains its scope and limitations.
3. The agent confirms that the student is a non-EU student.
4. The agent asks structured questions about:
   - visa type;
   - arrival date;
   - VLS-TS validation status;
   - French address;
   - CVEC status;
   - university registration status;
   - certificat de scolarité / student card;
   - Ameli registration;
   - bank account / RIB;
   - housing status;
   - rental contract;
   - interest in CAF;
   - visa expiry date.
5. The agent calls backend tools to update the student profile.
6. The backend generates a prioritized roadmap.
7. The agent summarizes the roadmap by voice.
8. The dashboard displays the roadmap, blockers, next actions, and known/unknown profile fields.
9. A post-call summary is stored for later review.

## Core modules in Phase 1

The roadmap covers seven areas:

1. VLS-TS validation
2. CVEC / university registration
3. Ameli health insurance registration
4. Bank account / RIB
5. Housing setup
6. CAF readiness, high-level only
7. Residence permit renewal reminder

## Roadmap output

Each roadmap step should include:

- title;
- status;
- priority;
- blocker, if any;
- next action;
- explanation;
- relevant official source ID;
- confidence level.

Example:

```json
{
  "step_id": "vls_ts_validation",
  "title": "Validate VLS-TS",
  "status": "urgent",
  "priority": 1,
  "blocking_items": ["visa_not_validated"],
  "next_action": "Validate your VLS-TS on the official foreigner administration portal.",
  "explanation": "This is usually one of the first steps for non-EU students arriving with a VLS-TS.",
  "source_ids": ["service_public_vls_ts", "campus_france_vls_ts"],
  "confidence": "high"
}