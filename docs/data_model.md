# Data Model — CivicAid Étudiant Phase 1

## Purpose

The data model defines how CivicAid Étudiant represents a non-EU student's post-arrival administrative situation and turns it into a structured roadmap.

The model supports:

- ElevenLabs voice intake;
- backend tool calls;
- roadmap generation;
- dashboard rendering;
- post-call summary;
- future persistence.

## Core objects

Phase 1 has two main objects:

1. `StudentProfile`
2. `ArrivalRoadmap`

## 1. StudentProfile

`StudentProfile` stores the structured state collected from the voice conversation.

It intentionally avoids sensitive information.

### Stored

The system may store:

- nationality category;
- country;
- arrival date;
- visa type;
- whether VLS-TS is validated;
- whether the student has a French address;
- CVEC status;
- university registration status;
- whether the student has certificat de scolarité;
- whether the student has registered for Ameli;
- whether the student has a bank account;
- whether the student has a RIB;
- housing status;
- whether the student has a rental contract;
- whether the student wants CAF;
- visa expiry date.

### Not stored

The system must not store:

- passport number;
- visa number;
- full address;
- IBAN;
- social security number;
- uploaded documents;
- passwords;
- government portal credentials.

## StudentProfile example

```json
{
  "student_id": "demo_001",
  "nationality_category": "non_eu",
  "country": "India",
  "has_arrived": true,
  "arrival_date": "2026-09-10",
  "visa_type": "vls_ts_student",
  "visa_validated": false,
  "visa_expiry_date": "2027-09-09",
  "has_french_address": true,
  "cvec_status": "not_done",
  "university_registration_status": "in_progress",
  "has_certificat_scolarite": false,
  "has_student_card": false,
  "ameli_registered": false,
  "has_bank_account": false,
  "has_rib": false,
  "housing_status": "temporary",
  "has_permanent_housing": false,
  "has_rental_contract": false,
  "wants_caf": true,
  "profile_confidence": "medium",
  "unknown_fields": []
}