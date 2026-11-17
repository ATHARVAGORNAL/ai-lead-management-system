# AI-Powered Lead Management & Automation System

A local, end-to-end lead management system that captures incoming leads, stores them in
SQLite, uses a local Ollama LLM to classify each lead as **Hot / Warm / Cold**, exposes a
Flask REST API and a simple dashboard, automates capture through **Google Forms → Google
Sheets → n8n**, and gives a Hermes AI agent two restricted tools to look up and update leads.

> Local development starter. Not a production deployment. Keep the app on localhost;
> add authentication before exposing it to a network.

---

## 1. Project overview

The system turns incoming business enquiries into qualified, actionable leads:

- **Capture** — leads arrive via the REST API (manually, from the dashboard, or
  automatically from Google Forms through n8n).
- **Store** — every lead is saved in a SQLite database with a unique-email constraint.
- **Qualify** — an Ollama LLM reads each lead's message and returns a temperature
  (Hot / Warm / Cold), a short requirements summary, the business intent, and a
  suggested personalized reply.
- **Manage** — a minimal dashboard shows totals, per-lead temperature, status, and an
  Analyze button. Status can be updated through the API or a Hermes agent tool.
- **Export** — leads can be exported as CSV for reporting.

Everything runs locally: Flask, SQLite, and Ollama on your machine; n8n local or hosted.

## 2. Key features

- Flask REST API for creating, listing, retrieving, analyzing, and updating leads.
- SQLite storage with a case-insensitive unique-email constraint to prevent duplicates.
- Strict input validation (required fields, email format, phone length) with JSON errors.
- Ollama-powered lead analysis: Hot / Warm / Cold classification + suggested response.
- Graceful degradation — if Ollama is unavailable, the lead stays saved and the analyze
  endpoint returns HTTP 503 with `analysis_status` set to `failed`.
- Minimal dark-themed dashboard with stats cards, lead table, and per-row Analyze.
- CSV export of all leads.
- Two restricted Hermes agent tool endpoints (lookup + status update).
- Starter n8n workflow export: Google Sheets Trigger → Flask create → Flask analyze.

## 3. Technology stack

| Layer | Technology |
|---|---|
| Web framework | Flask 3.x (Python) |
| Database | SQLite 3 (WAL mode, `sqlite3` stdlib) |
| AI / LLM | Ollama (`/api/generate`, JSON mode) |
| Automation | n8n (Google Sheets Trigger + HTTP Request) |
| Lead intake | Google Forms linked to Google Sheets |
| Agent interface | Hermes (two HTTP tool endpoints) |
| Frontend | HTML + vanilla JS + CSS (no build step) |
| Validation | `email-validator` |
| Config | `python-dotenv` (`.env`) |

Python dependencies (`requirements.txt`): `Flask>=3.0,<4.0`, `requests>=2.31,<3.0`,
`email-validator>=2.1,<3.0`, `python-dotenv>=1.0,<2.0`.

## 4. System architecture

```
Google Form ──submit──> Google Sheet ──(poll)──> n8n workflow
                                                      │
                                    1) POST /api/leads          2) POST /api/leads/<id>/analyze
                                                      ▼
                                              Flask app (port 7000)
                                                      │
                                         ┌────────────┼─────────────┐
                                         ▼            ▼             ▼
                                    SQLite DB    Ollama LLM     Hermes agent
                                  (leads table)  (classify)    (lookup / update)
                                         ▲
                                         │
                            Dashboard (browser) ── /api/leads, /api/stats
```

- **Flask** is the single entrypoint: it serves the dashboard, the REST API, the CSV
  export, and the two agent tool endpoints.
- **Ollama** is an external local service called over HTTP; it is treated as fallible.
- **n8n** is an external orchestrator that polls a Google Sheet and drives two API calls.
- **Hermes** is an external agent that calls the two restricted tool endpoints.
- **SQLite** is the only persistent store; the database file is gitignored.

## 5. Project folder structure

```
ai-lead-management-system/
├── app.py                          # Flask app: routes, API, agent tools, CSV export
├── database.py                     # SQLite connection + schema initialization
├── agent_tools.py                  # Restricted Hermes tool wrappers
├── services/
│   ├── lead_service.py             # Lead CRUD, validation, stats
│   ├── ollama_service.py           # Ollama lead-qualification client
│   └── reporting_service.py        # CSV serialization
├── database/
│   └── leads.db                    # SQLite database (gitignored, created at runtime)
├── templates/
│   └── index.html                  # Dashboard page
├── static/
│   ├── css/style.css
│   └── js/app.js                   # Dashboard logic (fetch, render, analyze)
├── n8n/
│   └── lead_google_sheets_workflow.json   # Importable n8n workflow
├── hermes/
│   └── TOOLS.md                    # Hermes tool documentation
├── submission/                     # Assignment deliverables
│   ├── EVIDENCE.md
│   ├── GAMMA_REPORT.md
│   ├── DEMO_SCRIPT.md
│   └── screenshots/                # Captured evidence
├── .env.example                    # Safe configuration template (placeholders only)
├── .env                            # Real config (gitignored, never committed)
├── .gitignore
├── requirements.txt
└── README.md
```

