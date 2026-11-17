# Project Analysis: AI Lead Management System

Generated from a direct inspection of the current project at `C:/maxy/ai-lead-management-system`.

Scope and constraints followed:
- Inspected repository files and SQLite schema.
- Did not install packages.
- Did not run destructive commands.
- Did not read `.env` contents; only noted that the file exists.
- Wrote this requested report as `PROJECT_ANALYSIS.md`.

## 1. Project architecture and folder structure

### Repository overview

The project is a small local-development Flask application for collecting business leads, storing them in SQLite, optionally analyzing them with Ollama, showing them in a browser dashboard, exporting CSV, and exposing two restricted HTTP endpoints intended as Hermes agent tools.

Top-level structure observed:

```text
.
├── app.py
├── agent_tools.py
├── database.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── database/
│   └── leads.db
├── hermes/
│   └── TOOLS.md
├── n8n/
│   └── lead_google_sheets_workflow.json
├── services/
│   ├── __init__.py
│   ├── lead_service.py
│   ├── ollama_service.py
│   └── reporting_service.py
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
    └── index.html
```

Runtime/cache artifacts also exist locally:

```text
__pycache__/
database/leads.db
```

`.gitignore` excludes virtual environments, `__pycache__`, `.env`, SQLite database files, and macOS `.DS_Store` files.

### Code size snapshot

`pygount` is not installed in this environment, and the user explicitly requested no installs, so I used a local read-only Python line counter instead.

Observed text line counts:

| File | Lines |
|---|---:|
| `app.py` | 159 |
| `services/lead_service.py` | 149 |
| `services/ollama_service.py` | 54 |
| `database.py` | 43 |
| `agent_tools.py` | 21 |
| `services/reporting_service.py` | 12 |
| `services/__init__.py` | 0 |
| `templates/index.html` | 33 |
| `static/js/app.js` | 36 |
| `static/css/style.css` | 16 |
| `README.md` | 102 |
| `hermes/TOOLS.md` | 26 |
| `n8n/lead_google_sheets_workflow.json` | 97 |
| `requirements.txt` | 4 |
| `.env.example` | 3 |

By extension, excluding `.env` content:

| Extension/type | File count | Text lines observed |
|---|---:|---:|
| `.py` | 7 | 438 |
| `.md` | 2 | 128 |
| `.json` | 1 | 97 |
| `.html` | 1 | 33 |
| `.js` | 1 | 36 |
| `.css` | 1 | 16 |
| `.txt` | 1 | 4 |
| `.example` | 1 | 3 |
| `.db` | 1 | binary SQLite DB |
| `.env` | present | not inspected |

### Main architectural flow

1. `app.py` creates the Flask app, initializes the database, and defines all HTTP routes.
2. `database.py` owns the SQLite file path and connection settings.
3. `services/lead_service.py` handles lead CRUD-like operations, validation, status updates, and stats.
4. `services/ollama_service.py` calls Ollama `/api/generate` to analyze one lead.
5. `services/reporting_service.py` serializes lead dictionaries to CSV.
6. `agent_tools.py` wraps lead lookup and lead status update behavior for agent-facing endpoints.
7. `templates/index.html`, `static/js/app.js`, and `static/css/style.css` implement a minimal dashboard.
8. `n8n/lead_google_sheets_workflow.json` is a starter workflow: Google Sheets trigger -> create lead -> analyze lead.
9. `hermes/TOOLS.md` documents the two HTTP tool endpoints for Hermes.

### Important architecture observations

- The app uses a flat architecture rather than Flask Blueprints.
- Business logic is partially separated into `services/`, but `app.py` still performs analysis persistence directly with SQL in `api_analyze_lead`.
- There is no formal configuration object. Configuration is pulled ad hoc from environment variables in `ollama_service.py`, while database path and Flask host/port/debug are hardcoded.
- There is no migration system; schema creation is `CREATE TABLE IF NOT EXISTS` only.
- There is no authentication or authorization layer.
- There is no test suite in the repository.

## 2. Flask backend and API endpoints

