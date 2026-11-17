
import time

from database import get_connection
from email_validator import validate_email, EmailNotValidError

VALID_STATUSES = {"New", "Contacted", "Converted", "Rejected"}


def execute_with_retry(operation, retries=3):
    """Retry SQLite operations when the database is temporarily locked."""
    for attempt in range(retries):
        try:
            return operation()
        except Exception as exc:
            if "database is locked" not in str(exc).lower():
                raise

            if attempt == retries - 1:
                raise

            time.sleep(0.5 * (attempt + 1))


def create_lead(data):
    name = data["name"].strip()
    email = data["email"].strip().lower()
    phone = str(data["phone"]).strip()
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

    def insert():
        conn = get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO leads (name, email, phone, company, message)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, phone, company, message))

            lead_id = cursor.lastrowid
            conn.commit()

            row = conn.execute(
                "SELECT * FROM leads WHERE id = ?", (lead_id,)
            ).fetchone()

            return dict(row)

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    return execute_with_retry(insert)


def get_leads():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_lead(lead_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_lead_status(lead_id, status):
    if status not in VALID_STATUSES:
        raise ValueError("Invalid lead status")

    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE leads SET status = ? WHERE id = ?",
            (status, lead_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            return None

        row = conn.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()

        return dict(row) if row else None

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_stats():
    conn = get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM leads"
        ).fetchone()[0]

        by_temperature = {
            row["temperature"] or "Unanalysed": row["count"]
            for row in conn.execute("""
                SELECT temperature, COUNT(*) AS count
                FROM leads GROUP BY temperature
            """)
        }

        by_status = {
            row["status"]: row["count"]
            for row in conn.execute("""
                SELECT status, COUNT(*) AS count
                FROM leads GROUP BY status
            """)
        }

        return {
            "total": total,
            "temperature": by_temperature,
            "status": by_status
        }
    finally:
        conn.close()
