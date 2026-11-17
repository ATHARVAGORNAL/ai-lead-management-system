# AI-Powered Lead Management System

A basic lead-management project using Flask, SQLite, Ollama, n8n, Google Forms/Sheets and a Hermes agent tool interface.

## Included
- Flask REST API for creating, listing and retrieving leads.
- SQLite storage with unique email constraint to prevent duplicates.
- Input validation and JSON error responses.
- Ollama analysis endpoint for Hot/Warm/Cold classification, requirements, business intent and a suggested reply.
- Simple browser dashboard and CSV export.
- Two restricted agent tool endpoints for Hermes: lead lookup and lead status update.
- Starter n8n workflow export for Google Sheets Trigger -> Flask -> Ollama analysis.

## Requirements
- Python 3.10+
- Ollama installed and running
- n8n (local or hosted)
- Google Form linked to a Google Sheet

## Setup (Windows PowerShell)

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull llama3.2:3b
python app.py
```

Open `http://127.0.0.1:7000`.

If PowerShell blocks activation, run the commands from Command Prompt instead:
```bat
venv\\Scripts\\activate
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API health |
| POST | `/api/leads` | Create a lead |
| GET | `/api/leads` | List leads |
| GET | `/api/leads/<id>` | Get one lead |
| POST | `/api/leads/<id>/analyze` | Run Ollama analysis |
| PATCH | `/api/leads/<id>/status` | Update lead status |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/reports/leads.csv` | Export leads as CSV |
| GET | `/api/agent/tools/lookup-lead?email=...` | Hermes lookup tool |
| POST | `/api/agent/tools/update-lead-status` | Hermes status tool |

## Create a lead (PowerShell)

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:7000/api/leads `
  -ContentType "application/json" `
  -Body '{"name":"Rahul Sharma","email":"rahul@example.com","phone":"9876543210","company":"ABC Technologies","message":"We need an AI chatbot for customer support. Please share details and pricing."}'
```

Then analyze it:
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:7000/api/leads/1/analyze
```

Duplicate email returns HTTP 409. Invalid input returns HTTP 400. If Ollama is down, the lead remains saved and the analysis endpoint returns HTTP 503.

## Google Forms + n8n
1. Create a Google Form with fields named `Name`, `Email`, `Phone Number`, `Company`, `Requirement`.
2. In Google Forms, open Responses and link the form to a Google Sheet.
3. In n8n, import `n8n/lead_google_sheets_workflow.json`.
4. Configure the Google Sheets Trigger credentials, spreadsheet ID and sheet name.
5. Confirm the column names in the HTTP Request expression match your Sheet headers.
6. Make Flask reachable from n8n. `127.0.0.1` works only when n8n runs on the same machine. For n8n Cloud, use a secure tunnel or hosted HTTPS URL; do not expose Flask directly without authentication.
7. Activate the workflow and submit a test form response.

The included workflow is a starter export. Google Sheets node credentials and the exact form response column names must be configured in your n8n instance.

## Hermes
Read `hermes/TOOLS.md`. The Flask app exposes two restricted HTTP tool endpoints. Connect them to your installed Hermes environment using its supported HTTP/MCP tool mechanism. Hermes versions and tool configuration methods differ, so this project does not assume a particular Hermes configuration format.

## Gamma report
Export actual application data from `/api/reports/leads.csv`. Use the CSV and `/api/stats` results as the source data when creating the Gamma presentation. Do not use invented statistics.

## GitHub

```bash
git init
git add .
git commit -m "Initial AI lead management project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-lead-management-system.git
git push -u origin main
```

Database files, virtual environments and `.env` are excluded through `.gitignore`.

## Important limitations
- This is a local development starter, not a production deployment.
- The agent tool endpoints are not authenticated. Keep the app on localhost during development; add authentication before exposing it to a network.
- n8n workflow is an importable starting point and needs your Google credentials and sheet mapping.
- The dashboard is intentionally minimal.