### Flask app construction

`app.py` imports Flask, service functions, and agent tool wrappers. It creates the app globally:

- `app = Flask(__name__)`
- `initialize_database()` is called at import time.

Import-time database initialization means simply importing `app.py` can create or alter runtime state by creating the database directory/file/table. That is convenient for a starter app but is a weak production pattern.

### Route map traced from `app.py`

| Method | Endpoint | Handler | Purpose |
|---|---|---|---|
| GET | `/` | `dashboard` | Render dashboard template. |
| GET | `/api/health` | `health` | Health response. |
| POST | `/api/leads` | `api_create_lead` | Create a lead. |
| GET | `/api/leads` | `api_get_leads` | List all leads. |
| GET | `/api/leads/<int:lead_id>` | `api_get_lead` | Fetch one lead by ID. |
| POST | `/api/leads/<int:lead_id>/analyze` | `api_analyze_lead` | Run Ollama analysis and persist result. |
| PATCH | `/api/leads/<int:lead_id>/status` | `api_update_status` | Update lead status. |
| GET | `/api/stats` | `api_stats` | Return lead totals grouped by status and temperature. |
| GET | `/api/reports/leads.csv` | `api_export_csv` | Export all leads to CSV. |
| GET | `/api/agent/tools/lookup-lead` | `agent_lookup_lead` | Agent-facing lead lookup. |
| POST | `/api/agent/tools/update-lead-status` | `agent_update_status` | Agent-facing lead status update. |
| errorhandler | `404` | `not_found` | JSON 404 for `/api/*`, plain text otherwise. |

The app runs with:

```python
app.run(host="127.0.0.1", port=7000, debug=True, use_reloader=False)
```

All project documentation (README, n8n workflow, Hermes `TOOLS.md`) has been aligned to this port.

### Endpoint behavior details

#### `GET /`

Renders `templates/index.html`, which loads:

- `/static/css/style.css`
- `/static/js/app.js`

The dashboard shows stats, lead rows, an Export CSV link, and an Analyze button per lead.

#### `GET /api/health`

Returns:

```json
{"status": "success", "message": "AI Lead Management API is running"}
```

#### `POST /api/leads`

Flow:

1. Reads JSON using `request.get_json(silent=True)`.
2. Rejects non-object JSON with HTTP 400.
3. Requires these fields:
   - `name`
   - `email`
   - `phone`
   - `company`
   - `message`
4. Converts all provided values to stripped strings; missing values become empty strings.
5. Rejects missing/empty required values with HTTP 400.
6. Calls `create_lead(data)`.
7. Returns HTTP 201 with the created lead.
8. Catches `ValueError` as HTTP 400.
9. Catches `sqlite3.IntegrityError` as HTTP 409 duplicate email.

Validation in `create_lead`:

- Requires all five fields to be non-empty.
- Lowercases email.
- Uses `email_validator.validate_email(..., check_deliverability=False)`.
- Requires phone length between 7 and 20 characters.

Notable behavior:

- Phone accepts any characters as long as length is 7-20; it does not validate numeric or phone-like format.
- There is no max length validation for name/company/message, so large payloads can be stored.
- No authentication/rate limiting/CORS/CSRF protections.

#### `GET /api/leads`

Returns all leads ordered by descending `id`.

Current implementation calls `get_leads()` twice:

```python
return jsonify({"status": "success", "total": len(get_leads()), "leads": get_leads()})
```

This performs two independent database reads and may produce inconsistent `total` vs `leads` under concurrent writes.

#### `GET /api/leads/<id>`

Fetches a lead by integer ID.

- Returns HTTP 200 with lead if found.
- Returns HTTP 404 if missing.

#### `POST /api/leads/<id>/analyze`

Flow:

1. Looks up the lead.
2. Returns HTTP 404 if not found.
3. Calls `analyze_lead(lead)` in `services/ollama_service.py`.
4. If successful, directly executes SQL in `app.py` to update:
   - `temperature`
   - `requirements`
   - `business_intent`
   - `suggested_response`
   - `analysis_status='completed'`