## 6. Installation prerequisites

- **Python 3.10+**.
- **Ollama** installed and running — <https://ollama.com>. At least one model pulled
  (e.g. `ollama pull llama3.2:3b`).
- **n8n** (local or hosted) — only required for the Google Forms automation flow.
- A **Google Form** linked to a **Google Sheet** — only required for automated capture.
- **Git** for cloning/committing.
- Windows, macOS, or Linux. The setup commands below are written for Windows.

## 7. Environment configuration

Configuration is read from a `.env` file via `python-dotenv`. `load_dotenv()` is called
at the very top of `app.py`, **before** any service import, so the values below reach the
running application.

Copy the safe template and edit it:

```powershell
Copy-Item .env.example .env
```

`.env.example` contains **placeholders only** (no secrets):

```ini
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=60
```

| Variable | Purpose | Default in template |
|---|---|---|
| `OLLAMA_URL` | Base URL of the Ollama server | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model used for analysis | `llama3.2:3b` (any pulled model works) |
| `OLLAMA_TIMEOUT` | Request timeout in seconds | `60` |

> Change `OLLAMA_MODEL` to any model you have pulled with `ollama pull`. The `.env` file
> is gitignored — never commit real configuration or credentials.

## 8. Step-by-step setup (Windows)

1. Open PowerShell in the project folder.
2. Create and activate a virtual environment:
   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt instead:
   ```bat
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Create your `.env` from the template:
   ```powershell
   Copy-Item .env.example .env
   ```
5. Pull an Ollama model (if not already pulled):
   ```powershell
   ollama pull llama3.2:3b
   ```
6. Start the Flask application:
   ```powershell
   python app.py
   ```
7. Open the dashboard in your browser:
   ```
   http://127.0.0.1:7000
   ```

## 9. How to start the Flask application

From the project root, with the venv activated and Ollama running:

```powershell
python app.py
```

The server binds to `127.0.0.1` on **port 7000** (see `app.py`). Confirm it is up:

```powershell
curl http://127.0.0.1:7000/api/health
```

Expected response:
```json
{"status": "success", "message": "AI Lead Management API is running"}
```

> `debug=True` and `use_reloader=False` are set in `app.py`. This is a development server.

## 10. How to configure and run Ollama

1. Install Ollama from <https://ollama.com> and start it (it usually runs as a background
   service on `http://localhost:11434`).
2. Pull a model:
   ```powershell
   ollama pull llama3.2:3b
   ```
3. Verify Ollama is reachable:
   ```powershell
   curl http://localhost:11434/api/tags
   ```
4. Set `OLLAMA_URL`, `OLLAMA_MODEL`, and `OLLAMA_TIMEOUT` in `.env`.
5. The Flask analyze endpoint calls `POST {OLLAMA_URL}/api/generate` with
   `stream: false` and `format: "json"`, asking the model to return JSON with the keys
   `temperature`, `requirements`, `business_intent`, and `suggested_response`.

If Ollama is down or returns invalid JSON, the lead remains saved and the analyze
endpoint returns HTTP 503 with `analysis_status = "failed"`.

## 11. How to configure and run Hermes

The Flask app exposes two restricted HTTP tool endpoints intended for a Hermes agent.
Read `hermes/TOOLS.md` for the full specification.

- **Tool 1 — `lookup_lead`**
  - Method: `GET`
  - URL: `http://127.0.0.1:7000/api/agent/tools/lookup-lead`
  - Query: `email` **or** `lead_id`
  - Returns the lead record. HTTP 200 on hit, 404 when not found, 400 when neither
    parameter is supplied.
- **Tool 2 — `update_lead_status`**
  - Method: `POST`
  - URL: `http://127.0.0.1:7000/api/agent/tools/update-lead-status`
  - JSON body: `{"lead_id": 1, "status": "Contacted"}`
  - Allowed statuses: `New`, `Contacted`, `Converted`, `Rejected`.
  - HTTP 200 on success, 400 on invalid id/status, 404 when the lead does not exist.

