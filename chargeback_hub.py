"""
NewAge Products — Retailer Chargeback Management Hub
Full module: Dashboard, Case Tracker, ASN/Appointment/POD Logic,
Dispute Probability Scorer, Retailer SOPs, Heat Maps, AI Recommendations
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random, io, requests

random.seed(77)

NAVY   = "#17375E"
SLATE  = "#4B5563"
GREEN  = "#2E7D32"
ORANGE = "#ED6C02"
RED    = "#D32F2F"
BG     = "#F8FAFC"
WHITE  = "#FFFFFF"
BLUE2  = "#2C5282"
GOLD   = "#F6E05E"

# ── Retailer compliance rules ──────────────────────────────────────────────────
RETAILER_RULES = {
    "Costco": {
        "color": "#005DAA",
        "asn_timing": "24 hours before shipment",
        "appointment": "Required — must book 72-96 hrs in advance",
        "pod_required": "Yes — signed POD within 24 hours",
        "delivery_window": "Strict — same day as appointment only",
        "routing_guide": "Costco Routing Guide v2024 — mandatory carrier list",
        "dispute_window": "30 days from deduction date",
        "evidence_required": ["Signed POD", "ASN transmission log", "997 confirmation", "BOL", "Appointment confirmation"],
        "common_chargebacks": ["Missing ASN", "Missed Appointment", "Late Delivery", "Short Shipment"],
        "contact": "Costco Vendor Compliance: vendor.compliance@costco.com",
        "portal": "Costco Supplier Portal (CSP)",
        "penalty": "$250 per violation + % of PO value",
    },
    "Home Depot": {
        "color": "#F96302",
        "asn_timing": "Must be sent before carrier pickup",
        "appointment": "Required for all deliveries — HDDC system",
        "pod_required": "Yes — within 48 hours",
        "delivery_window": "±1 day from appointment",
        "routing_guide": "HD Routing Guide — GPS-verified carrier required",
        "dispute_window": "45 days from deduction",
        "evidence_required": ["POD with timestamp", "ASN + 997", "Carrier GPS confirmation", "BOL", "Photos if damage"],
        "common_chargebacks": ["Late ASN", "Routing Guide Violation", "Late Delivery", "Damage"],
        "contact": "HD Vendor Relations: vendorrelations@homedepot.com",
        "portal": "HD Partner Portal (HDPP)",
        "penalty": "2-3% of PO value per violation",
    },
    "Wayfair": {
        "color": "#7B189F",
        "asn_timing": "Same day as shipment — before end of business",
        "appointment": "Not required for most — carrier managed",
        "pod_required": "Yes — e-POD preferred",
        "delivery_window": "Promised date window ±0 days",
        "routing_guide": "Wayfair CastleGate or approved carrier list",
        "dispute_window": "60 days from invoice date",
        "evidence_required": ["e-POD", "ASN confirmation", "Carrier tracking", "Customer delivery photo"],
        "common_chargebacks": ["Missing POD", "Late Delivery", "Damage Claim", "ASN Mismatch"],
        "contact": "Wayfair Partner Services: partnerservices@wayfair.com",
        "portal": "Wayfair Partner Home",
        "penalty": "$100-$500 flat + chargeback % of order",
    },
    "Amazon": {
        "color": "#FF9900",
        "asn_timing": "Required before shipment — Vendor Central",
        "appointment": "Required for FC deliveries — CARP system",
        "pod_required": "Yes — Amazon confirms receipt",
        "delivery_window": "Strict — must hit FC receive window",
        "routing_guide": "Amazon Routing Guide — must use Amazon partnered carriers",
        "dispute_window": "30 days from chargeback notice",
        "evidence_required": ["CARP appointment confirmation", "ASN in Vendor Central", "BOL", "Carrier tracking", "FC receipt confirmation"],
        "common_chargebacks": ["PO On-Time Accuracy", "Receive Window Miss", "ASN Accuracy", "Shortage"],
        "contact": "Amazon Vendor Central — Case Management",
        "portal": "Amazon Vendor Central (AVC)",
        "penalty": "1-3% of PO value — auto-deducted",
    },
    "Lowe's": {
        "color": "#004990",
        "asn_timing": "24 hours before pickup",
        "appointment": "Required — VendorNet system",
        "pod_required": "Yes — within 24 hours of delivery",
        "delivery_window": "Must-arrive-by date strict",
        "routing_guide": "Lowe's Routing Guide — collect shipments only",
        "dispute_window": "45 days from deduction",
        "evidence_required": ["POD", "ASN + 997", "Appointment confirmation", "BOL", "Carrier tracking printout"],
        "common_chargebacks": ["Late Delivery", "Missed Appointment", "Missing ASN", "Label Error"],
        "contact": "Lowe's Vendor Support: vendorsupport@lowes.com",
        "portal": "VendorNet / Lowe's LowesLink",
        "penalty": "$500 flat + 2% of PO",
    },
    "Direct E-commerce": {
        "color": "#2E7D32",
        "asn_timing": "Same day as shipment",
        "appointment": "Not required — residential delivery",
        "pod_required": "Photo POD preferred",
        "delivery_window": "Promised date on order confirmation",
        "routing_guide": "Internal carrier selection — approved list",
        "dispute_window": "90 days",
        "evidence_required": ["Carrier tracking", "Photo POD", "Customer communication log", "Order confirmation"],
        "common_chargebacks": ["Late Delivery", "Damage", "Missing Item", "Wrong Item"],
        "contact": "Internal Customer Service team",
        "portal": "Internal OMS / Shopify",
        "penalty": "Refund + return freight cost",
    },
}

# ── Root cause categories ──────────────────────────────────────────────────────
ROOT_CAUSES = [
    "Missing ASN", "Late ASN", "ASN Quantity Mismatch", "PO/SKU/UPC Mismatch",
    "Missed Delivery Appointment", "Late Delivery", "Missing POD",
    "Short Shipment", "Damage Claim", "Routing Guide Violation",
    "Label/Carton Error", "Carrier Documentation Delay",
    "Warehouse Shipping Error", "Retailer Dispute/Invalid Deduction",
]

RETAILERS    = list(RETAILER_RULES.keys())
CARRIERS     = ["FedEx", "UPS", "XPO Logistics", "Estes Express", "Old Dominion"]
REGIONS      = ["Northeast", "Southeast", "Midwest", "Southwest", "West Coast", "Canada"]
OWNERS       = ["EDI/Logistics Coord.", "Warehouse Manager", "Inventory Control",
                "Logistics Manager", "Carrier Mgmt/Ops", "Packaging QA",
                "Operations/EDI", "Account Manager"]
DISP_STATUS  = ["Open", "Under Review", "Disputed", "Approved", "Denied", "Written Off", "Recovered"]

# ── Generate 30 chargeback cases ───────────────────────────────────────────────
def make_chargeback_cases():
    cases = []
    today = datetime.now()

    retailer_weights = {
        "Costco": 5, "Home Depot": 7, "Wayfair": 6,
        "Amazon": 6, "Lowe's": 4, "Direct E-commerce": 2,
    }
    retailer_pool = []
    for r, w in retailer_weights.items():
        retailer_pool.extend([r] * w)

    rc_by_retailer = {
        "Costco":            ["Missing ASN", "Missed Delivery Appointment", "Late Delivery", "Short Shipment"],
        "Home Depot":        ["Late ASN", "Routing Guide Violation", "Late Delivery", "Damage Claim"],
        "Wayfair":           ["Missing POD", "Late Delivery", "Damage Claim", "ASN Quantity Mismatch"],
        "Amazon":            ["PO/SKU/UPC Mismatch", "Short Shipment", "Missing ASN", "Late Delivery"],
        "Lowe's":            ["Late Delivery", "Missed Delivery Appointment", "Missing ASN", "Label/Carton Error"],
        "Direct E-commerce": ["Late Delivery", "Damage Claim", "Missing POD", "Warehouse Shipping Error"],
    }

    for i in range(1, 31):
        retailer = retailer_pool[i % len(retailer_pool)]
        rc       = random.choice(rc_by_retailer[retailer])
        carrier  = random.choice(CARRIERS)
        region   = random.choice(REGIONS)
        amount   = round(random.uniform(150, 4500), 2)
        aging    = random.randint(1, 85)
        ddl      = random.randint(5, 45)
        ship_date= today - timedelta(days=aging + random.randint(5,15))
        del_date = ship_date + timedelta(days=random.randint(3, 10))
        appt_date= del_date - timedelta(days=1)

        # Evidence availability
        pod_avail     = random.choice(["Yes", "Yes", "Yes", "No"])
        asn_status    = random.choice(["Sent", "Sent", "Late", "Missing", "Mismatch"])
        photos_avail  = random.choice(["Yes", "No"]) if "Damage" in rc else "N/A"
        evidence_score= (
            (30 if pod_avail == "Yes" else 0) +
            (30 if asn_status == "Sent" else (10 if asn_status == "Late" else 0)) +
            (20 if photos_avail == "Yes" else (10 if photos_avail == "N/A" else 0)) +
            random.randint(0, 20)
        )

        # Dispute probability
        dispute_prob = min(100, evidence_score + random.randint(-10, 10))
        dispute_rec  = (
            "DISPUTE — Strong evidence" if dispute_prob >= 70 else
            ("NEGOTIATE — Mixed fault" if dispute_prob >= 45 else
             ("ACCEPT — Our fault" if dispute_prob >= 20 else "ACCEPT — Clear fault"))
        )

        # Owner
        owner_map = {
            "Missing ASN": "EDI/Logistics Coord.",
            "Late ASN": "Warehouse Manager",
            "ASN Quantity Mismatch": "Inventory Control",
            "PO/SKU/UPC Mismatch": "Inventory Control",
            "Missed Delivery Appointment": "Logistics Manager",
            "Late Delivery": "Carrier Mgmt/Ops",
            "Missing POD": "Operations/EDI",
            "Short Shipment": "Warehouse Manager",
            "Damage Claim": "Packaging QA",
            "Routing Guide Violation": "Logistics Manager",
            "Label/Carton Error": "Warehouse Manager",
            "Carrier Documentation Delay": "Carrier Mgmt/Ops",
            "Warehouse Shipping Error": "Warehouse Manager",
            "Retailer Dispute/Invalid Deduction": "Account Manager",
        }

        escalation = "Yes" if amount > 10000 or aging > 60 else "No"
        disp_status = random.choices(
            DISP_STATUS, weights=[20, 15, 20, 15, 10, 10, 10]
        )[0]
        recovery = round(amount * random.uniform(0.5, 0.9), 2) if disp_status == "Recovered" else 0

        prevention = {
            "Missing ASN": "Implement pre-shipment ASN validation gate",
            "Late ASN": "Redesign workflow: ASN send before carrier booking",
            "ASN Quantity Mismatch": "Staged picking with ASN pre-validation",
            "PO/SKU/UPC Mismatch": "Quarterly item master reconciliation with retailer",
            "Missed Delivery Appointment": "Book appointments 72-96 hrs before pickup",
            "Late Delivery": "Carrier performance scorecard — 98% OT required",
            "Missing POD": "Automated POD capture — photo + GPS + signature",
            "Short Shipment": "Weigh and count verification before shipment close",
            "Damage Claim": "Packaging audit + carrier handling review",
            "Routing Guide Violation": "Mandatory routing guide checklist before booking",
            "Label/Carton Error": "Barcode verification scan before load",
            "Carrier Documentation Delay": "Escalate carrier POD SLA — 24hr requirement",
            "Warehouse Shipping Error": "Pick-pack-verify process with 3-way check",
            "Retailer Dispute/Invalid Deduction": "Account manager monthly compliance review",
        }.get(rc, "Review root cause and implement corrective action")

        cases.append({
            "Chargeback ID":         f"CB-{2000+i}",
            "Retailer":              retailer,
            "PO Number":             f"PO-{random.randint(10000,99999)}",
            "Order Number":          f"ORD-{random.randint(1000,9999)}",
            "ASN Number":            f"ASN-{random.randint(10000,99999)}",
            "Carrier":               carrier,
            "Region":                region,
            "Delivery Appt Date":    appt_date.strftime("%Y-%m-%d"),
            "Actual Delivery Date":  del_date.strftime("%Y-%m-%d"),
            "POD Available":         pod_avail,
            "ASN Status":            asn_status,
            "Chargeback Reason":     rc,
            "Root Cause Category":   rc,
            "Amount":                amount,
            "Aging Days":            aging,
            "Dispute Deadline":      (today + timedelta(days=ddl)).strftime("%Y-%m-%d"),
            "Days to Deadline":      ddl,
            "Evidence Score":        evidence_score,
            "Dispute Probability":   dispute_prob,
            "Recommended Action":    dispute_rec,
            "Owner":                 owner_map.get(rc, "Logistics Manager"),
            "Dispute Status":        disp_status,
            "Recovery Amount":       recovery,
            "Escalation Required":   escalation,
            "Prevention Action":     prevention,
            "Photos Available":      photos_avail,
        })

    return pd.DataFrame(cases)

# ── Dispute probability scorer ─────────────────────────────────────────────────
def score_dispute(asn_sent, asn_timing, asn_accepted, asn_accuracy,
                  po_accuracy, appt_compliance, on_time, pod_available,
                  carrier_history, prior_success, retailer_pattern):
    scores = {
        "ASN sent on time (≥24hrs)":      10 if asn_timing == "≥24 hrs before" else (5 if asn_timing == "Same day" else 0),
        "ASN accepted by retailer (997)":  10 if asn_accepted == "Yes" else 0,
        "ASN data accuracy":               asn_accuracy,
        "PO/Order fulfillment accuracy":   po_accuracy,
        "Appointment compliance":          10 if appt_compliance == "On time" else (5 if appt_compliance == "Late" else 0),
        "On-time delivery":                10 if on_time == "On time" else (5 if on_time == "1-2 days late" else 0),
        "POD/Evidence availability":       10 if pod_available == "Complete POD + photos" else (5 if pod_available == "POD only" else 0),
        "Carrier performance history":     carrier_history,
        "Prior dispute success":           prior_success,
        "Retailer chargeback pattern":     retailer_pattern,
    }
    total = sum(scores.values())
    return scores, total

# ── Session helpers ────────────────────────────────────────────────────────────
def get_cb_comments(row_id):
    key = "cb_comments"
    if key not in st.session_state:
        st.session_state[key] = {}
    return st.session_state[key].get(str(row_id), {"Comment 1": "", "Comment 2": ""})

def save_cb_comment(row_id, col, val):
    key = "cb_comments"
    if key not in st.session_state:
        st.session_state[key] = {}
    if str(row_id) not in st.session_state[key]:
        st.session_state[key][str(row_id)] = {"Comment 1": "", "Comment 2": ""}
    st.session_state[key][str(row_id)][col] = val

def download_with_comments(df, id_col, filename):
    comments = st.session_state.get("cb_comments", {})
    export = df.copy()
    export["Comment 1"] = export[id_col].apply(lambda x: comments.get(str(x), {}).get("Comment 1", ""))
    export["Comment 2"] = export[id_col].apply(lambda x: comments.get(str(x), {}).get("Comment 2", ""))
    export["Export Date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export.to_excel(writer, index=False)
    buf.seek(0)
    st.download_button(
        "⬇️ Download with Comments",
        data=buf,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

def section(title):
    st.markdown(
        f'<div style="background:{NAVY};color:white;padding:8px 16px;'
        f'border-radius:6px 6px 0 0;font-size:13px;font-weight:600;">{title}</div>',
        unsafe_allow_html=True
    )

# ── MAIN RENDERER ──────────────────────────────────────────────────────────────
def render_chargeback_hub():
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{NAVY} 0%,{BLUE2} 100%);'
        f'color:white;padding:16px 24px;border-radius:8px;margin-bottom:16px;">'
        f'<div style="font-size:20px;font-weight:700;">🏪 Retailer Chargeback Management Hub</div>'
        f'<div style="font-size:12px;color:#CBD5E0;margin-top:3px;">'
        f'NewAge Products &nbsp;|&nbsp; ASN, Appointment & POD Compliance &nbsp;|&nbsp; '
        f'{datetime.now().strftime("%B %d, %Y")}</div></div>',
        unsafe_allow_html=True
    )

    cases_df = make_chargeback_cases()

    tabs = st.tabs([
        "📊 Retailer Dashboard",
        "📋 Case Tracker",
        "🔍 Dispute Probability Scorer",
        "🌎 Region & Carrier Heat Map",
        "🤖 AI Recommendations",
        "📚 Retailer SOP Checklists",
        "📝 Executive Summary",
    ])

    # ── Tab 1: Retailer Dashboard ──────────────────────────────────────────────
    with tabs[0]:
        section("📊 Chargeback Performance by Retailer")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Summary KPIs
        c1,c2,c3,c4,c5 = st.columns(5)
        total_val     = cases_df["Amount"].sum()
        total_cases   = len(cases_df)
        disputed_val  = cases_df[cases_df["Dispute Status"].isin(["Disputed","Under Review"])]["Amount"].sum()
        recovered_val = cases_df["Recovery Amount"].sum()
        net_loss      = total_val - recovered_val

        for col, label, val, color in [
            (c1, "Total Chargeback Value",  f"${total_val:,.0f}",      RED),
            (c2, "Total Cases",             f"{total_cases}",           NAVY),
            (c3, "Under Dispute",           f"${disputed_val:,.0f}",   ORANGE),
            (c4, "Recovered",               f"${recovered_val:,.0f}",  GREEN),
            (c5, "Net Loss",                f"${net_loss:,.0f}",       RED),
        ]:
            with col:
                st.markdown(
                    f'<div style="background:{WHITE};border:1px solid #E2E8F0;'
                    f'border-top:4px solid {color};border-radius:8px;padding:14px;text-align:center;">'
                    f'<div style="font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;">{label}</div>'
                    f'<div style="font-size:24px;font-weight:700;color:{color};margin:6px 0 2px;">{val}</div>'
                    f'</div>', unsafe_allow_html=True
                )

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # Retailer cards
        cols = st.columns(3)
        for i, (retailer, rules) in enumerate(RETAILER_RULES.items()):
            r_cases  = cases_df[cases_df["Retailer"] == retailer]
            r_total  = r_cases["Amount"].sum()
            r_count  = len(r_cases)
            r_recov  = r_cases["Recovery Amount"].sum()
            r_net    = r_total - r_recov
            r_rate   = r_count / max(total_cases, 1) * 100
            top_rc   = r_cases["Root Cause Category"].mode()[0] if len(r_cases) > 0 else "—"
            top_carr = r_cases["Carrier"].mode()[0] if len(r_cases) > 0 else "—"
            open_val = r_cases[r_cases["Dispute Status"] == "Open"]["Amount"].sum()
            score    = 100 - min(100, (r_count * 5) + (r_total / 500))
            status   = "🟢 GREEN" if score > 70 else ("🟡 YELLOW" if score > 45 else "🔴 RED")
            s_color  = GREEN if score > 70 else (ORANGE if score > 45 else RED)

            with cols[i % 3]:
                st.markdown(
                    f'<div style="background:{WHITE};border:1px solid #E2E8F0;'
                    f'border-top:5px solid {rules["color"]};border-radius:8px;padding:16px;margin-bottom:12px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
                    f'<div style="font-size:14px;font-weight:700;color:{NAVY};">{retailer}</div>'
                    f'<div style="font-size:12px;font-weight:700;color:{s_color};">{status}</div>'
                    f'</div>'
                    f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">'
                    f'<div><div style="font-size:10px;color:{SLATE};">Total Amount</div><div style="font-size:14px;font-weight:700;color:{RED};">${r_total:,.0f}</div></div>'
                    f'<div><div style="font-size:10px;color:{SLATE};">Cases</div><div style="font-size:14px;font-weight:700;color:{NAVY};">{r_count}</div></div>'
                    f'<div><div style="font-size:10px;color:{SLATE};">Open</div><div style="font-size:13px;font-weight:600;color:{ORANGE};">${open_val:,.0f}</div></div>'
                    f'<div><div style="font-size:10px;color:{SLATE};">Recovered</div><div style="font-size:13px;font-weight:600;color:{GREEN};">${r_recov:,.0f}</div></div>'
                    f'<div><div style="font-size:10px;color:{SLATE};">Net Loss</div><div style="font-size:13px;font-weight:600;color:{RED};">${r_net:,.0f}</div></div>'
                    f'<div><div style="font-size:10px;color:{SLATE};">Chargeback %</div><div style="font-size:13px;font-weight:600;color:{NAVY};">{r_rate:.0f}%</div></div>'
                    f'</div>'
                    f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid #E2E8F0;">'
                    f'<div style="font-size:10px;color:{SLATE};">Top Reason: <strong>{top_rc}</strong></div>'
                    f'<div style="font-size:10px;color:{SLATE};margin-top:2px;">Top Carrier: <strong>{top_carr}</strong></div>'
                    f'</div></div>',
                    unsafe_allow_html=True
                )

        # Bar chart
        r_summary = cases_df.groupby("Retailer").agg(
            Total=("Amount","sum"), Cases=("Chargeback ID","count"),
            Recovered=("Recovery Amount","sum")
        ).reset_index()
        r_summary["Net Loss"] = r_summary["Total"] - r_summary["Recovered"]
        r_summary = r_summary.sort_values("Total", ascending=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Net Loss", x=r_summary["Net Loss"], y=r_summary["Retailer"],
                             orientation="h", marker_color=RED))
        fig.add_trace(go.Bar(name="Recovered", x=r_summary["Recovered"], y=r_summary["Retailer"],
                             orientation="h", marker_color=GREEN))
        fig.update_layout(
            barmode="stack", height=260,
            margin=dict(l=0,r=0,t=10,b=10),
            plot_bgcolor=BG, paper_bgcolor=BG,
            legend=dict(orientation="h", y=1.1),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(tickfont=dict(size=11)),
            title=dict(text="Chargeback Exposure by Retailer — Net Loss vs Recovered", font=dict(size=11,color=SLATE)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: Case Tracker ────────────────────────────────────────────────────
    with tabs[1]:
        section("📋 Chargeback Case Tracker — All 30 Cases")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # Filters
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            sel_ret = st.multiselect("Filter Retailer", RETAILERS, default=[])
        with fc2:
            sel_rc  = st.multiselect("Filter Root Cause", ROOT_CAUSES[:8], default=[])
        with fc3:
            sel_stat= st.multiselect("Filter Status", DISP_STATUS, default=[])

        filtered = cases_df.copy()
        if sel_ret:  filtered = filtered[filtered["Retailer"].isin(sel_ret)]
        if sel_rc:   filtered = filtered[filtered["Root Cause Category"].isin(sel_rc)]
        if sel_stat: filtered = filtered[filtered["Dispute Status"].isin(sel_stat)]

        display_cols = ["Chargeback ID","Retailer","Carrier","Region","Chargeback Reason",
                        "Amount","ASN Status","POD Available","Aging Days","Days to Deadline",
                        "Evidence Score","Dispute Probability","Recommended Action",
                        "Owner","Dispute Status","Recovery Amount","Escalation Required"]
        disp = filtered[display_cols].copy()
        disp["Amount"]          = disp["Amount"].apply(lambda x: f"${x:,.2f}")
        disp["Recovery Amount"] = disp["Recovery Amount"].apply(lambda x: f"${x:,.2f}")
        disp["Evidence Score"]  = disp["Evidence Score"].apply(lambda x: f"{x}/100")
        disp["Dispute Probability"] = disp["Dispute Probability"].apply(lambda x: f"{x}%")

        def color_action(val):
            if "DISPUTE" in str(val):   return "background-color:#E8F5E9;color:#2E7D32;font-weight:700"
            if "NEGOTIATE" in str(val): return "background-color:#FFF3E0;color:#E65100;font-weight:600"
            if "ACCEPT" in str(val):    return "background-color:#FDECEA;color:#C62828;font-weight:600"
            return ""
        def color_pod(val):
            if val == "Yes": return "background-color:#E8F5E9;color:#2E7D32;font-weight:600"
            if val == "No":  return "background-color:#FDECEA;color:#C62828;font-weight:700"
            return ""
        def color_asn(val):
            if val == "Sent":    return "background-color:#E8F5E9;color:#2E7D32"
            if val == "Missing": return "background-color:#FDECEA;color:#C62828;font-weight:700"
            if val == "Late":    return "background-color:#FFF3E0;color:#E65100;font-weight:600"
            return "background-color:#EBF4FF;color:#1565C0"
        def color_esc(val):
            if val == "Yes": return "background-color:#FDECEA;color:#C62828;font-weight:700"
            return ""

        styled = (disp.style
                  .map(color_action, subset=["Recommended Action"])
                  .map(color_pod, subset=["POD Available"])
                  .map(color_asn, subset=["ASN Status"])
                  .map(color_esc, subset=["Escalation Required"]))

        st.dataframe(styled, use_container_width=True, hide_index=True, height=400)

        # Comments
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        with st.expander("✏️ Add / Edit Comments"):
            for idx, row in filtered.head(15).iterrows():
                cid = row["Chargeback ID"]
                existing = get_cb_comments(cid)
                c1, c2, c3 = st.columns([2,3,3])
                with c1:
                    st.markdown(f"<div style='font-size:12px;font-weight:600;padding-top:6px;'>{cid} — {row['Retailer']}</div>", unsafe_allow_html=True)
                with c2:
                    v1 = st.text_input("C1", value=existing["Comment 1"],
                        key=f"cb_c1_{cid}", label_visibility="collapsed",
                        placeholder="Comment 1 — action taken")
                    save_cb_comment(cid, "Comment 1", v1)
                with c3:
                    v2 = st.text_input("C2", value=existing["Comment 2"],
                        key=f"cb_c2_{cid}", label_visibility="collapsed",
                        placeholder="Comment 2 — follow-up / status")
                    save_cb_comment(cid, "Comment 2", v2)

        download_with_comments(filtered, "Chargeback ID", "NewAge_Chargeback_Cases")

    # ── Tab 3: Dispute Probability Scorer ─────────────────────────────────────
    with tabs[2]:
        section("🔍 Dispute Probability Scorer — Score Any Chargeback Case")
        st.markdown(
            f'<div style="background:#EBF4FF;border:1px solid #BEE3F8;border-left:4px solid #3182CE;'
            f'border-radius:6px;padding:12px 16px;margin:8px 0 14px;font-size:13px;">'
            f'Score each factor 0-10. The model calculates your dispute win probability and recommends an action.</div>',
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)
        with c1:
            asn_sent    = st.selectbox("Was ASN sent?", ["Yes","No"])
            asn_timing  = st.selectbox("ASN send timing", ["≥24 hrs before","Same day","After shipment","Not sent"])
            asn_accepted= st.selectbox("ASN accepted by retailer (997)?", ["Yes","No","Unknown"])
            asn_acc_sc  = st.slider("ASN data accuracy (0-10)", 0, 10, 8)
            po_acc_sc   = st.slider("PO/Order fulfillment accuracy (0-10)", 0, 10, 9)

        with c2:
            appt_comp   = st.selectbox("Appointment compliance", ["On time","Late","Missed","N/A"])
            on_time_del = st.selectbox("Delivery performance", ["On time","1-2 days late","3+ days late"])
            pod_avail   = st.selectbox("POD/Evidence availability", ["Complete POD + photos","POD only","No POD"])
            carrier_sc  = st.slider("Carrier performance history (0-10)", 0, 10, 7)
            prior_sc    = st.slider("Prior dispute success with retailer (0-10)", 0, 10, 6)
            pattern_sc  = st.slider("Retailer chargeback pattern (0-10, 10=rare)", 0, 10, 5)

        if st.button("Calculate Dispute Probability"):
            scores, total = score_dispute(
                asn_sent, asn_timing, asn_accepted, asn_acc_sc,
                po_acc_sc, appt_comp, on_time_del, pod_avail,
                carrier_sc, prior_sc, pattern_sc
            )

            prob_color = GREEN if total >= 70 else (ORANGE if total >= 45 else RED)
            action = (
                "DISPUTE — Strong evidence. File immediately." if total >= 70 else
                ("NEGOTIATE — Mixed fault. Seek partial credit." if total >= 45 else
                 ("EVALUATE — Low probability. Weigh cost vs benefit." if total >= 25 else
                  "ACCEPT — Clear internal fault. Pay and prevent recurrence."))
            )
            win_pct = (
                "70-90% win probability" if total >= 70 else
                ("40-70% win probability" if total >= 45 else
                 ("20-40% win probability" if total >= 25 else "<20% win probability"))
            )

            st.markdown(
                f'<div style="background:{prob_color};color:white;border-radius:8px;'
                f'padding:16px 24px;margin:12px 0;">'
                f'<div style="font-size:11px;opacity:0.8;font-weight:700;text-transform:uppercase;">Dispute Score</div>'
                f'<div style="font-size:36px;font-weight:700;">{total}/100 &nbsp;—&nbsp; {win_pct}</div>'
                f'<div style="font-size:14px;margin-top:6px;">{action}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Score breakdown
            st.markdown("**Score Breakdown:**")
            for factor, pts in scores.items():
                bar_w = int(pts / 10 * 100)
                bar_c = GREEN if pts >= 7 else (ORANGE if pts >= 4 else RED)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;padding:5px 0;">'
                    f'<div style="font-size:12px;color:{NAVY};min-width:280px;">{factor}</div>'
                    f'<div style="flex:1;background:#E2E8F0;border-radius:4px;height:8px;">'
                    f'<div style="width:{bar_w}%;height:8px;border-radius:4px;background:{bar_c};"></div></div>'
                    f'<div style="font-size:12px;font-weight:700;color:{bar_c};min-width:30px;">{pts}/10</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # ── Tab 4: Heat Map ────────────────────────────────────────────────────────
    with tabs[3]:
        section("🌎 Region & Carrier Heat Map")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            region_data = cases_df.groupby("Region")["Amount"].sum().sort_values(ascending=True).reset_index()
            fig1 = go.Figure(go.Bar(
                x=region_data["Amount"], y=region_data["Region"],
                orientation="h",
                marker_color=[RED if v == region_data["Amount"].max() else ORANGE for v in region_data["Amount"]],
                text=[f"${v:,.0f}" for v in region_data["Amount"]],
                textposition="outside",
            ))
            fig1.update_layout(height=280, margin=dict(l=0,r=60,t=30,b=10),
                title=dict(text="Chargeback by Region", font=dict(size=12,color=SLATE)),
                xaxis=dict(showgrid=False,showticklabels=False),
                yaxis=dict(tickfont=dict(size=11)),
                plot_bgcolor=BG, paper_bgcolor=BG)
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            carrier_data = cases_df.groupby("Carrier")["Amount"].sum().sort_values(ascending=True).reset_index()
            fig2 = go.Figure(go.Bar(
                x=carrier_data["Amount"], y=carrier_data["Carrier"],
                orientation="h",
                marker_color=[RED if v == carrier_data["Amount"].max() else NAVY for v in carrier_data["Amount"]],
                text=[f"${v:,.0f}" for v in carrier_data["Amount"]],
                textposition="outside",
            ))
            fig2.update_layout(height=280, margin=dict(l=0,r=60,t=30,b=10),
                title=dict(text="Chargeback by Carrier", font=dict(size=12,color=SLATE)),
                xaxis=dict(showgrid=False,showticklabels=False),
                yaxis=dict(tickfont=dict(size=11)),
                plot_bgcolor=BG, paper_bgcolor=BG)
            st.plotly_chart(fig2, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            rc_data = cases_df.groupby("Root Cause Category")["Amount"].sum().sort_values(ascending=False).head(8).reset_index()
            fig3 = go.Figure(go.Bar(
                x=rc_data["Root Cause Category"], y=rc_data["Amount"],
                marker_color=[RED,RED,ORANGE,ORANGE,ORANGE,NAVY,NAVY,NAVY][:len(rc_data)],
                text=[f"${v:,.0f}" for v in rc_data["Amount"]],
                textposition="outside",
            ))
            fig3.update_layout(height=280, margin=dict(l=0,r=0,t=30,b=60),
                title=dict(text="Top Root Causes by $ Amount", font=dict(size=12,color=SLATE)),
                xaxis=dict(tickfont=dict(size=9),tickangle=30),
                yaxis=dict(showgrid=False,showticklabels=False),
                plot_bgcolor=BG, paper_bgcolor=BG)
            st.plotly_chart(fig3, use_container_width=True)

        with c4:
            ret_rc = cases_df.groupby(["Retailer","Root Cause Category"]).size().reset_index(name="Count")
            pivot  = ret_rc.pivot(index="Root Cause Category", columns="Retailer", values="Count").fillna(0)
            fig4 = go.Figure(go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                colorscale=[[0,"#E8F5E9"],[0.5,"#FFF3E0"],[1,"#FDECEA"]],
                text=pivot.values.astype(int),
                texttemplate="%{text}",
                showscale=False,
            ))
            fig4.update_layout(height=280, margin=dict(l=0,r=0,t=30,b=10),
                title=dict(text="Root Cause × Retailer Heat Map", font=dict(size=12,color=SLATE)),
                xaxis=dict(tickfont=dict(size=10)),
                yaxis=dict(tickfont=dict(size=9)),
                paper_bgcolor=BG)
            st.plotly_chart(fig4, use_container_width=True)

    # ── Tab 5: AI Recommendations ──────────────────────────────────────────────
    with tabs[4]:
        section("🤖 AI Recommendations — Top Priority Cases")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        priority_cases = cases_df[
            (cases_df["Days to Deadline"] < 20) |
            (cases_df["Amount"] > 2000) |
            (cases_df["Escalation Required"] == "Yes")
        ].head(8)

        for _, row in priority_cases.iterrows():
            urgency = "🔴 URGENT" if row["Days to Deadline"] < 10 else ("🟡 HIGH" if row["Days to Deadline"] < 20 else "🔵 REVIEW")
            urg_color = RED if "URGENT" in urgency else (ORANGE if "HIGH" in urgency else BLUE2)

            with st.expander(
                f"{urgency} — {row['Chargeback ID']} | {row['Retailer']} | "
                f"${row['Amount']:,.2f} | {row['Chargeback Reason']} | {row['Days to Deadline']} days to deadline"
            ):
                col1, col2 = st.columns([3,2])
                with col1:
                    # Evidence checklist
                    rules = RETAILER_RULES[row["Retailer"]]
                    evidence_items = rules["evidence_required"]
                    checklist_html = "".join(
                        f'<div style="display:flex;gap:8px;padding:4px 0;">'
                        f'<span style="color:{GREEN};">✓</span>'
                        f'<span style="font-size:12px;">{item}</span></div>'
                        for item in evidence_items
                    )
                    st.markdown(
                        f'<div style="background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;padding:14px;">'
                        f'<div style="font-size:11px;font-weight:700;color:{NAVY};text-transform:uppercase;margin-bottom:8px;">Required Evidence for {row["Retailer"]}</div>'
                        f'{checklist_html}'
                        f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid #E2E8F0;">'
                        f'<div style="font-size:11px;color:{SLATE};">Portal: <strong>{rules["portal"]}</strong></div>'
                        f'<div style="font-size:11px;color:{SLATE};margin-top:2px;">Contact: <strong>{rules["contact"]}</strong></div>'
                        f'<div style="font-size:11px;color:{SLATE};margin-top:2px;">Dispute Window: <strong>{rules["dispute_window"]}</strong></div>'
                        f'</div></div>',
                        unsafe_allow_html=True
                    )

                with col2:
                    disp_color = GREEN if "DISPUTE" in row["Recommended Action"] else (ORANGE if "NEGOTIATE" in row["Recommended Action"] else RED)
                    st.markdown(
                        f'<div style="background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;padding:14px;">'
                        f'<div style="font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;">Recommendation</div>'
                        f'<div style="font-size:13px;font-weight:700;color:{disp_color};margin:4px 0 10px;">{row["Recommended Action"]}</div>'
                        f'<div style="font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;">Owner</div>'
                        f'<div style="font-size:12px;margin:2px 0 8px;">{row["Owner"]}</div>'
                        f'<div style="font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;">ASN Status</div>'
                        f'<div style="font-size:12px;margin:2px 0 8px;">{row["ASN Status"]}</div>'
                        f'<div style="font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;">POD Available</div>'
                        f'<div style="font-size:12px;margin:2px 0 8px;">{row["POD Available"]}</div>'
                        f'<div style="font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;">Prevention Action</div>'
                        f'<div style="font-size:12px;margin:2px 0;">{row["Prevention Action"]}</div>'
                        f'<div style="margin-top:8px;padding:6px;background:{"#FDECEA" if row["Escalation Required"]=="Yes" else "#E8F5E9"};border-radius:4px;">'
                        f'<div style="font-size:11px;font-weight:700;color:{"#C62828" if row["Escalation Required"]=="Yes" else "#2E7D32"};">'
                        f'Escalation: {row["Escalation Required"]}</div></div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    # ── Tab 6: Retailer SOP Checklists ────────────────────────────────────────
    with tabs[5]:
        section("📚 Retailer-Specific SOP Checklists — Compliance Rules & Contact Guide")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        sel_retailer = st.selectbox("Select Retailer", list(RETAILER_RULES.keys()))
        rules = RETAILER_RULES[sel_retailer]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div style="background:{rules["color"]};color:white;border-radius:8px;padding:14px 18px;margin-bottom:12px;">'
                f'<div style="font-size:16px;font-weight:700;">{sel_retailer}</div>'
                f'<div style="font-size:11px;opacity:0.85;margin-top:4px;">Supplier Compliance Portal: {rules["portal"]}</div>'
                f'<div style="font-size:11px;opacity:0.85;margin-top:2px;">Contact: {rules["contact"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            compliance_items = [
                ("ASN Timing", rules["asn_timing"]),
                ("Appointment Required", rules["appointment"]),
                ("POD Required", rules["pod_required"]),
                ("Delivery Window", rules["delivery_window"]),
                ("Routing Guide", rules["routing_guide"]),
                ("Dispute Window", rules["dispute_window"]),
                ("Penalty", rules["penalty"]),
            ]
            for label, val in compliance_items:
                st.markdown(
                    f'<div style="display:flex;gap:12px;padding:8px 12px;'
                    f'background:{WHITE};border:1px solid #E2E8F0;border-radius:4px;margin-bottom:4px;">'
                    f'<div style="font-size:12px;font-weight:700;color:{NAVY};min-width:160px;">{label}</div>'
                    f'<div style="font-size:12px;color:{SLATE};">{val}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        with c2:
            st.markdown("**Required Evidence for Dispute:**")
            for item in rules["evidence_required"]:
                st.markdown(
                    f'<div style="display:flex;gap:8px;padding:7px 12px;'
                    f'background:{WHITE};border:1px solid #E2E8F0;border-radius:4px;margin-bottom:4px;">'
                    f'<span style="color:{GREEN};font-weight:700;">✓</span>'
                    f'<span style="font-size:12px;">{item}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown("**Common Chargeback Types:**")
            for cb in rules["common_chargebacks"]:
                st.markdown(
                    f'<div style="display:flex;gap:8px;padding:7px 12px;'
                    f'background:#FDECEA;border:1px solid #FFCDD2;border-radius:4px;margin-bottom:4px;">'
                    f'<span style="color:{RED};font-weight:700;">⚠</span>'
                    f'<span style="font-size:12px;color:{RED};font-weight:600;">{cb}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # ASN Pre-Shipment Checklist
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("**Pre-Shipment ASN Validation Checklist:**")
        asn_checks = [
            "PO exists in system and is open",
            "PO line quantity matches picked quantity",
            "SKU in our master matches PO SKU",
            "SKU in retailer master confirmed",
            "UPC barcode matches ASN and carton label",
            "Shipped quantity matches PO (±tolerance)",
            "SCAC code = approved carrier on routing guide",
            "Carton IDs assigned and tracked",
            "Pallet IDs assigned and tracked",
            "Ship-to address matches PO",
            "Delivery appointment scheduled and confirmed",
            "ASN ready to transmit — send 24hrs before pickup",
        ]
        cols = st.columns(2)
        for i, check in enumerate(asn_checks):
            with cols[i % 2]:
                st.checkbox(check, key=f"asn_{sel_retailer}_{i}")

        # Download SOP
        sop_text = f"""NEWAGE PRODUCTS — {sel_retailer.upper()} SUPPLIER COMPLIANCE SOP
