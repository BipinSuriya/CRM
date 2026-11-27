import json, os, socket, time, urllib.request, urllib.error
from pathlib import Path
from typing import Dict, Any
from storage import now_ist, load_json, save_json
from intake import log_audit

SYSTEM_RULES = """You are Dreamwell Technologies Sales & CRM AI Assistant.
Rules:
1. Never invent price bands. Direct pricing questions to WhatsApp +91 90805 83767.
2. Go-live timelines: "typically within 2 business days after prerequisites."
3. NAP: registered in Sathyamangalam, Tamil Nadu; operating hub in Coimbatore.
4. Reply in preferred_lang (en, ta, or tanglish).
Return ONLY JSON: intent, qualification_score (1-10), recommended_stage (Qualified or Proposal_Drafted), reply_lang, draft_reply."""


def get_gemini_key() -> str:
    p = Path(".env")
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key or "your_" in key.lower():
        raise RuntimeError("Missing GEMINI_API_KEY in .env file.")
    return key


def call_gemini(lead: Dict[str, Any]) -> Dict[str, Any]:
    key = get_gemini_key()
    model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    snap = {k: lead.get(k) for k in ("lead_id", "name", "city", "industry", "channel", "preferred_lang", "latest_message")}
    prompt = SYSTEM_RULES + "\n\nLead:\n" + json.dumps(snap, ensure_ascii=False)
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3},
    }).encode("utf-8")

    for attempt in range(1, 4):
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as e:
            code = getattr(e, "code", None)
            if (code in (429, 503) or code is None) and attempt < 3:
                print("Retrying Gemini...", e)
                time.sleep(attempt * 3)
                continue
            detail = e.read().decode("utf-8", "ignore") if hasattr(e, "read") else str(e)
            raise RuntimeError(f"Gemini error ({code}): {detail}")


def qualify_and_draft(lead_id: str) -> Dict[str, Any]:
    leads = load_json("leads")
    lead = next((x for x in leads if x.get("lead_id") == lead_id), None)
    if not lead:
        raise ValueError("Lead not found: " + lead_id)

    ai = call_gemini(lead)
    lead["stage"] = ai.get("recommended_stage", "Qualified")
    lead["ai_intent"] = ai.get("intent", "other")
    lead["ai_score"] = ai.get("qualification_score", 5)
    save_json("leads", leads)

    outbox = load_json("outbox")
    did = f"DR-{len(outbox) + 1:04d}"
    draft = {
        "draft_id": did,
        "lead_id": lead_id,
        "channel": lead.get("channel", "WhatsApp"),
        "reply_lang": ai.get("reply_lang", lead.get("preferred_lang", "en")),
        "draft_text": ai["draft_reply"],
        "status": "pending_approval",
        "created_at_ist": now_ist(),
    }
    outbox.append(draft)
    save_json("outbox", outbox)
    log_audit("ai_draft_created", lead_id, f"Draft {did} (pending_approval)")
    return draft


if __name__ == "__main__":
    d = qualify_and_draft("LD-0006")
    print("Draft ID:", d["draft_id"], "| Status:", d["status"], "| Lang:", d["reply_lang"])
    print("Draft Reply:\n", d["draft_text"])