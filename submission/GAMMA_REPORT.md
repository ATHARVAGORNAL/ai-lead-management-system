# Gamma Presentation Report — AI-Powered Lead Management & Automation System

> Format note: each "Slide" below is one Gamma slide. Copy the heading + body as a single
> slide. Suggested screenshots are noted where relevant and correspond to files in
> `submission/screenshots/`.

---

## Slide 1 — Project title and objective

**AI-Powered Lead Management & Automation System**

Objective: build a local, end-to-end system that captures incoming business leads,
stores them reliably, and uses a local LLM (Ollama) to automatically qualify each lead as
Hot, Warm, or Cold — then exposes the data through a REST API, a dashboard, an n8n
automation pipeline, and two restricted Hermes AI agent tools.

The system turns raw enquiries into prioritized, actionable leads without sending any
data to external clouds: Flask, SQLite, and Ollama all run on the local machine.

---

## Slide 2 — Problem statement and proposed solution

**Problem**
- Incoming leads arrive from many channels (forms, email, manual entry) with no
  consistent qualification.
- Sales teams waste time on cold enquiries and risk losing hot ones.
- Manual qualification is slow, subjective, and does not scale.

**Proposed solution**
- A single Flask service ingests leads, stores them in SQLite, and asks a local Ollama
  LLM to classify each lead and draft a suggested reply.
- Google Forms + n8n automate capture so new form responses are ingested and analyzed
  with no manual step.
- A Hermes agent can look up and update leads through two restricted, validated tools.

---

## Slide 3 — System architecture

```
Google Form → Google Sheet → n8n → Flask API (port 7000) → SQLite
                                       ↓
                                    Ollama LLM (classify Hot/Warm/Cold)
                                       ↓
                              Dashboard · CSV · Hermes agent tools
```

- **Flask** is the single entrypoint: dashboard, REST API, CSV export, and agent tools.
- **Ollama** is called over HTTP and treated as fallible (graceful 503 on failure).
- **n8n** polls a Google Sheet and drives two API calls (create + analyze).
- **Hermes** calls two restricted HTTP tool endpoints.
- **SQLite** is the only persistent store (WAL mode, unique-email constraint).

*Suggested screenshot: `01_dashboard.png` (the running application).*

---

## Slide 4 — Technology stack

| Layer | Technology |
|---|---|
| Web framework | Flask 3.x (Python) |
| Database | SQLite 3 (WAL, stdlib `sqlite3`) |
| AI / LLM | Ollama (`/api/generate`, JSON mode) |
| Automation | n8n (Google Sheets Trigger + HTTP Request) |
| Lead intake | Google Forms → Google Sheets |
| Agent interface | Hermes (two HTTP tools) |
| Frontend | HTML + vanilla JS + CSS |
| Validation | `email-validator` |
| Config | `python-dotenv` (`.env`) |

Everything runs locally; no external cloud APIs are required for the core pipeline.

---

## Slide 5 — Lead capture workflow

**Google Forms → Google Sheets → n8n → Flask API → SQLite**

1. A prospect submits a Google Form (Name, Email, Phone Number, Company, Requirement).
2. The response is written to a linked Google Sheet ("Form Responses 1").
3. An n8n **Google Sheets Trigger** polls the sheet every minute.
4. n8n posts the row to `POST /api/leads` on Flask (port 7000).
5. Flask validates the input, enforces the unique-email constraint, and stores the lead.
6. n8n then calls `POST /api/leads/<id>/analyze`, which runs Ollama and persists the
   classification back to the same SQLite row.

*Suggested screenshot: `04_n8n_workflow.png` (n8n canvas).*

---

## Slide 6 — AI lead classification

Ollama reads each lead's message and returns structured JSON:

- **temperature** — Hot / Warm / Cold
- **requirements** — short summary of what the prospect needs
- **business_intent** — the prospect's intent
- **suggested_response** — a polite, personalized reply