Connect these endpoints to your Hermes installation using its supported HTTP/MCP tool
mechanism. The agent instructions in `hermes/TOOLS.md` say: use `lookup_lead` to retrieve
lead information; use `update_lead_status` only when the user explicitly asks to change a
status; never invent leads or claim success without a tool confirmation; stay within these
two tools.

> The agent tool endpoints are **not authenticated**. Keep the app on localhost during
> development and add authentication before any network exposure.

## 12. How to import and execute the n8n workflow

1. Start n8n (local or cloud).
2. In n8n, choose **Import from File** and select
   `n8n/lead_google_sheets_workflow.json`.
3. Open the **Google Sheets Trigger** node and configure:
   - Your Google Sheets credentials.
   - The spreadsheet ID (replace `REPLACE_WITH_GOOGLE_SHEET_ID`).
   - The sheet name (default `Form Responses 1`).
4. Open the **Create Lead in Flask** node and confirm the column-name expression matches
   your Sheet headers (`Name`, `Email`, `Phone Number`, `Company`, `Requirement`).
5. Confirm both HTTP Request nodes point at `http://127.0.0.1:7000` (the workflow is
   preconfigured for port 7000).
6. Make Flask reachable from n8n. `127.0.0.1` works only when n8n runs on the same
   machine. For n8n Cloud, use a secure tunnel or hosted HTTPS URL; do **not** expose
   Flask directly without authentication.
7. Activate the workflow and submit a test form response.

The workflow runs three nodes in sequence:
**Google Sheets Trigger** (poll every minute) → **Create Lead in Flask**
(`POST /api/leads`) → **Analyze Lead with Ollama**
(`POST /api/leads/<id>/analyze`).

> The included workflow is an importable starting point. Google Sheets credentials and the
> exact form-response column names must be configured in your n8n instance.

## 13. Google Forms and Google Sheets integration

1. Create a Google Form with these fields:
   - `Name`
   - `Email`
   - `Phone Number`
   - `Company`
   - `Requirement`
2. In Google Forms, open **Responses** and click **Link to Sheets** to create (or choose)
   a destination spreadsheet.
3. Note the spreadsheet ID (the long string in the Sheet URL) and the sheet tab name.
4. Import the n8n workflow as described above and wire the trigger to this sheet.
5. Submit a test response. The row appears in the Sheet, n8n polls it, posts it to Flask,
   and Flask analyzes it with Ollama.

## 14. API endpoint documentation

Base URL: `http://127.0.0.1:7000`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/leads` | Create a lead |
| GET | `/api/leads` | List all leads |
| GET | `/api/leads/<id>` | Retrieve one lead |
| POST | `/api/leads/<id>/analyze` | Run Ollama analysis |
| PATCH | `/api/leads/<id>/status` | Update lead status |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/reports/leads.csv` | Export leads as CSV |
| GET | `/api/agent/tools/lookup-lead` | Hermes tool — lookup by `email` or `lead_id` |
| POST | `/api/agent/tools/update-lead-status` | Hermes tool — update status |

All API responses use the envelope `{"status": "success" | "error", ...}`.

### Create a lead — `POST /api/leads`

Request:
```json
{
  "name": "Rahul Sharma",
  "email": "rahul@example.com",
  "phone": "9876543210",
  "company": "ABC Technologies",
  "message": "We need an AI chatbot for customer support. Please share details and pricing."
}
```

Response (HTTP 201):
```json
{
  "status": "success",
  "message": "Lead created",
  "lead": {
    "id": 1, "name": "Rahul Sharma", "email": "rahul@example.com",
    "phone": "9876543210", "company": "ABC Technologies",
    "message": "We need an AI chatbot for customer support. Please share details and pricing.",
    "status": "New", "temperature": null, "requirements": null,
    "business_intent": null, "suggested_response": null,
    "analysis_status": "pending", "created_at": "2026-11-17 03:45:14"
  }
}
```

PowerShell example:
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:7000/api/leads `
  -ContentType "application/json" `
  -Body '{"name":"Rahul Sharma","email":"rahul@example.com","phone":"9876543210","company":"ABC Technologies","message":"We need an AI chatbot for customer support. Please share details and pricing."}'
