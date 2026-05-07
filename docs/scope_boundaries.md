# Scope Boundaries — Phase 1


```markdown
# Scope Boundaries — Phase 1

## Project

CivicAid Étudiant — Non-EU Student Arrival Roadmap Agent

## Phase 1 scope summary

Phase 1 helps non-EU students arriving in France generate a personalized administrative roadmap.

The product focuses on sequencing, blockers, and next actions across the most common arrival steps.

## In scope

### User segment

Phase 1 supports:

- non-EU students;
- students arriving in France for higher education;
- students with or likely to have a VLS-TS étudiant;
- students staying longer than 3 months;
- students who need a post-arrival administrative roadmap.

### Languages

Phase 1 should primarily support English.

French administrative terms should be explained clearly in English.

Examples:

- VLS-TS
- CVEC
- certificat de scolarité
- RIB
- CAF
- Ameli
- titre de séjour

### Roadmap modules

Phase 1 includes these modules:

1. VLS-TS validation
2. CVEC / university registration
3. Ameli health insurance registration
4. Bank account / RIB
5. Housing setup
6. CAF readiness, high-level only
7. Residence permit renewal reminder

### VLS-TS validation

The agent can:

- ask whether the user has a VLS-TS étudiant;
- ask when the user arrived in France;
- ask whether the visa has been validated;
- ask whether the user has a French address;
- mark the step as urgent, done, unknown, or future;
- explain that official validation must be completed through the official portal;
- recommend official verification.

The agent cannot:

- validate the visa;
- collect visa number;
- collect passport number;
- pay the tax;
- guarantee legal status;
- provide legal advice.

### CVEC / university registration

The agent can:

- ask whether CVEC is completed;
- ask whether the student is administratively registered;
- ask whether the student has a certificat de scolarité or student card;
- identify whether university registration appears blocked;
- explain that university registration documents are dependencies for other steps.

The agent cannot:

- pay CVEC;
- connect to the CVEC portal;
- complete university registration;
- verify enrollment with a university.

### Ameli health insurance

The agent can:

- ask whether the student has registered for French health insurance;
- identify whether Ameli registration appears blocked by missing university registration or residence-status documentation;
- explain that foreign students use the dedicated Ameli registration path;
- list high-level documents likely needed.

The agent cannot:

- submit an Ameli application;
- upload documents;
- validate social security rights;
- provide medical advice.

### Bank account / RIB

The agent can:

- ask whether the student has a French bank account;
- ask whether the student has a RIB;
- explain why a RIB is useful for Ameli reimbursements, CAF, rent, and payments;
- mark the step as ready, done, or unknown.

The agent cannot:

- recommend a specific commercial bank;
- open a bank account;
- collect banking credentials;
- store IBAN or account numbers.

### Housing setup

The agent can:

- ask whether the student has permanent accommodation;
- ask whether the student has a rental contract;
- identify whether housing-related steps are blocked;
- explain that housing documents may be needed for future steps.

The agent cannot:

- verify a lease;
- review legal contract terms;
- store the full address;
- provide legal advice about rental disputes.

### CAF readiness, high-level only

The agent can:

- ask whether the student wants to apply for CAF housing aid;
- identify whether CAF preparation appears blocked by missing RIB or rental contract;
- explain that a deeper CAF readiness check will be part of a future phase;
- route the student to the official CAF process.

The agent cannot:

- calculate exact CAF amount;
- guarantee CAF eligibility;
- submit a CAF application;
- collect landlord SIRET in Phase 1;
- perform document-level CAF readiness checking in Phase 1.

### Residence renewal reminder

The agent can:

- ask for visa expiry date;
- calculate a future renewal reminder window;
- mark renewal as future;
- explain that the student should verify renewal timing officially.

The agent cannot:

- submit a renewal application;
- decide legal eligibility;
- provide legal advice;
- handle complex immigration cases.

## Out of scope

Phase 1 does not support:

- EU/EEA/Swiss students;
- French students;
- short-stay visitors;
- researchers;
- salarié visas;
- passeport talent;
- family reunification;
- asylum/refugee procedures;
- undocumented situations;
- tax filing;
- work authorization;
- internship legal rules;
- scholarship eligibility;
- CROUS housing applications;
- deep CAF eligibility;
- legal disputes;
- medical advice;
- uploading or analyzing personal documents;
- direct government portal integrations;
- automatic form submission;
- payment flows.

## Sensitive information policy

The agent should not ask for or store:

- passport number;
- visa number;
- full residential address;
- bank account number;
- IBAN;
- social security number;
- birth certificate;
- residence permit scan;
- rental contract file;
- health documents;
- tax documents;
- passwords;
- government portal credentials.

The agent may ask high-level yes/no or status questions such as:

- “Do you have a French address?”
- “Do you have a RIB?”
- “Have you validated your VLS-TS?”
- “Do you have your certificat de scolarité?”

## Allowed data to store

For Phase 1, the app may store:

```json
{
  "nationality_category": "non_eu",
  "country": "India",
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