from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30), name="IST")
DATA_DIR = Path("data")
FILES = {
    "leads": DATA_DIR / "leads.json",
    "conversations": DATA_DIR / "conversations.json",
    "outbox": DATA_DIR / "outbox.json",
    "audit_log": DATA_DIR / "audit_log.json",
}

def now_ist():
    return datetime.now(IST).isoformat(timespec="seconds")

def load_json(key):
    path = FILES[key]
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(key, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FILES[key].write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def seed_demo_data(force=False):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for key in ("conversations", "outbox", "audit_log"):
        if force or not FILES[key].exists():
            save_json(key, [])
    if not force and FILES["leads"].exists():
        return

    now = datetime.now(IST)
    old_ts = (now - timedelta(hours=52)).isoformat(timespec="seconds")
    now_ts = now.isoformat(timespec="seconds")

    # Synthetic mock leads for local dry-run testing only
    sample_leads = [
        {"lead_id": "L001", "name": "Karthik Traders (Mock)", "phone": "+91 90000 00001", "city": "Erode", "industry": "Wholesale", "channel": "WhatsApp", "preferred_lang": "tanglish", "stage": "New", "followup_count": 0, "external_sequence_active": False, "last_contacted_ist": None, "created_at_ist": now_ts, "latest_message": "Bro WhatsApp AI bot price enna? Monthly evlo aagum?"},
        {"lead_id": "L002", "name": "Kovai Loom Works (Mock)", "phone": "+91 90000 00002", "city": "Coimbatore", "industry": "Textiles", "channel": "Website", "preferred_lang": "en", "stage": "New", "followup_count": 0, "external_sequence_active": False, "last_contacted_ist": None, "created_at_ist": now_ts, "latest_message": "Hi, we want an AI sales automation demo for our Coimbatore unit."},
        {"lead_id": "L003", "name": "Sri Murugan Hardware (Mock)", "phone": "+91 90000 00003", "city": "Salem", "industry": "Retail", "channel": "WhatsApp", "preferred_lang": "en", "stage": "Nurture", "followup_count": 1, "external_sequence_active": False, "last_contacted_ist": old_ts, "created_at_ist": old_ts, "latest_message": "Thanks, share details when free, checking with my partner."},
        {"lead_id": "L004", "name": "Metro Packaging (Mock)", "phone": "+91 90000 00004", "city": "Tiruppur", "industry": "Packaging", "channel": "WhatsApp", "preferred_lang": "tanglish", "stage": "Nurture", "followup_count": 1, "external_sequence_active": False, "last_contacted_ist": old_ts, "created_at_ist": old_ts, "latest_message": "Stop messaging please, vendaam."},
        {"lead_id": "L005", "name": "Apex Distributors (Mock)", "phone": "+91 90000 00005", "city": "Coimbatore", "industry": "Distribution", "channel": "Email", "preferred_lang": "en", "stage": "New", "followup_count": 0, "external_sequence_active": False, "last_contacted_ist": None, "created_at_ist": now_ts, "latest_message": "Give us 40% discount and confirm if you are hiring Python interns."},
    ]
    save_json("leads", sample_leads)

if __name__ == "__main__":
    seed_demo_data(force=True)
    leads = load_json("leads")
    print(f"Seeded {len(leads)} synthetic leads at {now_ist()}")