5. Returns analysis JSON.
6. If `OllamaError` occurs, updates `analysis_status='failed'`, returns HTTP 503, and includes `lead_saved: true`.

Issues:

- SQL persistence for analysis is in the route handler, not in the service layer.
- Connection close is manually repeated and not protected by `finally`; if `commit()` fails, the connection may remain open.
- The route does not set `analysis_status='in_progress'`, so concurrent analyze requests can race.
- It does not clear old analysis fields on failure, so a lead could show stale analysis with `analysis_status='failed'` if reanalysis fails after a previous success.
- It only catches `OllamaError`; unexpected database errors or other exceptions bubble up.

#### `PATCH /api/leads/<id>/status`

Accepts JSON body:

```json
{"status": "New"}
```

Allowed statuses:

- `New`
- `Contacted`
- `Converted`
- `Rejected`

Returns updated lead or 404 if lead not found.

#### `GET /api/stats`

Returns:

```json
{
  "status": "success",
  "stats": {
    "total": 3,
    "temperature": {"Hot": 1, "Unanalysed": 2},
    "status": {"New": 3}
  }
}
```

Exact values depend on database contents. The current SQLite database row count observed during inspection was 3.

Note: code spells unanalysed with British spelling: `Unanalysed`. The dashboard only reads `Hot`, `Warm`, and `Cold`, so unanalysed count is not displayed except indirectly through total.

#### `GET /api/reports/leads.csv`

Serializes all leads to CSV with these fields:

- `id`
- `name`
- `email`
- `phone`
- `company`
- `message`
- `status`
- `temperature`
- `requirements`
- `business_intent`
- `suggested_response`
- `analysis_status`
- `created_at`

No authentication means this endpoint exposes all lead data to any caller that can reach the server.

#### `GET /api/agent/tools/lookup-lead`

Reads query args:

- `email`
- `lead_id` as int

Calls `lookup_lead_tool(email=email, lead_id=lead_id)`.

Returns HTTP 200 if `found` is truthy, else HTTP 404.

Notable bug risk:

- In direct tool code, `lookup_lead_tool` casts `lead_id` using `int(lead_id)`. The Flask route already parses `lead_id` as int, but direct internal callers can trigger `ValueError` with non-integer input.

#### `POST /api/agent/tools/update-lead-status`

Reads JSON, calls:

```python
update_lead_status_tool(data.get("lead_id"), data.get("status"))
```

Important behavior:

- The tool requires `lead_id` to already be an `int`, not a numeric string. JSON `{ "lead_id": "1" }` returns HTTP 400.
- The endpoint is unauthenticated and can mutate lead status.

### Frontend/dashboard behavior

`static/js/app.js`:

- Fetches `/api/leads` and `/api/stats` concurrently.
- Updates total/hot/warm/cold counters.
- Builds lead table rows.
- Adds an Analyze button that calls `POST /api/leads/{id}/analyze`.

Security-relevant observation:

- The code uses `innerHTML`, but it defines a local `safe()` function escaping `& < > " '`, and applies it to lead-controlled fields used in the row HTML.
- The static empty-state row uses constant HTML, not user input.
- The Analyze button uses `lead.id` without escaping in `data-id`, but `id` comes from SQLite integer primary key and the route path enforces int on creation/read paths.

Bug:

- `analyzeLead(id)` reads `event?.target` without accepting an `event` parameter. This relies on a browser-global `event`, which is non-standard/fragile and can fail in strict or some browser contexts. The click listener calls `()=>analyzeLead(lead.id)` and does not pass the event.

## 3. SQLite database schema and relationships

### Database location

`database.py` derives paths from the repository directory:

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "leads.db")
```

### Connection settings

Every connection:

- Ensures `database/` directory exists.
- Opens SQLite with `timeout=30`.
- Sets `row_factory = sqlite3.Row`.
- Enables `PRAGMA foreign_keys = ON`.
- Sets `PRAGMA busy_timeout = 30000`.

Initialization:

- Sets `PRAGMA journal_mode = WAL`.
- Creates `leads` table if absent.

### Actual schema observed from `database/leads.db`

```sql
CREATE TABLE leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    phone TEXT NOT NULL,
    company TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'New',
    temperature TEXT,
    requirements TEXT,
    business_intent TEXT,
    suggested_response TEXT,
    analysis_status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