**Classification rules given to the model:**
- **Hot** — clear buying intent, urgency, or a request for pricing/demo.
- **Warm** — interest shown, but more information is needed.
- **Cold** — vague, exploratory, no clear buying intent.

Only the lead's name, company, and message are sent to the model (email and phone are
withheld). The model is instructed not to invent facts, prices, or commitments. If Ollama
is unavailable, the lead stays saved and `analysis_status` becomes `failed` (HTTP 503).

*Suggested screenshot: `03_ollama_analysis_result.png` or `03b_ollama_analysis.txt`.*

---

## Slide 7 — Hermes AI agent

The Flask app exposes two restricted HTTP tools for a Hermes agent:

**`lookup_lead`** (read-only)
- `GET /api/agent/tools/lookup-lead?email=...` or `?lead_id=...`
- HTTP 200 + lead record on hit; 404 when not found; 400 when no identifier is supplied.

**`update_lead_status`** (scoped write)
- `POST /api/agent/tools/update-lead-status` with `{"lead_id": <int>, "status": <allowed>}`
- Allowed statuses: New, Contacted, Converted, Rejected.
- HTTP 200 on success; 400 for invalid id/status; 404 when the lead does not exist.

Guardrails (from `hermes/TOOLS.md`): update status only on explicit user request; never
invent leads; never claim success without a tool confirmation; stay within these two tools.

*Suggested screenshot: `05_hermes_lookup_lead.txt` and `06_hermes_update_lead_status.txt`.*

---

## Slide 8 — Dashboard and lead management

The dashboard at `http://127.0.0.1:7000` provides:

- **Stats cards** — Total leads, Hot, Warm, Cold counts (live from `/api/stats`).
- **Lead table** — each lead with company, requirement, a temperature pill, status, and an
  Analyze button (live from `/api/leads`).
- **Export CSV** — downloads all leads via `/api/reports/leads.csv`.
- **Refresh** — re-fetches leads and stats.

Status can be managed through the REST API (`PATCH /api/leads/<id>/status`) or through the
Hermes `update_lead_status` tool. The dashboard is intentionally minimal and renders
client-side with vanilla JS.

*Suggested screenshot: `02_lead_list_temperatures.png`.*

---

## Slide 9 — Testing and verification

An end-to-end API audit was run against the live server on port 7000. The self-cleaning
harness creates one synthetic lead, exercises every endpoint, verifies SQLite persistence
directly, then deletes only the lead it created.

**Result: 28 / 28 tests passed**, covering:
- Create / list / retrieve (200 / 404).
- Ollama analyze + direct SQLite persistence check.
- Status update (200), invalid status (400), missing lead (404).
- Duplicate email (409), missing/invalid fields (400), non-JSON body (400).
- CSV export and stats aggregation.
- Hermes `lookup_lead` (200 / 404 / 400) and `update_lead_status` (200 / 400 / 404).

**Hermes tool demonstration (verified):**
- `lookup_lead` found `rahul@example.com` (id 1).
- With explicit authorization, `update_lead_status` changed lead 1 from New → Contacted.
- Verified through `lookup_lead`, `GET /api/leads/1`, and a direct SQLite read — all
  three agreed and confirmed persistence.

*Suggested screenshot: `07_api_verification_results.txt`.*

---

## Slide 10 — Conclusion and future scope

**Conclusion**
- A complete, local lead-management pipeline: capture → store → AI qualify → manage →
  export, with an automation layer (n8n) and an agent layer (Hermes).
- Verified end-to-end: 28/28 API tests pass, Ollama classification works, and both Hermes
  tools function with confirmed database persistence.

**Future scope**
- Configurable port via `APP_PORT`; authentication for API and agent endpoints.
- DELETE endpoint and pagination for `GET /api/leads`.
- Retry/backoff and observability for Ollama; prompt-injection mitigation.
- Database migrations; ISO-8601 timestamps; production WSGI server; committed test suite.

---

*All results in this report are supported by captured evidence in
`submission/screenshots/`. No statistics or test results were invented.*
