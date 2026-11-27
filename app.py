import streamlit as st
from storage import load_json, save_json, seed_demo_data
from intake import ingest_lead, log_audit
from agent import qualify_and_draft
from crm_actions import approve_draft, reject_draft, queue_followup_drafts, DRY_RUN

st.set_page_config(page_title="Dreamwell AI CRM", layout="wide")
seed_demo_data(force=False)

st.title("Dreamwell Technologies — Agentic AI CRM")
mode = "DRY-RUN (Safe Mode)" if DRY_RUN else "LIVE"
st.info(f"WhatsApp: {mode} | Hub: Coimbatore | Reg: Sathyamangalam, TN | IST")

leads = load_json("leads")
outbox = load_json("outbox")
pending = [d for d in outbox if d.get("status") == "pending_approval"]
dry = [d for d in outbox if d.get("status") == "sent_dry_run"]
active = [x for x in leads if x.get("external_sequence_active")]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Leads", len(leads))
c2.metric("Pending Approval", len(pending))
c3.metric("Dry-Run Sent", len(dry))
c4.metric("Active Follow-Ups", len(active))

t1, t2, t3 = st.tabs(["Leads & AI", "Approval Queue", "Logs"])

with t1:
    with st.expander("Add New Lead", expanded=False):
        with st.form("lead_form"):
            nm = st.text_input("Name", "Meena Silks (Synthetic)")
            ph = st.text_input("Phone", "9842211223")
            ct = st.text_input("City", "Coimbatore")
            ind = st.text_input("Industry", "Textiles")
            ch = st.selectbox("Channel", ["WhatsApp", "Instagram", "Website"])
            msg = st.text_area("Message", "Vanakkam, bot pricing sollunga")
            if st.form_submit_button("Save Lead"):
                ld, created = ingest_lead(nm, ph, ct, ind, ch, msg)
                st.success("Saved " + ld["lead_id"] + " (new=" + str(created) + ")")
                st.rerun()

    for ld in leads:
        lid, ln = ld["lead_id"], ld.get("name", "")
        lc, ls, ll, lm = ld.get("city", ""), ld.get("stage", ""), ld.get("preferred_lang", ""), ld.get("latest_message", "")
        cols = st.columns([3, 1, 1])
        cols[0].write(f"**{lid} — {ln}** ({lc}) | {ls} | {ll}\n_{lm}_")
        seq = ld.get("external_sequence_active", False)
        if cols[1].button("Stop Seq" if seq else "Start Seq", key="s_" + lid):
            ld["external_sequence_active"] = not seq
            save_json("leads", leads)
            log_audit("sequence_toggle", lid, "active=" + str(not seq))
            st.rerun()
        if cols[2].button("AI Qualify", key="a_" + lid):
            try:
                dr = qualify_and_draft(lid)
                st.success("Draft " + dr["draft_id"] + " created")
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.dataframe(leads, use_container_width=True)

with t2:
    if st.button("Queue Follow-Up Drafts"):
        added = queue_followup_drafts()
        st.success(f"Queued {len(added)} draft(s)")
        st.rerun()
    for d in pending:
        did, dl, dlg, dt = d["draft_id"], d.get("lead_id", ""), d.get("reply_lang", ""), d.get("created_at_ist", "")
        with st.container(border=True):
            st.write(f"**{did}** | {dl} | {dlg} | {dt}")
            st.write(d.get("draft_text", ""))
            b1, b2 = st.columns(2)
            if b1.button("Approve (Dry-Run)", key="p_" + did):
                approve_draft(did)
                st.rerun()
            if b2.button("Reject", key="r_" + did):
                reject_draft(did)
                st.rerun()
    st.dataframe(outbox, use_container_width=True)

with t3:
    st.subheader("Conversations")
    st.dataframe(list(reversed(load_json("conversations"))), use_container_width=True)
    st.subheader("Audit Log (IST)")
    st.dataframe(list(reversed(load_json("audit_log"))), use_container_width=True)