Generated: {datetime.now().strftime("%B %d, %Y")}

PORTAL: {rules['portal']}
CONTACT: {rules['contact']}
PENALTY: {rules['penalty']}

COMPLIANCE REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━
ASN Timing: {rules['asn_timing']}
Appointment: {rules['appointment']}
POD Required: {rules['pod_required']}
Delivery Window: {rules['delivery_window']}
Routing Guide: {rules['routing_guide']}
Dispute Window: {rules['dispute_window']}

REQUIRED EVIDENCE FOR DISPUTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join('✓ ' + e for e in rules['evidence_required'])}

COMMON CHARGEBACK TYPES
━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join('⚠ ' + c for c in rules['common_chargebacks'])}

PRE-SHIPMENT ASN VALIDATION CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join('☐ ' + c for c in asn_checks)}
"""
        st.download_button(
            f"⬇️ Download {sel_retailer} SOP",
            data=sop_text,
            file_name=f"NewAge_{sel_retailer.replace(' ','_')}_SOP_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )

    # ── Tab 7: Executive Summary ───────────────────────────────────────────────
    with tabs[6]:
        section("📝 Chargeback Executive Summary — Weekly Leadership Report")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        total_val     = cases_df["Amount"].sum()
        disputed_val  = cases_df[cases_df["Dispute Status"].isin(["Disputed","Under Review"])]["Amount"].sum()
        recovered_val = cases_df["Recovery Amount"].sum()
        net_loss      = total_val - recovered_val
        top_retailer  = cases_df.groupby("Retailer")["Amount"].sum().idxmax()
        top_rc        = cases_df["Root Cause Category"].mode()[0]
        top_carrier   = cases_df.groupby("Carrier")["Amount"].sum().idxmax()
        top_region    = cases_df.groupby("Region")["Amount"].sum().idxmax()
        critical_count= len(cases_df[cases_df["Days to Deadline"] < 10])

        c1,c2,c3,c4 = st.columns(4)
        for col, label, val, color in [
            (c1, "Total Exposure",    f"${total_val:,.0f}",      RED),
            (c2, "Under Dispute",     f"${disputed_val:,.0f}",   ORANGE),
            (c3, "Recovered",         f"${recovered_val:,.0f}",  GREEN),
            (c4, "Net Loss",          f"${net_loss:,.0f}",       RED),
        ]:
            with col:
                st.markdown(
                    f'<div style="background:{WHITE};border:1px solid #E2E8F0;'
                    f'border-left:4px solid {color};border-radius:6px;padding:12px;">'
                    f'<div style="font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;">{label}</div>'
                    f'<div style="font-size:22px;font-weight:700;color:{color};margin-top:4px;">{val}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        summary_html = (
            f'<div style="background:{WHITE};border:1px solid #E2E8F0;border-radius:8px;padding:24px;line-height:1.9;font-size:14px;">'
            f'<div style="font-size:10px;font-weight:700;color:{NAVY};text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;">'
            f'📆 Weekly Chargeback Report &nbsp;|&nbsp; {datetime.now().strftime("%B %d, %Y")} &nbsp;|&nbsp; Returns &amp; Claims Division'
            f'</div>'
            f'<strong>Situation:</strong> This week the team reviewed {len(cases_df)} active chargeback cases totaling '
            f'${total_val:,.0f} in exposure across 6 retail partners. Net loss after recovery stands at '
            f'${net_loss:,.0f}. {critical_count} cases are within 10 days of their dispute deadline and require immediate action.<br><br>'
            f'<strong>Top Retailers:</strong> {top_retailer} accounts for the highest chargeback dollar value this period. '
            f'All retailers should be reviewed against their compliance rules before the next shipment cycle.<br><br>'
            f'<strong>Root Cause Analysis:</strong> The most frequent root cause is <strong>{top_rc}</strong>, '
            f'which drives the majority of preventable chargebacks. {top_carrier} is the top carrier involved in chargeback-linked shipments. '
            f'The {top_region} region shows the highest geographic concentration of chargebacks.<br><br>'
            f'<strong>Recommended Actions:</strong><br>'
            f'1. File disputes on all {critical_count} cases with deadlines under 10 days — assign to chargeback analyst today.<br>'
            f'2. Implement ASN pre-shipment validation gate to eliminate {top_rc} chargebacks — estimated 80% reduction within 60 days.<br>'
            f'3. Conduct {top_carrier} carrier compliance review and add to performance scorecard for Q4 QBR.<br>'
            f'<div style="margin-top:16px;padding-top:12px;border-top:1px solid #E2E8F0;font-size:11px;color:#718096;">'
            f'Prepared by: Returns &amp; Claims Control Tower &nbsp;|&nbsp; '
            f'Review period: {(datetime.now()-timedelta(days=7)).strftime("%b %d")} – {datetime.now().strftime("%b %d, %Y")}'
            f'</div></div>'
        )
        st.markdown(summary_html, unsafe_allow_html=True)

        st.download_button(
            "⬇️ Download Chargeback Executive Summary",
            data=f"NEWAGE PRODUCTS — WEEKLY CHARGEBACK REPORT\n{datetime.now().strftime('%B %d, %Y')}\n\n"
                 f"Total Exposure: ${total_val:,.0f}\nUnder Dispute: ${disputed_val:,.0f}\n"
                 f"Recovered: ${recovered_val:,.0f}\nNet Loss: ${net_loss:,.0f}\n\n"
                 f"Top Retailer: {top_retailer}\nTop Root Cause: {top_rc}\n"
                 f"Top Carrier: {top_carrier}\nTop Region: {top_region}\n"
                 f"Critical Deadline Cases: {critical_count}",
            file_name=f"NewAge_Chargeback_Summary_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )
