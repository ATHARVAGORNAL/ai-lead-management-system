# Demo Script — AI-Powered Lead Management & Automation System

A practical 2–3 minute screen-recording script. Speak the narration while performing the
actions. Replace `rahul@example.com` / lead id `1` with a safe test lead if you prefer not
to show existing data on camera. **Do not display `.env`, credentials, or personal lead
information.**

## Preparation (before recording)

1. Start Ollama: `ollama serve` (or confirm it is running).
2. Start Flask: in the project folder with the venv active, run `python app.py`.
3. Confirm the server: open `http://127.0.0.1:7000/api/health` — expect
   `{"status":"success",...}`.
4. Have a terminal open for curl commands and a browser tab on the dashboard.
5. (Optional) Have n8n open with the imported workflow and your Google Form ready.

---

## 0:00–0:20 — Introduce the project and its purpose

**Narration:** "This is an AI-powered lead management system. It captures incoming leads,
stores them in SQLite, uses a local Ollama language model to classify each lead as Hot,
Warm, or Cold, and exposes a Flask API, a dashboard, an n8n automation pipeline, and two
Hermes agent tools — all running locally."

**Action:** Show the dashboard at `http://127.0.0.1:7000`.

---

## 0:20–0:45 — Show the dashboard and existing leads

**Narration:** "The dashboard shows live stats — total leads and Hot, Warm, Cold counts —
and a table of every lead with its temperature and status. Each row has an Analyze button,
and there's a CSV export."

**Action:**
- Point to the stats cards (Total / Hot / Warm / Cold).
- Scroll the lead table so the temperature pills (Hot / Warm / Cold) and statuses are
  visible.

---

## 0:45–1:15 — Demonstrate lead capture through Google Forms/Sheets and n8n

**Narration:** "Leads can be captured automatically. A Google Form feeds a Google Sheet;
n8n polls that sheet every minute, posts the row to the Flask API to create the lead, then
calls the analyze endpoint so Ollama qualifies it immediately."

**Action:**
- Switch to the n8n tab and show the three-node workflow:
  Google Sheets Trigger → Create Lead in Flask → Analyze Lead with Ollama.
- (Optional, if configured) Submit a test Google Form response, then return to the
  dashboard and click Refresh to show the new lead appear.

> If n8n is not configured on camera, show the workflow JSON node URLs
> (`http://127.0.0.1:7000/api/leads` and `.../analyze`) and explain the flow.

---

## 1:15–1:40 — Show Ollama classifying a lead as Hot, Warm, or Cold

**Narration:** "Now let's see the AI classification. I'll create a test lead with a strong
buying signal and analyze it."

**Action (terminal):**
```bash
# Create a safe test lead
curl -s -X POST http://127.0.0.1:7000/api/leads \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Lead","email":"demo_lead@example.com","phone":"9876543210","company":"Demo Corp","message":"We urgently need an AI chatbot for customer support. Please share pricing and demo availability."}'

# Capture the returned id, then analyze it (replace <id>)
curl -s -X POST http://127.0.0.1:7000/api/leads/<id>/analyze
```

**Narration:** "Ollama classified this as Hot because the message shows urgency and a
pricing/demo request, and it drafted a suggested response." Point to the `temperature`,
`requirements`, `business_intent`, and `suggested_response` fields in the JSON.

> Clean up afterward (off-camera): delete the demo lead from SQLite, or leave it if your
> instructor allows test data.

---

## 1:40–2:15 — Demonstrate Hermes: look up a lead, update its status, verify

**Narration:** "A Hermes agent can interact with leads through two restricted tools. First,
lookup_lead."

**Action (terminal) — lookup:**
```bash
curl -s 'http://127.0.0.1:7000/api/agent/tools/lookup-lead?email=rahul@example.com'
```
**Narration:** "The tool returns the full lead record with `found: true` and HTTP 200."

**Action (terminal) — update (say you are giving the explicit instruction on camera):**
```bash
curl -s -X POST http://127.0.0.1:7000/api/agent/tools/update-lead-status \
  -H "Content-Type: application/json" \
  -d '{"lead_id":1,"status":"Contacted"}'
```
**Narration:** "With an explicit instruction, I update lead 1's status to Contacted. The
tool returns `success: true` and the updated lead."

**Action (terminal) — verify:**
```bash
curl -s 'http://127.0.0.1:7000/api/agent/tools/lookup-lead?lead_id=1'
curl -s 'http://127.0.0.1:7000/api/leads/1'
```
**Narration:** "I verify through both the Hermes tool and the standard API — both now show
status Contacted, confirming the change persisted."

---

## 2:15–2:40 — Show the final result and summarize

**Narration:** "To summarize: we captured a lead, Ollama classified it as Hot, the Hermes
agent looked it up and updated its status, and we verified the change through the API and
the database. The full pipeline — Google Forms, n8n, Flask, SQLite, Ollama, and Hermes —
runs locally and was verified end-to-end with 28 out of 28 API tests passing."

**Action:**
- Show the dashboard once more (Refresh) so the updated status is visible.
- (Optional) show `submission/screenshots/07_api_verification_results.txt` for the 28/28
  result.

---

## Timing checklist

| Segment | Time | Key action |
|---|---|---|
| Intro | 0:00–0:20 | Dashboard overview |
| Dashboard + leads | 0:20–0:45 | Stats + lead table with temperatures |
| Google Forms + n8n | 0:45–1:15 | n8n workflow (and optional form submit) |
| Ollama classification | 1:15–1:40 | Create + analyze a test lead |
| Hermes tools | 1:40–2:15 | lookup → update → verify |
| Summary | 2:15–2:40 | Final dashboard + 28/28 result |

Total: ~2 minutes 40 seconds.
