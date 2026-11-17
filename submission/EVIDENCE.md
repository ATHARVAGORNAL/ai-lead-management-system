# Evidence Index — AI-Powered Lead Management System

This index describes every evidence artifact in `submission/screenshots/`, what it
demonstrates, and how it was produced. All evidence was captured from the **live Flask
server on port 7000** and the **configured Ollama instance**. No screenshots were
fabricated; terminal-output files are verbatim captures of real API calls.

## Verification environment

- Flask server: `http://127.0.0.1:7000` (running from `app.py`).
- Ollama: `http://localhost:11434` (model loaded from `.env` via `load_dotenv()`).
- Database: `database/leads.db` (3 original leads; ids 1, 2, 3).
- Test data: synthetic leads only. Existing leads were never modified or deleted during
  evidence capture (lead 1's status `Contacted` is the result of the explicitly
  authorized Hermes demonstration performed earlier).

## Screenshot / evidence inventory

| # | File | Type | Demonstrates |
|---|------|------|--------------|
| 1 | `01_dashboard.png` | Browser screenshot | The AI Lead Management dashboard: title, stats cards (Total / Hot / Warm / Cold), Export CSV button, and the Leads panel. Captured by opening `http://127.0.0.1:7000/`. |
| 2 | `02_lead_list_temperatures.png` | Browser screenshot | The lead table rendered on the dashboard, showing each lead with its temperature pill (Hot / Warm / Cold) and status (New / Contacted) plus a per-row Analyze button. Captured after scrolling the dashboard to the table. Lead table content verified via DOM: Test (Cold / New), Rohan (Warm / New), Rahul Sharma (Hot / Contacted). |
| 3 | `03_ollama_analysis_result.png` | Browser screenshot | The stored Ollama analysis for lead 1, viewed at `http://127.0.0.1:7000/api/leads/1` in the browser: `temperature: Hot`, `requirements`, `business_intent`, and `suggested_response` fields populated by the LLM. |
| 3a | `03a_create_lead.txt` | Terminal output | Creation of a synthetic lead (`Evidence Lead`) via `POST /api/leads`, returned HTTP 201 with a new id. |
| 3b | `03b_ollama_analysis.txt` | Terminal output | A **live** Ollama analysis (`POST /api/leads/<id>/analyze`) on the synthetic lead using the configured model, returning `temperature: Hot`, requirements, business intent, and a suggested response. The synthetic lead was deleted immediately after capture (it was not an existing record). |
| 4 | `04_n8n_workflow.png` | **MANUAL — not captured** | The n8n workflow canvas showing the three nodes: Google Sheets Trigger → Create Lead in Flask → Analyze Lead with Ollama. See "Manual capture required" below. |
| 5 | `05_hermes_lookup_lead.txt` | Terminal output | Execution of the Hermes `lookup_lead` tool: `GET /api/agent/tools/lookup-lead?email=rahul@example.com` returning HTTP 200 with `found: true` and the full lead record. |
| 6 | `06_hermes_update_lead_status.txt` | Terminal output | Execution of the Hermes `update_lead_status` tool (explicitly authorized): `POST /api/agent/tools/update-lead-status` with `{"lead_id":1,"status":"Contacted"}` returning HTTP 200 + `success: true`, followed by verification through `lookup_lead` and `GET /api/leads/1`, both showing `status: Contacted`. |
| 7 | `07_api_verification_results.txt` | Terminal output | The full end-to-end API audit harness output: **28 / 28 tests passed, 0 failed**, covering all 10 required flows plus edge cases and both Hermes tools. The harness is self-cleaning (it deletes the synthetic lead it creates). |

## Manual capture required

`04_n8n_workflow.png` could **not** be captured automatically because n8n is not running
in this environment, and the task forbids fabricating screenshots.

To capture it yourself:

1. Start n8n and import `n8n/lead_google_sheets_workflow.json` (Import from File).
2. Open the workflow canvas so all three nodes are visible:
   - **Google Sheets Trigger**
   - **Create Lead in Flask** (HTTP Request → `http://127.0.0.1:7000/api/leads`)
   - **Analyze Lead with Ollama** (HTTP Request → `http://127.0.0.1:7000/api/leads/<id>/analyze`)
3. Take a screenshot of the canvas and save it as
   `submission/screenshots/04_n8n_workflow.png`.

If you also want a Google Forms screenshot, capture your Google Form (with the fields
Name, Email, Phone Number, Company, Requirement) and the linked Google Sheet tab
"Form Responses 1".

## Integrity notes

- Browser screenshots (`01`, `02`, `03`) were taken with a real headless browser against
  the running Flask app; the lead-table content in `02` was additionally confirmed by
  reading the rendered DOM.
- Terminal-output files (`03a`, `03b`, `05`, `06`, `07`) are verbatim captures of actual
  HTTP responses, not transcriptions.
- The database was re-verified after all evidence capture: only leads 1, 2, 3 remain; no
  existing record was deleted. The synthetic leads created during evidence capture
  (ids 6, 8, etc.) were deleted by the self-cleaning harness / explicit cleanup.
