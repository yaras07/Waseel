# Waseel — واصل
### A voice-first medication companion for visually impaired Saudi Arabic speakers
AI Readiness Hackathon submission.

Waseel lets a blind or low-vision patient point a phone camera at a medicine box
(or just speak the medicine's name), hear a short, warm explanation **in Saudi
dialect Arabic**, and have adherence + symptoms automatically tracked and shared
with a caregiver — with zero passwords, using biometric sign-in.

## Files in this repo

| File | What it is |
|---|---|
| `waseel_pipeline.ipynb` | **Main deliverable.** One self-contained Colab notebook: biometric sign-in, caregiver sync, OCR + voice medication logging (with spoken capture guidance), Saudi-dialect LLM explanations, TTS, auto-scheduled reminders, post-dose check-in, AI daily summary. |
| `waseel_db.py` | Standalone data layer + notifications module (JSON-backed), importable by a future Streamlit app per the Technical Architecture doc's 4-layer design. |
| `waseel_knowledge_base.json` | SFDA-grounded medication knowledge base (unchanged from what you provided). |
| `requirements.txt` | Python dependencies. |

## Running the demo (Google Colab)

1. Open `waseel_pipeline.ipynb` in Colab.
2. Upload `waseel_knowledge_base.json` to the Colab session when prompted.
3. (Optional, for a live LLM instead of DEMO_MODE) set your key:
   ```python
   import os
   os.environ["ANTHROPIC_API_KEY"] = "your-key-here"
   ```
4. Run all cells top to bottom.

**No API key? No camera? No problem for the demo.** Every external dependency
(LLM, camera, microphone, TTS) has a graceful fallback — a template-based
grounded response, a file-upload/typed-text prompt, or a text-only printout —
so the whole flow still runs end-to-end on stage even without network access
or hardware.

## Honesty note on biometrics

A browser-based Colab notebook cannot reach a phone's real Face ID / Touch ID
hardware (Secure Enclave) — only a native iOS/Android app or WebAuthn can. For
this prototype:
- **Face verification is real**: webcam capture + OpenCV face matching (demo-
  grade, not production biometric security).
- **Fingerprint is a documented stub** that simulates success after a short
  delay, standing in for a future native Touch ID / WebAuthn call.

## ITU policy alignment

- **ITU-T Y.3172** (`SRC → PP → M → SINK`): every notebook section is labeled
  with which pipeline stage it implements.
- **ITU AI Readiness 2.0** — Human Interface & AI for Inclusion: voice-first,
  Saudi-dialect-first design; the LLM only paraphrases fields already present
  in the SFDA-grounded knowledge base (no hallucinated dosages/warnings);
  biometric capture images/audio are deleted immediately after use.
- **SFDA compliance rules** (Code Block 1) are enforced, not just displayed:
  - *SFDA-REG-002 (Algorithmic Transparency)* — every AI explanation carries
    an explicit grounding/confidence flag.
  - *SFDA-REG-003 (Safety & Auditability)* — every AI recommendation,
    caregiver alert, and pairing event is written to an immutable
    `audit_log` table in the database.
- **AI-RE Toolkit** (`github.com/CrashingGuru/ITUAIReadiness`) — architecture
  choices in this repo (modular pipeline stages, grounded LLM, audit logging)
  map directly onto that toolkit's self-assessment checklist.

## What changed from the original team files

See the accompanying chat message for the full list — in short: `waseel_db.py`
gained `pairing_codes`, `scheduled_reminders`, and `audit_log` tables (plus a
`caregiver_visual_check_needed` flag on medication logs); Abrar's LLM/TTS code
was rebuilt from her PDF (the PDF text extraction had corrupted the Arabic RTL
text and some f-strings); Ghala's OCR matching was adapted to the real
`tradeName: {ar, en}` / flat-string `dosageForm` schema actually used in
`waseel_knowledge_base.json` (her original code expected a different shape).

## Known limitations for judges

- Face verification (OpenCV LBPH) is demo-grade, not a production biometric
  system.
- The `assess_risk_level()` heuristic (presence of a `warning` field →
  "high risk") is a placeholder until the team defines real SFDA/SDI
  severity scoring.
- Reminders are "fired" when the notebook calls `get_due_reminders()`; a
  production deployment would trigger real push notifications from a backend
  cron job instead.
