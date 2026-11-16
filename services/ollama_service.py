import json
import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT", "60"))

class OllamaError(Exception):
    pass

def analyze_lead(lead):
    prompt = f"""
You are a lead qualification assistant. Analyze this incoming business lead.
Return ONLY valid JSON with exactly these keys:
temperature (Hot, Warm, or Cold),
requirements (short string),
business_intent (short string),
suggested_response (polite personalized reply).

Use Hot when there is clear buying intent, urgency, or a request for pricing/demo.
Use Warm when the prospect shows interest but needs more information.
Use Cold when the message is vague, exploratory, or has no clear buying intent.
Do not invent facts, prices, or commitments.

Lead:
Name: {lead['name']}
Company: {lead['company']}
Message: {lead['message']}
"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                  "format": "json"},
            timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        payload = response.json()
        result = json.loads(payload.get("response", ""))
        temperature = str(result.get("temperature", "")).title()
        if temperature not in {"Hot", "Warm", "Cold"}:
            raise ValueError("Invalid lead temperature")
        for key in ("requirements", "business_intent", "suggested_response"):
            if not isinstance(result.get(key), str) or not result[key].strip():
                raise ValueError(f"Missing or invalid field: {key}")
        return {
            "temperature": temperature,
            "requirements": result["requirements"].strip(),
            "business_intent": result["business_intent"].strip(),
            "suggested_response": result["suggested_response"].strip()
        }
    except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise OllamaError(f"Lead analysis failed: {exc}") from exc