```

### List leads — `GET /api/leads`

Response (HTTP 200):
```json
{
  "status": "success",
  "total": 3,
  "leads": [ { "id": 1, "name": "Rahul Sharma", "temperature": "Hot", "status": "Contacted", "...": "..." }, "..." ]
}
```

### Retrieve one lead — `GET /api/leads/<id>`

Response (HTTP 200): the same `lead` object shown above (with analysis fields populated
after analysis). HTTP 404 when the id does not exist.

### Analyze a lead — `POST /api/leads/<id>/analyze`

No request body. Calls Ollama and persists the result.

Response (HTTP 200):
```json
{
  "status": "success",
  "lead_id": 1,
  "analysis": {
    "temperature": "Hot",
    "requirements": "AI chatbot for customer support",
    "business_intent": "Request for pricing/demo",
    "suggested_response": "Hi Rahul, thanks for considering ABC Technologies..."
  }
}
```

If Ollama is unavailable or returns invalid JSON, the lead stays saved and the response is
HTTP 503 with `{"status": "error", "message": "...", "lead_saved": true}`, and the row's
`analysis_status` is set to `failed`.

### Update status — `PATCH /api/leads/<id>/status`

Request:
```json
{ "status": "Contacted" }
```

Allowed values: `New`, `Contacted`, `Converted`, `Rejected`.
Response (HTTP 200): the updated `lead` object. HTTP 400 for an invalid status, 404 if the
lead does not exist.

### Statistics — `GET /api/stats`

Response (HTTP 200):
```json
{
  "status": "success",
  "stats": {
    "total": 3,
    "temperature": { "Hot": 1, "Warm": 1, "Cold": 1 },
    "status": { "New": 2, "Contacted": 1 }
  }
}
```

### CSV export — `GET /api/reports/leads.csv`

Returns a `text/csv` attachment (`lead_report.csv`) with columns:
`id, name, email, phone, company, message, status, temperature, requirements,
business_intent, suggested_response, analysis_status, created_at`.

### Hermes lookup tool — `GET /api/agent/tools/lookup-lead`

Query: `email` **or** `lead_id`.
```bash
curl 'http://127.0.0.1:7000/api/agent/tools/lookup-lead?email=rahul@example.com'
```
HTTP 200 + `{"found": true, "lead": {...}}` on hit; HTTP 404 + `{"found": false}` when
not found; HTTP 400 when neither parameter is supplied.

### Hermes update tool — `POST /api/agent/tools/update-lead-status`

```bash
curl -X POST http://127.0.0.1:7000/api/agent/tools/update-lead-status \
  -H "Content-Type: application/json" \
  -d '{"lead_id":1,"status":"Contacted"}'
