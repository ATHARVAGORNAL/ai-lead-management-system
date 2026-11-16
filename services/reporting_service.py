import csv
import io

def leads_to_csv(leads):
    output = io.StringIO()
    fields = ["id", "name", "email", "phone", "company", "message", "status",
              "temperature", "requirements", "business_intent", "suggested_response",
              "analysis_status", "created_at"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(leads)
    return output.getvalue()
