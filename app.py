from flask import Flask, request, jsonify, render_template, Response
from database import initialize_database, get_connection
from services.ollama_service import analyze_lead, OllamaError
from services.lead_service import create_lead, get_leads, get_lead, update_lead_status, get_stats
from services.reporting_service import leads_to_csv
from agent_tools import lookup_lead_tool, update_lead_status_tool
import sqlite3
import csv
import io

app = Flask(__name__)
initialize_database()

@app.get("/")
def dashboard():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify({"status": "success", "message": "AI Lead Management API is running"})

@app.post("/api/leads")
def api_create_lead():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400
    required = ["name", "email", "phone", "company", "message"]
    missing = [key for key in required if not isinstance(data.get(key), str) or not data[key].strip()]
    if missing:
        return jsonify({"status": "error", "message": "Missing or empty required fields", "fields": missing}), 400
    try:
        lead = create_lead(data)
        return jsonify({"status": "success", "message": "Lead created", "lead": lead}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "A lead with this email already exists"}), 409

@app.get("/api/leads")
def api_get_leads():
    return jsonify({"status": "success", "total": len(get_leads()), "leads": get_leads()})

@app.get("/api/leads/<int:lead_id>")
def api_get_lead(lead_id):
    lead = get_lead(lead_id)
    if not lead:
        return jsonify({"status": "error", "message": "Lead not found"}), 404
    return jsonify({"status": "success", "lead": lead})

@app.post("/api/leads/<int:lead_id>/analyze")
def api_analyze_lead(lead_id):
    lead = get_lead(lead_id)
    if not lead:
        return jsonify({"status": "error", "message": "Lead not found"}), 404
    try:
        analysis = analyze_lead(lead)
        conn = get_connection()
        conn.execute("""
            UPDATE leads SET temperature=?, requirements=?, business_intent=?,
            suggested_response=?, analysis_status='completed' WHERE id=?
        """, (
            analysis["temperature"], analysis["requirements"],
            analysis["business_intent"], analysis["suggested_response"], lead_id
        ))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "lead_id": lead_id, "analysis": analysis})
    except OllamaError as exc:
        conn = get_connection()
        conn.execute("UPDATE leads SET analysis_status='failed' WHERE id=?", (lead_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "error", "message": str(exc), "lead_saved": True}), 503

@app.patch("/api/leads/<int:lead_id>/status")
def api_update_status(lead_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    allowed = ["New", "Contacted", "Converted", "Rejected"]
    if status not in allowed:
        return jsonify({"status": "error", "message": f"Status must be one of: {', '.join(allowed)}"}), 400
    lead = update_lead_status(lead_id, status)
    if not lead:
        return jsonify({"status": "error", "message": "Lead not found"}), 404
    return jsonify({"status": "success", "lead": lead})

@app.get("/api/stats")
def api_stats():
    return jsonify({"status": "success", "stats": get_stats()})

@app.get("/api/reports/leads.csv")
def api_export_csv():
    content = leads_to_csv(get_leads())
    return Response(content, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=lead_report.csv"})

# Simple HTTP tools that can be exposed to Hermes through its supported HTTP/MCP tool mechanism.
@app.get("/api/agent/tools/lookup-lead")
def agent_lookup_lead():
    email = request.args.get("email")
    lead_id = request.args.get("lead_id", type=int)
    result = lookup_lead_tool(email=email, lead_id=lead_id)
    return jsonify(result), (200 if result.get("found") else 404)

@app.post("/api/agent/tools/update-lead-status")
def agent_update_status():
    data = request.get_json(silent=True) or {}
    result, code = update_lead_status_tool(data.get("lead_id"), data.get("status"))
    return jsonify(result), code

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Endpoint not found"}), 404
    return "Page not found", 404

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7000, debug=True,use_reloader=False)