```
HTTP 200 + `{"success": true, "lead": {...}}`; 400 for invalid `lead_id`/`status`; 404
when the lead does not exist.

## 15. SQLite database explanation

The database is a single SQLite file at `database/leads.db` (gitignored, created
automatically on first run by `initialize_database()`). The connection uses WAL journal
mode, a 30s busy timeout, and `PRAGMA foreign_keys = ON`. Write operations retry on
"database is locked".

Single table schema:

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT NOT NULL | |
| `email` | TEXT NOT NULL | `UNIQUE`, case-insensitive (`COLLATE NOCASE`) |
| `phone` | TEXT NOT NULL | Validated 7–20 chars |
| `company` | TEXT NOT NULL | |
| `message` | TEXT NOT NULL | |
| `status` | TEXT NOT NULL | Default `New`; one of New / Contacted / Converted / Rejected |
| `temperature` | TEXT | Set by Ollama: Hot / Warm / Cold |
| `requirements` | TEXT | Set by Ollama |
| `business_intent` | TEXT | Set by Ollama |
| `suggested_response` | TEXT | Set by Ollama |
| `analysis_status` | TEXT NOT NULL | Default `pending`; `completed` or `failed` after analysis |
| `created_at` | TEXT NOT NULL | SQLite `CURRENT_TIMESTAMP` (UTC) |

There are no related tables and no migrations; the schema is created with
`CREATE TABLE IF NOT EXISTS`. The unique-email constraint is what makes duplicate
creation return HTTP 409.

## 16. Lead classification workflow (Hot, Warm, Cold)

When `POST /api/leads/<id>/analyze` is called:

1. The lead record is loaded from SQLite.
2. A qualification prompt is built from the lead's `name`, `company`, and `message`
   (email and phone are **not** sent to the model).
3. The prompt instructs the model to return **only** JSON with four keys:
   `temperature`, `requirements`, `business_intent`, `suggested_response`.
4. Classification rules given to the model:
   - **Hot** — clear buying intent, urgency, or a request for pricing/demo.
   - **Warm** — the prospect shows interest but needs more information.
   - **Cold** — the message is vague, exploratory, or has no clear buying intent.
   - The model is told not to invent facts, prices, or commitments.
5. The response is parsed and validated:
   - `temperature` must be one of `Hot` / `Warm` / `Cold`.
   - The other three fields must be non-empty strings.
6. On success, the four fields are written to the row and `analysis_status` becomes
   `completed`. On any failure (network, invalid JSON, bad values), `analysis_status`
   becomes `failed` and the endpoint returns HTTP 503 — the lead itself is never lost.

## 17. Hermes tools explanation

### `lookup_lead`

- **Purpose:** retrieve a single lead record without exposing the full API.
- **Call:** `GET /api/agent/tools/lookup-lead?email=...` or `?lead_id=...`.
- **Behavior:** returns the full lead object when found (HTTP 200, `found: true`);
  HTTP 404 with `found: false` when the lead does not exist; HTTP 400 when neither
  identifier is supplied.
- **Read-only:** it never modifies data.

### `update_lead_status`

- **Purpose:** change a lead's status, scoped to that single field.
- **Call:** `POST /api/agent/tools/update-lead-status` with `{"lead_id": <int>, "status": <allowed>}`.
- **Allowed statuses:** `New`, `Contacted`, `Converted`, `Rejected`.
- **Behavior:** HTTP 200 + `success: true` + the updated lead on success; HTTP 400 when
  `lead_id` is not an integer or the status is not allowed; HTTP 404 when the lead does
  not exist.
- **Guardrails (from `hermes/TOOLS.md`):** the agent should only update status on an
  explicit user request, never invent leads, and never claim success without a tool
  confirmation.

## 18. Testing and verification results

A self-cleaning end-to-end API audit was run against the live server on port 7000. It
creates one synthetic lead, exercises every endpoint, verifies SQLite persistence
directly, then deletes only the lead it created (existing records are never touched).

Latest result: **28 / 28 tests passed**, covering:

- Create, list, retrieve (200 / 404).
- Ollama analyze + direct SQLite persistence check.
- Status update (200), invalid status (400), missing lead (404).
- Duplicate email (409), missing fields (400 + `fields[]`), invalid email (400),
  short phone (400), non-JSON body (400).
- CSV export (columns + rows) and stats aggregation.
- Hermes `lookup_lead` (200 by email, 200 by lead_id, 404 not found, 400 no params).
- Hermes `update_lead_status` (200, 400 invalid, 400 non-int id, 404 missing).

A live Hermes tool demonstration was also performed: `lookup_lead` found
`rahul@example.com`, then (with explicit authorization) `update_lead_status` changed lead
1 from `New` → `Contacted`, verified through `lookup_lead`, `GET /api/leads/1`, and a
direct SQLite read — all three agreed and confirmed persistence.

Captured evidence is in `submission/screenshots/` and described in
`submission/EVIDENCE.md`.

## 19. Troubleshooting common issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `curl: (7) Failed to connect` to port 7000 | Flask not running | Start with `python app.py` |
| Analyze returns HTTP 503 | Ollama not running, wrong model, or transient empty response | Start Ollama; check `OLLAMA_MODEL` in `.env` matches a pulled model; retry |
| Analyze returns 503 "Expecting value..." | Ollama returned empty/non-JSON | Transient — retry; confirm model with `curl http://localhost:11434/api/tags` |
| `.env` values seem ignored | Old server still running | Stop and restart Flask so `load_dotenv()` runs |
| Duplicate email returns 409 | Email already exists | Use a different email (uniqueness is by design) |
| n8n cannot reach Flask | n8n not on same host as Flask | Use a tunnel / hosted URL for remote n8n; do not expose Flask unauthenticated |
| n8n workflow posts to wrong port | Workflow not updated | Confirm both HTTP nodes use `http://127.0.0.1:7000` |
| PowerShell activation blocked | Execution policy | Run from Command Prompt: `venv\Scripts\activate` |
| Dashboard shows "No leads yet" | No leads in DB | Create one via the API or a Google Form |

## 20. Future improvements

- Make the port configurable via an `APP_PORT` environment variable.
- Add authentication (API token) for the API and agent tool endpoints.
- Add a DELETE endpoint and pagination for `GET /api/leads`.
- Add retry/backoff and observability for Ollama calls (latency, model, failure category).
- Mitigate prompt injection for lead messages before sending them to the model.
- Add database migrations instead of `CREATE TABLE IF NOT EXISTS`.
- Store timestamps as ISO-8601 with an explicit timezone.
- Replace the dev server with a production WSGI server (e.g. gunicorn/waitress).
- Add unit and integration tests to the repository.

---

## GitHub

Remote: `https://github.com/ATHARVAGORNAL/ai-lead-management-system.git`, branch `main`.

Database files, virtual environments, `.env`, and cache files are excluded via `.gitignore`.
