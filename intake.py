import re
from typing import Dict, Any, Tuple
from storage import now_ist, load_json, save_json, seed_demo_data


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        return "+91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits
    return "+" + digits if digits else ""


def detect_language(text: str, fallback: str = "en") -> str:
    if any("\u0b80" <= ch <= "\u0bff" for ch in (text or "")):
        return "ta"
    tanglish_words = {"vanakkam", "enna", "venum", "sollunga", "iruku", "bro", "sir", "epdi"}
    words = set(re.findall(r"[a-zA-Z]+", (text or "").lower()))
    if words & tanglish_words:
        return "tanglish"
    return fallback


def append_conversation(lead_id: str, direction: str, channel: str, text: str) -> None:
    convos = load_json("conversations")
    convos.append({
        "lead_id": lead_id,
        "direction": direction,
        "channel": channel,
        "text": text,
        "timestamp_ist": now_ist(),
    })
    save_json("conversations", convos)


def log_audit(event: str, lead_id: str, details: str) -> None:
    logs = load_json("audit_log")
    logs.append({
        "timestamp_ist": now_ist(),
        "event": event,
        "lead_id": lead_id,
        "details": details,
    })
    save_json("audit_log", logs)


def ingest_lead(
    name: str,
    phone: str,
    city: str,
    industry: str,
    channel: str,
    message: str,
    preferred_lang: str = "",
) -> Tuple[Dict[str, Any], bool]:
    seed_demo_data(force=False)
    leads = load_json("leads")
    norm_phone = normalize_phone(phone)
    lang = preferred_lang or detect_language(message)
    ts = now_ist()

    for lead in leads:
        if normalize_phone(lead.get("phone", "")) == norm_phone and norm_phone:
            lead["latest_message"] = message
            lead["last_contacted_ist"] = ts
            save_json("leads", leads)
            append_conversation(lead["lead_id"], "inbound", channel, message)
            log_audit("dedup_update", lead["lead_id"], f"Merged duplicate phone {norm_phone}")
            return lead, False

    new_id = f"LD-{len(leads) + 1:04d}"
    new_lead = {
        "lead_id": new_id,
        "name": name,
        "phone": norm_phone,
        "city": city,
        "industry": industry,
        "channel": channel,
        "preferred_lang": lang,
        "stage": "New",
        "followup_count": 0,
        "external_sequence_active": False,
        "last_contacted_ist": ts,
        "created_at_ist": ts,
        "latest_message": message,
    }
    leads.append(new_lead)
    save_json("leads", leads)
    append_conversation(new_id, "inbound", channel, message)
    log_audit("new_lead", new_id, f"Created from {channel} ({city})")
    return new_lead, True


if __name__ == "__main__":
    lead1, created1 = ingest_lead(
        name="Karthik Traders (Synthetic)",
        phone="9876543210",
        city="Coimbatore",
        industry="Retail",
        channel="WhatsApp",
        message="Vanakkam, WhatsApp AI bot pricing sollunga",
    )
    print("First submit -> created:", created1, "| id:", lead1["lead_id"], "| lang:", lead1["preferred_lang"])

    lead2, created2 = ingest_lead(
        name="Karthik Traders (Synthetic)",
        phone="+91 98765 43210",
        city="Coimbatore",
        industry="Retail",
        channel="WhatsApp",
        message="Can we start next week?",
    )
    print("Second submit -> created:", created2, "| id:", lead2["lead_id"], "| total leads:", len(load_json("leads")))