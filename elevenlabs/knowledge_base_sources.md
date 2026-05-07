# ElevenLabs Knowledge Base Sources

## Purpose

The ElevenLabs Knowledge Base gives the agent official-source explanations for Phase 1.

The backend roadmap engine decides roadmap statuses and blockers.

The knowledge base explains the official context behind those steps.

## Upload strategy

Upload clean Markdown files instead of raw webpages.

Reason:

- cleaner retrieval;
- less navigation noise;
- easier to update;
- easier to test;
- easier to version-control;
- better for voice-friendly answers.

## Files to upload

Upload these files from:

`data/knowledge_pack/`

1. `01_vls_ts_validation.md`
2. `02_student_residence_renewal.md`
3. `03_campus_france_arrival_checklist.md`
4. `04_cvec_university_registration.md`
5. `05_ameli_foreign_student_registration.md`
6. `06_bank_rib_setup.md`
7. `07_caf_high_level_readiness.md`

## Source registry

The canonical list of sources lives in:

`data/sources/source_registry.csv`

## RAG behavior

The knowledge base should be used for explanations, not final decision logic.

Examples:

- "What is VLS-TS validation?"
- "Why do I need CVEC?"
- "Why is Ameli blocked?"
- "Why do I need a RIB?"
- "Why is CAF not ready yet?"

The agent should call the backend roadmap tool for actual roadmap statuses.

## Knowledge base maintenance

Each Markdown file should include:

- source_id;
- title;
- publisher;
- official URL;
- last_checked date;
- topic tags;
- roadmap implication;
- do-not-say guardrails.

## Manual upload checklist

For each file:

1. Open ElevenLabs dashboard.
2. Go to the agent.
3. Open Knowledge Base / Documents.
4. Add document.
5. Upload the Markdown file.
6. Enable retrieval/RAG if required.
7. Test with 1–2 questions from `data/eval/rag_test_questions.json`.

## Important design rule

Do not upload random blogs, Reddit posts, or unofficial student guides.

Only use official or high-trust sources.