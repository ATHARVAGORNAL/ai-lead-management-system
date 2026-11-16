"""Restricted business tools intended for the Hermes agent to call via the API."""
from services.lead_service import get_lead, get_leads, update_lead_status

def lookup_lead_tool(email=None, lead_id=None):
    if lead_id is not None:
        lead = get_lead(int(lead_id))
        return {"found": bool(lead), "lead": lead}
    if email:
        match = next((item for item in get_leads()
                      if item["email"].lower() == email.strip().lower()), None)
        return {"found": bool(match), "lead": match}
    return {"found": False, "error": "Provide email or lead_id"}

def update_lead_status_tool(lead_id, status):
    allowed = ["New", "Contacted", "Converted", "Rejected"]
    if not isinstance(lead_id, int) or status not in allowed:
        return {"success": False, "error": "Invalid lead_id or status"}, 400
    lead = update_lead_status(lead_id, status)
    if not lead:
        return {"success": False, "error": "Lead not found"}, 404
    return {"success": True, "lead": lead}, 200