SQLite also has:

```sql
CREATE TABLE sqlite_sequence(name,seq);
```

Indexes:

- Autoindex for unique email: `sqlite_autoindex_leads_1`

Foreign keys:

- None.

Current row count observed:

- `leads`: 3 rows.

I did not dump row contents because lead records can contain personal/contact information.

### Schema relationships

There is a single table and no relational model beyond the unique email constraint.

Logical entity:

- `leads` represents both incoming lead data and AI analysis data.

No separate tables exist for:

- status history
- analysis attempts
- agent actions/audit logs
- users/API clients
- organizations/companies
- comments/notes/follow-ups

### Data integrity gaps

The schema has no CHECK constraints for:

- allowed `status` values
- allowed `temperature` values
- allowed `analysis_status` values
- email shape
- phone length

The application enforces some of these rules, but direct DB writes or future code paths can violate them.

Recommended future constraints:

```sql
CHECK (status IN ('New', 'Contacted', 'Converted', 'Rejected'))
CHECK (temperature IS NULL OR temperature IN ('Hot', 'Warm', 'Cold'))
CHECK (analysis_status IN ('pending', 'completed', 'failed'))
```

Adding these requires a migration path, not a simple `CREATE TABLE IF NOT EXISTS` change.

## 4. Ollama integration and lead analysis workflow

### Configuration

`services/ollama_service.py` reads environment variables at import time:

```python
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT", "60"))
```

`.env.example` contains:

```text
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=60
```

Important issue:

- `python-dotenv` is listed in requirements, but the code never calls `load_dotenv()`. Running `python app.py` will not automatically load `.env` unless the runtime shell or Flask CLI loads it externally. Since the app is run as `python app.py` in README, `.env` values are likely ignored.

### Prompt and request

`analyze_lead(lead)` builds a prompt containing:

- name
- company
- message

It does not include:

- email
- phone
- existing status
- previous analysis

The prompt requests only valid JSON with exactly these keys:

- `temperature`
- `requirements`
- `business_intent`
- `suggested_response`

Temperature must be one of:

- `Hot`
- `Warm`
- `Cold`

It calls:

```python
POST {OLLAMA_URL}/api/generate
{
  "model": OLLAMA_MODEL,
  "prompt": prompt,
  "stream": false,
  "format": "json"
}
```

Timeout is `TIMEOUT_SECONDS`.

### Response handling

Flow:

1. `response.raise_for_status()` catches non-2xx HTTP status.
2. `payload = response.json()` parses Ollama response envelope.
3. `result = json.loads(payload.get("response", ""))` parses the model's generated JSON string.
4. Normalizes temperature with `.title()`.
5. Rejects any temperature outside `Hot/Warm/Cold`.
6. Requires non-empty strings for the other three fields.
7. Returns a sanitized dict.

Exceptions caught and wrapped as `OllamaError`:

- `requests.RequestException`
- `ValueError`
- `KeyError`
- `json.JSONDecodeError`

Note: `json.JSONDecodeError` subclasses `ValueError`, so listing both is redundant but harmless.

### Workflow from lead creation to analysis

Manual/API path:

1. Client posts to `POST /api/leads`.
2. App validates and stores lead with `analysis_status='pending'`.
3. Client posts to `POST /api/leads/{id}/analyze`.
4. App sends lead to Ollama.
5. On success, analysis fields are stored and `analysis_status='completed'`.
6. On failure, only `analysis_status='failed'` is stored.

Dashboard path:

1. Browser loads `/`.
2. JS fetches `/api/leads` and `/api/stats`.
3. User clicks Analyze.
4. JS posts to `/api/leads/{id}/analyze`.
5. JS refreshes dashboard.

n8n path:

