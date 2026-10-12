# ECHO — Early Care through Holistic Observation

**AI-assisted dementia support, caregiver assistance and care coordination prototype for ARDSICON'26 Track 04.**

ECHO is a **decision-support and care-coordination system, not a medical diagnostic system**. It combines consent-based profiles, holistic caregiver observations, an explainable XGBoost support-priority model, an ECHO Score, human review, practical interventions, recovery tracking, reminders, a Digital Help Centre and a multilingual voice-enabled Care Assistant.

## What this final demo build adds

- **Demo authentication + roles** — Caregiver, Care Team and Administrator access with a prototype bearer-session layer.
- **Consent-first profiles** — care profiles cannot be created without consent.
- **Holistic check-ins** — 12 structured indicators across memory, routine, behaviour, safety, social context, nutrition, daily living and caregiver burden.
- **XGBoost + SHAP** — support-priority prediction with visible contributing factors.
- **ECHO Score** — 0–100 support-priority indicator, explicitly separated from diagnosis or disease severity.
- **Human review gate** — significant interventions are blocked until a human accepts the relevant observation.
- **Intervention Engine** — recommended actions, planned/in-progress/completed states, follow-up dates and Better/Same/Worse outcomes.
- **Recovery Tracker** — ECHO Score trend, support-indicator trend, care journey and a **What changed?** comparison between the latest two check-ins.
- **Adaptive care loop** — intervention outcomes are visible alongside later observations so teams can continue, review or adapt support.
- **Periodic check-ins** — weekly/recurring reminder records with next-date tracking.
- **Digital Help Centre** — searchable prototype directory for professional, counselling, home-safety, caregiver, community and welfare resources by city/category.
- **Care summary export** — JSON summary for a person’s current state, previous state, interventions and human reviews.
- **Multilingual UI** — English, Tamil, Hindi, Malayalam, Telugu and Kannada.
- **Voice Care Assistant** — browser speech input/output plus cloud LLM support when configured.
- **Local AI safety fallback** — the demo remains usable for core assistant questions without an API key.
- **Accessibility** — large text and reduced motion controls.
- **Deployment-ready database option** — SQLite by default for zero-setup local demos; PostgreSQL supported through `DATABASE_URL` and Docker Compose.

## Core ECHO workflow

```text
Consent & profile
      ↓
Holistic caregiver check-in
      ↓
XGBoost support-priority assessment
      ↓
ECHO Score + SHAP explanation
      ↓
Human review
      ↓
Practical intervention
      ↓
Outcome: Better / Same / Worse
      ↓
Recovery Tracker + What changed?
      ↓
Next scheduled check-in
      ↓
Updated support coordination
```

## Tech stack

- Frontend: React + Vite + Recharts + Lucide
- Backend: FastAPI + SQLAlchemy
- Database: SQLite for local demo / PostgreSQL for deployment
- ML: XGBoost + SHAP + scikit-learn
- AI assistant: OpenAI Responses API when configured, with local safety fallback
- Voice: browser Speech Recognition + Speech Synthesis

## Run on Windows

### 1. Backend

```powershell
cd "C:\path\to\ECHO_Dementia_Support_Final\backend"
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Swagger API documentation:
`http://127.0.0.1:8000/docs`

### 2. Frontend

Open a second terminal:

```powershell
cd "C:\path\to\ECHO_Dementia_Support_Final\frontend"
npm install
npm run dev
```

Open:
`http://localhost:5173`

### 3. One-click Windows launcher

Double-click `start_windows.bat` after Python and Node.js are installed.

## Demo login

The login is intentionally lightweight for a hackathon prototype. Use any name and select a role:

- **Caregiver** — observe, assess, review and coordinate support
- **Care Team** — same plus care-team workflows
- **Administrator** — prototype full access

This is **not production authentication**. A production deployment should use Firebase/Auth0/Azure AD/another managed identity provider and persistent authorization.

## Optional OpenAI setup

The Care Assistant works without an API key using the local safety fallback. To enable open-ended cloud AI:

1. Copy `backend/.env.example` to `backend/.env`.
2. Add your `OPENAI_API_KEY`.
3. Set `OPENAI_MODEL` to a model available to your account.
4. Restart FastAPI.

The API key stays on the backend and is never placed in the React bundle.

## PostgreSQL / Docker

For deployment-like setup, the included `docker-compose.yml` starts PostgreSQL, FastAPI and the Vite frontend. Docker Desktop must be installed.

```bash
docker compose up --build
```

The backend uses the `DATABASE_URL` environment variable. If it is absent, the app falls back to SQLite for the easiest local demo.

## Model limitation — important for judging

The included XGBoost model is trained on **synthetic data**. The reported held-out accuracy is a **prototype-development metric**, not clinical accuracy. Do not describe it as dementia-detection accuracy. ECHO is not a diagnosis and the ECHO Score is not disease severity.

A real deployment would require ethically collected, expert-validated data, prospective evaluation, bias analysis, security review and clinical/organisational validation.

## Prototype resource data

The Digital Help Centre uses clearly labelled **prototype directory entries**. Phone numbers and organisations in the demo are placeholders for illustrating the workflow. They should be replaced by verified local services before real-world use.

## Key API endpoints

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/dashboard`
- `GET /api/people`
- `POST /api/people`
- `POST /api/assess`
- `POST /api/reviews`
- `POST /api/interventions`
- `PATCH /api/interventions/{id}`
- `GET /api/people/{id}/timeline`
- `GET /api/people/{id}/changes`
- `GET /api/people/{id}/summary`
- `GET /api/reminders/{person_id}`
- `POST /api/reminders`
- `PATCH /api/reminders/{id}`
- `GET /api/resources`
- `POST /api/chat`
- `GET /api/model-info`

## Responsible-use boundary

ECHO should support human decision-making rather than replace it. The interface repeatedly communicates:

> **Support-priority indicator — not a diagnosis.**

For immediate danger, serious injury, sudden major confusion or another emergency, users should seek appropriate local emergency/professional help rather than relying on the ECHO assistant.
