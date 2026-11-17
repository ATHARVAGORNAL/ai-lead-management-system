# Hermes agent tools

This project exposes two restricted tools over HTTP. Configure your Hermes installation to call these endpoints using its supported HTTP or MCP tool integration.

## Tool 1: lookup_lead
- Method: GET
- URL: `http://127.0.0.1:7000/api/agent/tools/lookup-lead`
- Query: `email` OR `lead_id`
- Purpose: retrieve one lead record.

Examples:
- `/api/agent/tools/lookup-lead?email=rahul@example.com`
- `/api/agent/tools/lookup-lead?lead_id=1`

## Tool 2: update_lead_status
- Method: POST
- URL: `http://127.0.0.1:7000/api/agent/tools/update-lead-status`
- JSON body: `{"lead_id": 1, "status": "Contacted"}`
- Allowed statuses: `New`, `Contacted`, `Converted`, `Rejected`

## Agent instructions
You are a lead-management assistant. Use `lookup_lead` to retrieve lead information.
Use `update_lead_status` only when the user explicitly asks to change a lead's status.
Never invent lead records or claim an update succeeded unless the tool returns success.
Do not perform any action outside these two tools.
Ask for a lead ID or email if the target is ambiguous.