1. Google Sheets Trigger polls every minute.
2. HTTP Request posts row fields to `http://127.0.0.1:7000/api/leads`.
3. HTTP Request posts to `http://127.0.0.1:7000/api/leads/{{$json.lead.id}}/analyze`.

n8n issue:

- If n8n is not on the same host/network namespace, `127.0.0.1` will point at the n8n runtime, not the Flask app.
- Duplicate lead creation returning 409 likely stops the workflow before analysis unless error handling is configured in n8n.

### Ollama integration weaknesses

- No retry/backoff for transient Ollama failures.
- No circuit breaker or async job queue; request blocks up to configured timeout.
- No prompt injection mitigation beyond output schema validation. Lead message content is inserted directly into the prompt.
- No max input length, so huge messages can create slow or expensive local inference calls.
- No observability of Ollama latency, model used, raw failure category, or analysis attempts.
- No audit trail for generated suggestions.

## 5. Agent tools and Hermes integration

### Implemented tools

`agent_tools.py` defines two Python functions:

#### `lookup_lead_tool(email=None, lead_id=None)`

Behavior:

- If `lead_id` is not `None`, converts it to int and calls `get_lead`.
- Else if `email` is provided, calls `get_leads()` and scans all leads in Python for case-insensitive email match.
- Else returns an error asking for email or lead_id.

Performance/security observations:

- Email lookup is O(n) over all leads rather than a targeted SQL query.
- It returns the full lead record, including phone and email.
- It has no caller authentication or authorization at the HTTP layer.
- Direct non-Flask callers can crash it by passing non-integer `lead_id`.

#### `update_lead_status_tool(lead_id, status)`

Behavior:

- Allows statuses: `New`, `Contacted`, `Converted`, `Rejected`.
- Requires `lead_id` to be an `int`.
- Calls `update_lead_status`.
- Returns `(result_dict, http_status_code)`.

Security observations:

- Exposed through unauthenticated HTTP endpoint.
- No audit log records which agent/user changed status.

### HTTP exposure

`app.py` exposes:

| Tool | Method | Endpoint |
|---|---|---|
| lookup lead | GET | `/api/agent/tools/lookup-lead?email=...` or `?lead_id=...` |
| update status | POST | `/api/agent/tools/update-lead-status` |

`hermes/TOOLS.md` documents these tools and includes agent instructions:

- Use lookup to retrieve lead information.
- Use update only when user explicitly asks to change status.
- Never invent lead records.
- Do not claim update success unless tool returns success.
- Ask for lead ID or email if ambiguous.

### Hermes documentation alignment

`hermes/TOOLS.md` points to:

```text
http://127.0.0.1:7000/api/agent/tools/...
```

This matches `app.py`, which runs on port 7000.

### Integration completeness

The project does not include an actual Hermes plugin, MCP server, OpenAPI spec, or tool manifest. It only provides HTTP endpoints and human documentation.

That matches README wording that says Hermes versions and tool configuration methods differ, but it means integration is not plug-and-play.

## 6. Dependencies and environment configuration

### Python dependencies

`requirements.txt`:

```text
Flask>=3.0,<4.0
requests>=2.31,<3.0
email-validator>=2.1,<3.0
python-dotenv>=1.0,<2.0
```

Dependency usage:

| Dependency | Used? | Where |
|---|---|---|
| Flask | yes | `app.py` |
| requests | yes | `services/ollama_service.py` |
| email-validator | yes | `services/lead_service.py` |
| python-dotenv | listed, but not used in code | no `load_dotenv()` call found |

### Current local interpreter/package observation

Without installing anything:

- `python3` reported Python 3.13.14 in one command context.
- `python` reported Python 3.14.9 in one command context.
- The broader session metadata says `python3=3.14.9`, `pip -> python3.10` mismatch, and `uv` installed.
- Import probes showed missing dependencies in the currently selected interpreters, especially `email_validator`, and app import failed because `email_validator` was missing.
- `uv run python` also did not provide Flask/requests/email-validator/dotenv in this repo because no project lock/venv install was performed, and installs were prohibited.

Practical implication:

