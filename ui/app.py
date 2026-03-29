import sys
import os
import tempfile
import streamlit as st

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.orchestrator import Orchestrator
from services.db_service import db_service

st.set_page_config(
    page_title="Invoice AI System",
    page_icon="🧾",
    layout="wide"
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ System Info")
    st.caption("Running on Ollama (local LLM)")

    st.subheader("📦 Inventory")
    items = db_service.get_all_items()
    for item in items:
        color = "🟢" if item["stock"] > 0 else "🔴"
        st.write("%s **%s** — %d in stock" % (color, item["item_name"], item["stock"]))

    st.divider()
    st.caption("Supported formats: PDF, TXT, CSV, JSON")

# ── Main ─────────────────────────────────────────────────────────────────────
st.title("🧾 Invoice AI Processing System")
st.write("Upload an invoice to run it through the full AI pipeline: Ingestion → Validation → Approval → Payment")

uploaded_file = st.file_uploader(
    "Upload Invoice",
    type=["pdf", "txt", "csv", "json"],
    help="Supports PDF, TXT, CSV, and JSON invoice formats"
)

if uploaded_file:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.info("📄 File uploaded: **%s**" % uploaded_file.name)

    if st.button("▶️ Run Pipeline", type="primary"):
        orchestrator = Orchestrator()

        # Progress bar
        progress = st.progress(0, text="Starting pipeline...")
        status_area = st.empty()

        with st.spinner("Processing invoice..."):
            # We hook into stages via the orchestrator result
            progress.progress(10, text="📥 Ingesting invoice...")
            result = orchestrator.run(tmp_path)

        progress.progress(100, text="✅ Done")

        # ── Final Status Banner ──────────────────────────────────────────────
        st.divider()
        status = result["status"]
        if status == "APPROVED":
            st.success("## ✅ APPROVED")
        elif status == "REJECTED":
            st.error("## ❌ REJECTED")
        else:
            st.error("## 💥 FAILED")

        if result.get("error"):
            st.error("**Error:** %s" % result["error"])

        # ── 4 Stage Cards ───────────────────────────────────────────────────
        st.subheader("Pipeline Stages")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("### 📥 Ingestion")
            if result.get("invoice"):
                inv = result["invoice"]
                st.success("✅ Success")
                st.write("**Vendor:** %s" % inv.vendor)
                st.write("**Total:** $%.2f" % inv.total)
                st.write("**Due:** %s" % (inv.due_date or "N/A"))
                st.write("**Items:** %d" % len(inv.items))
            else:
                st.error("❌ Failed")

        with col2:
            st.markdown("### ✅ Validation")
            if result.get("validation"):
                val = result["validation"]
                if val.is_valid:
                    st.success("✅ Passed")
                else:
                    st.error("❌ Failed")
                    for err in val.errors:
                        st.caption("• %s" % err)
            else:
                st.warning("⏭️ Skipped")

        with col3:
            st.markdown("### 🤔 Approval")
            if result.get("decision"):
                dec = result["decision"]
                if dec.approved:
                    st.success("✅ Approved")
                else:
                    st.error("❌ Rejected")
                st.caption(dec.reasoning)
            else:
                st.warning("⏭️ Skipped")

        with col4:
            st.markdown("### 💳 Payment")
            if result.get("payment"):
                pay = result["payment"]
                if pay.get("status") == "success":
                    st.success("✅ Success")
                    st.write("**TXN:** %s" % pay.get("transaction_id", "N/A"))
                    st.write("**Amount:** $%.2f" % pay.get("amount", 0))
                elif pay.get("status") == "skipped":
                    st.warning("⏭️ Skipped")
                    st.caption(pay.get("reason", ""))
                else:
                    st.error("❌ Failed")
            else:
                st.warning("⏭️ Skipped")

        # ── Invoice Items Table ──────────────────────────────────────────────
        if result.get("invoice") and result["invoice"].items:
            st.divider()
            st.subheader("📋 Invoice Line Items")
            items_data = [
                {
                    "Item": item.name,
                    "Qty": item.qty,
                    "Unit Price": "$%.2f" % item.price,
                    "Line Total": "$%.2f" % (item.qty * item.price)
                }
                for item in result["invoice"].items
            ]
            st.table(items_data)

        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
