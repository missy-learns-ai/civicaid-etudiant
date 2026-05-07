# User Persona — Phase 1

```markdown

## Primary persona

### Name

Arjun Mehta

### Profile

Arjun is a 23-year-old student from India who has recently arrived in France for a two-year master’s program in Paris.

### User segment

Non-EU international student arriving in France for long-term higher education.

### Immigration / study status

- Nationality category: non-EU
- Visa type: VLS-TS étudiant
- Program: master’s degree
- Stay duration: more than one year
- Arrival status: already arrived in France
- French administrative experience: low

### Current situation

Arjun arrived in France two weeks ago. He has temporary accommodation for the first month and is trying to understand what administrative steps he needs to complete.

He has heard about visa validation, CVEC, Ameli, CAF, RIB, and residence renewal, but he does not know which steps are urgent or which documents are needed.

### Main pain points

Arjun is confused because:

- information is spread across multiple official websites;
- many portals are in French;
- he does not know which steps depend on other steps;
- he does not know what is urgent;
- he is afraid of missing legal or administrative deadlines;
- he does not know whether he needs a French address before validating his visa;
- he does not know whether he can register for Ameli before university registration;
- he does not understand why a RIB is needed;
- he wants CAF but does not know whether he is ready.

### Jobs to be done

Arjun wants to:

1. Understand what to do after arriving in France.
2. Prioritize urgent administrative tasks.
3. Know what documents are missing.
4. Understand which tasks are blocked.
5. Avoid missing visa or residence deadlines.
6. Know when he can start Ameli and CAF processes.
7. Have a clear roadmap he can revisit later.

### Example user quote

> “I just arrived in France and everyone keeps mentioning VLS-TS, CVEC, Ameli, CAF, and RIB. I don’t know what to do first.”

### Example initial voice message

> “I’m an Indian student. I arrived in Paris two weeks ago for my master’s. I have a student visa but I don’t know what I need to do next.”

### What success looks like for this user

After using CivicAid Étudiant, Arjun should be able to say:

> “I know my next priority is validating my VLS-TS. I also know that Ameli is blocked until my university registration is complete, and CAF is not ready until I have a rental contract and RIB.”

## Secondary persona

### Name

Lucie Bernard

### Profile

Lucie works at the international student support office of a French university.

### User segment

University staff member who helps international students navigate administrative steps.

### Main pain points

Lucie receives repeated questions from students about:

- VLS-TS validation;
- CVEC;
- certificat de scolarité;
- Ameli;
- CAF;
- housing documents;
- renewal deadlines.

She wants students to arrive at support meetings better prepared.

### What Lucie wants

Lucie wants:

- students to understand basic administrative sequencing;
- students to know which documents they are missing;
- fewer repeated basic questions;
- visibility into common blockers;
- better triage before students ask for human help.

### Phase 1 relevance

The secondary persona is not fully supported in Phase 1, but the product should be designed so that future phases can include a support-team dashboard.

## Demo persona for Phase 1

Use this demo profile for the first project demo:

```json
{
  "name": "Arjun",
  "country": "India",
  "nationality_category": "non_eu",
  "program": "Master's degree",
  "city": "Paris",
  "arrival_date": "2026-09-10",
  "visa_type": "vls_ts_student",
  "visa_validated": false,
  "has_french_address": true,
  "cvec_status": "not_done",
  "university_registration_status": "in_progress",
  "has_certificat_scolarite": false,
  "ameli_registered": false,
  "has_bank_account": false,
  "has_rib": false,
  "has_permanent_housing": true,
  "has_rental_contract": false,
  "wants_caf": true,
  "visa_expiry_date": "2027-09-09"
}