- The repository has dependency declarations, but the current environment is not set up to run the app successfully without installing/syncing dependencies.

### Environment variables

Documented in `.env.example`:

- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT`

Used in code:

- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT`

Not configurable through env in code:

- Flask host (`127.0.0.1` hardcoded)
- Flask port (`7000` hardcoded)
- Flask debug mode (`True` hardcoded)
- Database path (`database/leads.db` hardcoded relative to repo)
- Allowed statuses
- CORS/auth/session/security settings

### README and runtime alignment

README setup says:

```text
python app.py
Open http://127.0.0.1:7000
```

`app.py` uses port `7000`, and the n8n workflow and Hermes docs now use port 7000 as well. The port mismatch has been resolved.

## 7. Existing bugs, security issues, and architectural weaknesses

### Confirmed bugs / correctness issues

#### 1. Port mismatch across app, README, n8n, and Hermes docs (resolved)

Evidence:

- `app.py` runs on port 7000.
- `README.md` references port 7000.
- `n8n/lead_google_sheets_workflow.json` posts to port 7000.
- `hermes/TOOLS.md` documents port 7000.

All endpoint references now agree on port 7000; this issue is closed.

#### 2. `.env` is not loaded by application code

Evidence:

- `requirements.txt` includes `python-dotenv`.
- No `load_dotenv()` call was found.
- `ollama_service.py` reads `os.getenv(...)` at import time.

Impact:

- `.env` settings may be ignored when running `python app.py`.
- Users may believe they configured Ollama but actually use defaults.

Severity: Medium.

#### 3. Runtime dependencies missing in current environment

Evidence:

- Import checks failed for `email_validator` in available interpreters.
- Importing `app.py` failed with `ModuleNotFoundError: No module named 'email_validator'`.

Impact:

- App cannot currently run in this inspected environment without dependency setup.

Severity: High for local execution, but environment-specific.

#### 4. Dashboard `analyzeLead` relies on implicit global `event`

Evidence:

`static/js/app.js`:

```javascript
async function analyzeLead(id){
  const button=event?.target;
```

The caller uses:

```javascript
tr.querySelector('button').addEventListener('click',()=>analyzeLead(lead.id));
```

Impact:

- Button disabling/text update can fail in browsers that do not expose global `event`.
- The analysis request may still work if the failure does not abort execution, but referencing an undeclared variable can throw `ReferenceError` depending on runtime semantics.

Severity: Medium.

#### 5. `GET /api/leads` queries the database twice

Evidence:

```python
return jsonify({"status": "success", "total": len(get_leads()), "leads": get_leads()})
```

Impact:

- Inefficient.
- Can produce inconsistent total/list under concurrent writes.

Severity: Low to Medium.

#### 6. Agent status endpoint rejects numeric string IDs

Evidence:

```python
if not isinstance(lead_id, int) or status not in allowed:
```

Impact:

- JSON clients or Hermes tool configs that send `{"lead_id": "1"}` instead of `{"lead_id": 1}` are rejected.

Severity: Low to Medium.

#### 7. `lookup_lead_tool` can raise on invalid direct `lead_id`

Evidence:

```python
lead = get_lead(int(lead_id))
```

Impact:

- Direct internal use with bad input can raise instead of returning a structured error. Flask query parsing avoids this for the current HTTP route.

Severity: Low.

### Security issues

#### 1. No authentication or authorization

Affected endpoints include lead list/detail/create/update/analyze, CSV export, and both agent tool endpoints.

Impact:

- Anyone who can reach the service can read lead contact data.
- Anyone who can reach the service can export all leads as CSV.
- Anyone who can reach the service can mutate lead status.
- Anyone who can reach the service can trigger Ollama analysis workloads.

Severity: Critical if exposed beyond localhost; acceptable only for local prototype use.

#### 2. Debug mode enabled

Evidence:

```python
debug=True
```

The app binds to `127.0.0.1`, which reduces exposure, but debug mode should not be hardcoded.

Severity: Medium locally; High if host binding changes.

#### 3. PII exposure

