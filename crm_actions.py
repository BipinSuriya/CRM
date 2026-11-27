import os
from typing import Dict, Any, List
from storage import now_ist, load_json, save_json
from intake import append_conversation, log_audit

DRY_RUN = os.environ.get("WHATSAPP_DRY_RUN", "true").lower() == "true"

TEMPLATES = {
    "en": "Hi {name}, checking in from Dreamwell Technologies (Coimbatore). Happy to share a demo. Pricing: WhatsApp +91 90805 83767.",
    "tanglish": "Vanakkam {name}! Dreamwell (Coimbatore) la irundhu follow-up pannrom. Demo venumna sollunga. Pricing: WhatsApp +91 90805 83767.",
    "ta": "வணக்கம் {name}, Dreamwell Technologies (Coimbatore) சார்பாக தொடர்பு கொள்கிறோம். விலை விவரங்களுக்கு WhatsApp +91 90805 83767.",
}


def approve_draft(draft_id: str, approver: str = "Vignesh") -> Dict[str, Any]:
    outbox = load_json("outbox")
    draft = next((d for d in outbox if d.get("draft_id") == draft_id), None)
    if not draft:
        raise ValueError("Draft not found: " + draft_id)
    if draft.get("status") != "pending_approval":
        raise ValueError("Already processed: " + draft.get("status", ""))

    mode = "sent_dry_run" if DRY_RUN else "approved_live"
    draft["status"] = mode
    draft["approved_by"] = approver
    draft["approved_at_ist"] = now_ist()
    save_json("outbox", outbox)

    leads = load_json("leads")
    lead = next((x for x in leads if x.get("lead_id") == draft["lead_id"]), None)
    if lead:
        lead["last_contacted_ist"] = now_ist()
        if lead.get("stage") == "New":
            lead["stage"] = "Qualified"
        save_json("leads", leads)

    append_conversation(draft["lead_id"], "outbound_" + mode, draft.get("channel", "WhatsApp"), draft["draft_text"])
    log_audit("draft_approved", draft["lead_id"], f"{draft_id} -> {mode} by {approver}")
    return draft


def reject_draft(draft_id: str, reason: str = "Needs edit") -> Dict[str, Any]:
    outbox = load_json("outbox")
    draft = next((d for d in outbox if d.get("draft_id") == draft_id), None)
    if not draft:
        raise ValueError("Draft not found: " + draft_id)
    draft["status"] = "rejected"
    draft["reject_reason"] = reason
    draft["rejected_at_ist"] = now_ist()
    save_json("outbox", outbox)
    log_audit("draft_rejected", draft["lead_id"], f"{draft_id}: {reason}")
    return draft


def queue_followup_drafts(max_followups: int = 3) -> List[Dict[str, Any]]:
    leads = load_json("leads")
    outbox = load_json("outbox")
    pending = {d.get("lead_id") for d in outbox if d.get("status") == "pending_approval"}
    created = []

    for lead in leads:
        lid = lead.get("lead_id", "")
        count = int(lead.get("followup_count", 0))
        if lead.get("stage") in ("Won", "Lost", "Closed") or count >= max_followups or lid in pending:
            continue
        if not lead.get("external_sequence_active", False):
            continue

        lang = lead.get("preferred_lang", "en")
        tpl = TEMPLATES.get(lang, TEMPLATES["en"])
        did = f"DR-{len(outbox) + 1:04d}"
        draft = {
            "draft_id": did,
            "lead_id": lid,
            "channel": lead.get("channel", "WhatsApp"),
            "reply_lang": lang,
            "draft_text": tpl.format(name=lead.get("name", "there")),
            "status": "pending_approval",
            "followup_number": count + 1,
            "created_at_ist": now_ist(),
        }
        outbox.append(draft)
        lead["followup_count"] = count + 1
        created.append(draft)
        log_audit("followup_queued", lid, f"Queued {did} (step {count + 1})")

    save_json("outbox", outbox)
    save_json("leads", leads)
    return created


if __name__ == "__main__":
    res = approve_draft("DR-0001", approver="Vignesh")
    print("Approved:", res["draft_id"], "| Mode:", res["status"])
    fups = queue_followup_drafts()
    print("Queued follow-up drafts:", len(fups))