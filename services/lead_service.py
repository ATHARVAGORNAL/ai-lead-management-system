from database import get_connection
from email_validator import validate_email, EmailNotValidError

VALID_STATUSES = {"New", "Contacted", "Converted", "Rejected"}

def create_lead(data):
    name = data["name"].strip()
    email = data["email"].strip().lower()
    phone = data["phone"].strip()
    company = data["company"].strip()
    message = data["message"].strip()

    if not all([name, email, phone, company, message]):
        raise ValueError("All lead fields are required")
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        raise ValueError("Invalid email address")
    if len(phone) < 7 or len(phone) > 20:
        raise ValueError("Phone number must be between 7 and 20 characters")

    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO leads (name, email, phone, company, message)
        VALUES (?, ?, ?, ?, ?)
    """, (name, email, phone, company, message))
    conn.commit()
    lead_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    conn.close()
    return dict(row)

def get_leads():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_lead(lead_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_lead_status(lead_id, status):
    if status not in VALID_STATUSES:
        raise ValueError("Invalid lead status")
    conn = get_connection()
    cursor = conn.execute("UPDATE leads SET status=? WHERE id=?", (status, lead_id))
    conn.commit()
    row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    conn.close()
    return dict(row) if cursor.rowcount else None

def get_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    by_temperature = {row["temperature"] or "Unanalysed": row["count"] for row in
        conn.execute("SELECT temperature, COUNT(*) AS count FROM leads GROUP BY temperature")}
    by_status = {row["status"]: row["count"] for row in
        conn.execute("SELECT status, COUNT(*) AS count FROM leads GROUP BY status")}
    conn.close()
    return {"total": total, "temperature": by_temperature, "status": by_status}