Lead records contain names, emails, phone numbers, company names, messages, and AI-generated response suggestions.

Exposed through list/detail/export/agent/dashboard paths. No masking, auth, access logging, or audit controls exist.

Severity: High if real lead data is used.

#### 4. No CSRF protections

The app uses JSON APIs and a same-origin dashboard. If authentication later uses cookies, CSRF protection will be needed for state-changing endpoints.

Severity: Low now; important for future.

#### 5. No rate limiting or input size limits

Large lead messages can bloat SQLite and Ollama prompts. Repeated analysis requests can consume local inference resources.

Severity: Medium.

#### 6. Prompt injection risk

Lead message text is embedded directly into the prompt. Output validation helps, but malicious lead text can still influence classification and generated response.

Severity: Medium.

#### 7. CSV injection risk

CSV export writes lead-controlled fields directly. Spreadsheet apps can interpret cells beginning with `=`, `+`, `-`, or `@` as formulas.

Severity: Medium.

### Architectural weaknesses

- Single-table design mixes raw lead data, status, analysis output, and analysis state.
- No migrations.
- No service boundary for analysis persistence.
- Synchronous Ollama calls happen in the request path.
- No structured logging/observability.
- No tests.
- Hermes integration is documented manually but not packaged as a plugin/MCP/OpenAPI artifact.

## 8. Recommended remediation plan

No application code was modified, but these are the recommended next changes.

### Highest priority

1. Port mismatch resolved.
   - README, n8n workflow, and Hermes `TOOLS.md` now all reference port 7000 to match `app.py`.
   - Prefer making port configurable with `APP_PORT`.

2. Load `.env` explicitly.
   - Add `from dotenv import load_dotenv` and call `load_dotenv()` before reading env vars.

3. Add authentication for non-local use.
   - At minimum, require an API token for API/agent/export endpoints.

4. Turn off hardcoded debug mode.
   - Read debug flag from env and default to false.

5. Fix current environment setup.
   - Use a consistent Python version and install/sync `requirements.txt` in a venv.

### Medium priority

6. Fix dashboard event handling.
7. Avoid duplicate `get_leads()` call.
8. Add targeted email lookup.
9. Add DB CHECK constraints and migrations.
10. Move analysis persistence into `lead_service.py`.
11. Add CSV formula escaping.
12. Add request size and field length limits.

### Longer-term architecture

13. Add analysis run history.
14. Add status history and agent audit logs.
15. Queue Ollama analysis.
16. Add tests with mocked Ollama responses.
17. Add a machine-readable Hermes integration artifact.

## 9. Verification notes

Actions actually performed:

- Listed project files with read-only shell commands.
- Searched source for Flask routes, SQLite usage, Ollama usage, Hermes/agent endpoints, config/env patterns, and security-sensitive patterns.
- Read relevant project files:
  - `app.py`
  - `database.py`
  - `agent_tools.py`
  - `services/lead_service.py`
  - `services/ollama_service.py`
  - `services/reporting_service.py`
  - `templates/index.html`
  - `static/js/app.js`
  - `static/css/style.css`
  - `requirements.txt`
  - `README.md`
  - `.env.example`
  - `.gitignore`
  - `hermes/TOOLS.md`
  - `n8n/lead_google_sheets_workflow.json`
- Inspected SQLite schema and metadata with read-only queries:
  - `sqlite_master`
  - `PRAGMA table_info(leads)`
  - `PRAGMA foreign_key_list(leads)`
  - `PRAGMA index_list(leads)`
  - `SELECT COUNT(*) FROM leads`
- Parsed `app.py` with Python AST to list routes because app import failed due missing runtime dependency.
- Verified `PROJECT_ANALYSIS.md` was written to the project root.

Limitations:

- Did not install `pygount`, despite the skill mentioning it, because the user explicitly prohibited installs and `pygount` was not present.
- Could not run Flask test-client smoke tests because the current Python environment lacks required dependencies.
- Did not inspect `.env` content to avoid reading secrets.
- Did not dump actual lead rows because they may contain personal/contact data.