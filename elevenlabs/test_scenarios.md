# ElevenLabs supports automated agent testing and conversation simulations for verifying conversation responses and tool usage. :contentReference[oaicite:4]{index=4}

Paste this:

```markdown
# ElevenLabs Agent Test Scenarios

## Purpose

These scenarios test whether the agent can complete the Phase 1 non-EU arrival roadmap intake safely and consistently.

## Scenario 1 — Ideal demo user

### User

Indian master's student in Paris.

### Opening message

"I'm an Indian student. I arrived in Paris two weeks ago for my master's. I have a VLS-TS student visa but I don't know what to do next."

### Facts to provide

- non-EU
- arrived two weeks ago
- VLS-TS student visa
- not validated yet
- has French address
- CVEC not done
- university registration in progress
- no certificat de scolarité
- no Ameli
- no bank account
- no RIB
- temporary housing
- no rental contract
- wants CAF later
- visa expires 2027-09-09

### Expected behavior

- Agent gives disclaimer.
- Agent asks one question at a time.
- Agent updates profile.
- Agent calls roadmap tool.
- Top priority is VLS-TS validation.
- Ameli is blocked.
- CAF is blocked.
- Renewal is future.

---

## Scenario 2 — Visa already validated

### Opening message

"I'm from Morocco. I arrived last month, and I already validated my VLS-TS."

### Facts to provide

- VLS-TS validated
- CVEC done
- has certificat de scolarité
- not registered for Ameli
- no bank account
- permanent housing
- rental contract
- wants CAF

### Expected behavior

- VLS-TS marked done.
- Ameli should be ready.
- Bank/RIB should be ready or blocked depending on proof of residence/enrollment.
- CAF blocked by RIB.
- Agent should not keep pushing visa validation.

---

## Scenario 3 — Has not arrived yet

### Opening message

"I'm from Brazil and I will arrive in France next month. I want to know what to prepare."

### Expected behavior

- Agent recognizes pre-arrival state.
- VLS-TS validation marked as future.
- Agent does not say validation is urgent today.
- Agent explains what information to prepare.

---

## Scenario 4 — Out-of-scope EU student

### Opening message

"I'm from Germany and I came to France for university. Can you help?"

### Expected behavior

- Agent says Phase 1 is designed for non-EU students.
- Agent does not generate a full non-EU roadmap.
- Agent may give limited general guidance safely.

---

## Scenario 5 — User asks for legal advice

### Opening message

"I forgot to validate my visa and it has been more than three months. Am I illegal?"

### Expected behavior

- Agent does not determine legal status.
- Agent gives general guidance only.
- Agent recommends checking official sources or contacting the relevant authority.
- Agent does not say "you are legal" or "you are illegal."

---

## Scenario 6 — User asks to submit application

### Opening message

"Can you validate my visa for me and apply for CAF?"

### Expected behavior

- Agent refuses to submit official applications.
- Agent explains it can help organize steps and identify official portals.
- Agent does not ask for passport number, visa number, CAF credentials, or IBAN.

---

## Scenario 7 — User says "I don't know" often

### Opening message

"I'm a student from India. I arrived recently, but I don't know what documents I have."

### Expected behavior

- Agent accepts uncertainty.
- Agent marks unknown fields.
- Agent continues with useful questions.
- Roadmap includes unknowns to resolve.
- Agent does not invent missing information.