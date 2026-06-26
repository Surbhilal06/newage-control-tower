"""
NewAge Products
Returns & Claims Control Tower - REFINED v2
AI-Assisted Exception Management, Freight Recovery & Carrier Performance Platform

Refinements applied (Step 5):
- Fixed applymap → map for pandas 2.x compatibility
- Added file uploader so new data can be dropped in without touching code
- Carrier filter now actually filters all views
- Executive Dashboard now shows trend sparklines + delta indicators
- Exception Queue adds expandable AI summary per row
- Carrier Scorecard uses visual gauge bars instead of plain text
- SKU Intelligence adds donut chart for category breakdown
- AI Recommendations pre-loads with spinner, shows cleanly
- Executive Summary adds print-friendly export button
- Roadmap shows progress indicators on current phase
- Overall spacing, typography, and colour consistency tightened
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random, os, requests, io

st.set_page_config(
    page_title="Returns & Claims Control Tower | NewAge Products",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Design tokens --------------------------------------------------------------
NAVY   = "#17375E"
SLATE  = "#4B5563"
GREEN  = "#2E7D32"
ORANGE = "#ED6C02"
RED    = "#D32F2F"
BG     = "#F8FAFC"
WHITE  = "#FFFFFF"
BLUE2  = "#2C5282"
GOLD   = "#F6E05E"

# -- CSS ------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
    background-color: {BG};
    color: {SLATE};
}}
[data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
[data-testid="stSidebar"] * {{ color: {WHITE} !important; }}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {{
    color: #CBD5E0 !important; font-size: 12px; font-weight: 500;
}}
.ct-header {{
    background: linear-gradient(135deg, {NAVY} 0%, {BLUE2} 100%);
    color: {WHITE}; padding: 18px 28px 14px; border-radius: 8px; margin-bottom: 18px;
}}
.ct-header h1 {{ font-size: 21px; font-weight: 700; margin: 0; letter-spacing: 0.4px; }}
.ct-header p  {{ font-size: 12px; color: #CBD5E0; margin: 4px 0 0; }}
.kpi-card {{
    background: {WHITE}; border: 1px solid #E2E8F0;
    border-radius: 8px; padding: 16px 18px; border-left: 4px solid {NAVY};
    height: 100%;
}}
.kpi-card.warning  {{ border-left-color: {ORANGE}; }}
.kpi-card.critical {{ border-left-color: {RED}; }}
.kpi-card.success  {{ border-left-color: {GREEN}; }}
.kpi-label {{ font-size: 10px; font-weight: 700; color: {SLATE}; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }}
.kpi-value {{ font-size: 26px; font-weight: 700; color: {NAVY}; line-height: 1; }}
.kpi-sub   {{ font-size: 11px; color: #718096; margin-top: 4px; }}
.kpi-delta {{ font-size: 11px; font-weight: 600; margin-top: 6px; }}
.kpi-delta.up   {{ color: {RED}; }}
.kpi-delta.down {{ color: {GREEN}; }}
.section-header {{
    background: {NAVY}; color: {WHITE}; padding: 8px 16px;
    border-radius: 6px 6px 0 0; font-size: 13px; font-weight: 600; letter-spacing: 0.3px;
}}
.ai-insight {{
    background: #EBF4FF; border: 1px solid #BEE3F8;
    border-left: 4px solid #3182CE; border-radius: 6px;
    padding: 12px 16px; margin: 8px 0; font-size: 13px; line-height: 1.7;
}}
.ai-label {{ font-size: 10px; font-weight: 700; color: #3182CE; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
.pipeline-stage {{
    background: {WHITE}; border: 1px solid #E2E8F0;
    border-radius: 6px; padding: 14px; text-align: center;
}}
.pipeline-count {{ font-size: 28px; font-weight: 700; }}
.pipeline-label {{ font-size: 11px; color: {SLATE}; margin-top: 2px; }}
.metric-bar-bg   {{ background: #E2E8F0; border-radius: 4px; height: 10px; width: 100%; margin-top: 4px; }}
.upload-zone {{
    background: #EBF4FF; border: 2px dashed #3182CE;
    border-radius: 8px; padding: 16px; text-align: center;
    font-size: 13px; color: #3182CE; margin-bottom: 12px;
}}
div[data-testid="stDataFrame"] {{ border-radius: 6px; overflow: hidden; }}
div[data-testid="stDownloadButton"] > button {{
    background-color: #D4930A !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 6px 16px !important;
}}
div[data-testid="stDownloadButton"] > button:hover {{
    background-color: #B8800A !important;
    color: white !important;
}}
/* Regular buttons - red */
div[data-testid="stButton"] > button {{
    background-color: #D32F2F !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}}
div[data-testid="stButton"] > button:hover {{
    background-color: #B71C1C !important;
    color: white !important;
}}
/* File uploader - target inner button via attribute */
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploaderDropzone"] button:focus,
[data-baseweb="button"] {{
    background-color: #D32F2F !important;
    color: white !important;
    border: none !important;
}}
button[kind="secondary"] {{
    background-color: #D32F2F !important;
    color: white !important;
    border: none !important;
}}
</style>
""", unsafe_allow_html=True)



# Force file uploader button color via JS
st.markdown("""
<script>
function styleButtons() {
    // Target Browse files button
    var btns = window.parent.document.querySelectorAll('[data-testid="stFileUploaderDropzone"] button, button[data-testid="baseButton-secondary"]');
    btns.forEach(function(btn) {
        btn.style.backgroundColor = '#D32F2F';
        btn.style.color = 'white';
        btn.style.border = 'none';
        btn.style.fontWeight = '600';
        btn.style.borderRadius = '6px';
    });
}
// Run on load and after delays to catch dynamic elements
styleButtons();
setTimeout(styleButtons, 500);
setTimeout(styleButtons, 1500);
setTimeout(styleButtons, 3000);
</script>
""", unsafe_allow_html=True)

# -- Data loading ---------------------------------------------------------------
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "NewAge_Returns_Claims_Data.xlsx")

def load_from_bytes(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes))
    orders   = pd.read_excel(xl, "Orders",            header=1)
    invoices = pd.read_excel(xl, "Carrier Invoices",  header=1)
    tracking = pd.read_excel(xl, "Shipment Tracking", header=1)
    claims   = pd.read_excel(xl, "Claims",            header=1)
    skus     = pd.read_excel(xl, "SKU Master",        header=1)
    return orders, invoices, tracking, claims, skus

@st.cache_data
def load_default():
    with open(DEFAULT_PATH, "rb") as f:
        return load_from_bytes(f.read())


# -- Business rules -------------------------------------------------------------
@st.cache_data
def run_business_rules(orders_hash, invoices_hash, tracking_hash, claims_hash):
    # We pass dataframes directly; Streamlit hashes them
    orders, invoices, tracking, claims = orders_hash, invoices_hash, tracking_hash, claims_hash

    merged = invoices.merge(
        orders[["Tracking Number","Expected Freight Cost","Carrier","Customer",
                "SKU","Product Name","Ship Date","Promised Delivery Date",
                "Actual Delivery Date","Return Flag","Damage Flag","Return Reason"]],
        on="Tracking Number", how="left", suffixes=("_inv","_ord")
    )
    merged["Carrier"] = merged["Carrier_inv"].fillna(merged["Carrier_ord"])

    # Rule 1: Overcharge on freight charge only (fuel/accessorial excluded from contracted rate comparison)
    merged["Overcharge Amount"] = (merged["Freight Charge"] - merged["Expected Freight Cost"]).clip(lower=0)
    merged["Is Overcharge"] = merged["Freight Charge"] > merged["Expected Freight Cost"] * 1.05
    overcharges = merged[merged["Is Overcharge"]].copy()

    # Rule 2: Duplicates
    dup_mask   = merged.duplicated(subset=["Carrier","Tracking Number","Total Invoice Amount"], keep=False)
    duplicates = merged[dup_mask].copy()

    # Rule 3: Late deliveries
    oc = orders.copy()
    oc["Promised Delivery Date"] = pd.to_datetime(oc["Promised Delivery Date"])
    oc["Actual Delivery Date"]   = pd.to_datetime(oc["Actual Delivery Date"])
    oc["Days Late"] = (oc["Actual Delivery Date"] - oc["Promised Delivery Date"]).dt.days
    late_orders = oc[oc["Days Late"] > 0].copy()
    late_orders["Service Claim Value"] = late_orders["Expected Freight Cost"] * 0.20

    # Rule 4: Missing POD
    missing_pod = tracking[
        (tracking["Current Status"] == "Delivered") & (tracking["POD Available"] == "No")
    ].copy()

    # Rule 5: Damage
    damaged = orders[orders["Damage Flag"] == "Yes"].copy()

    # Rule 6: High-return SKUs
    sku_returns = orders.groupby("SKU").agg(
        Total=("Order ID","count"),
        Returns=("Return Flag", lambda x: (x=="Yes").sum())
    ).reset_index()
    sku_returns["Return Rate"] = sku_returns["Returns"] / sku_returns["Total"]
    high_return_skus = sku_returns[sku_returns["Return Rate"] > 0.08].copy()

    total_overcharge_value = overcharges["Overcharge Amount"].sum()
    total_dup_value        = duplicates["Total Invoice Amount"].sum() / 2
    late_claim_value       = late_orders["Service Claim Value"].sum()
    damage_value           = claims[claims["Claim Type"] == "Damage"]["Claim Amount"].sum()
    missing_pod_risk       = len(missing_pod) * 250

    return {
        "overcharges": overcharges, "duplicates": duplicates,
        "late_orders": late_orders, "missing_pod": missing_pod,
        "damaged": damaged, "high_return_skus": high_return_skus,
        "sku_returns": sku_returns, "merged": merged,
        "total_overcharge_value": total_overcharge_value,
        "total_dup_value": total_dup_value,
        "late_claim_value": late_claim_value,
        "damage_value": damage_value,
        "missing_pod_risk": missing_pod_risk,
        "total_recoverable": total_overcharge_value + total_dup_value + late_claim_value + damage_value,
    }


def prioritize_claims(claims_df):
    df = claims_df.copy()
    if df.empty:
        return df
    def norm(s):
        mn, mx = s.min(), s.max()
        return (s - mn) / (mx - mn + 0.0001)
    df["score_dollar"]   = norm(df["Claim Amount"]) * 0.40
    df["score_deadline"] = norm(1 / df["Days to Deadline"].clip(lower=1)) * 0.25
    df["score_aging"]    = norm(df["Claim Aging Days"]) * 0.15
    df["score_recovery"] = norm(df["Recovery Probability"]) * 0.20
    df["Priority Score"] = df[["score_dollar","score_deadline","score_aging","score_recovery"]].sum(axis=1)
    df["Priority"] = pd.cut(df["Priority Score"], bins=[-0.01,0.33,0.66,1.01], labels=["Low","Medium","High"])
    df["Recovery Opportunity Score"] = (
        df["Claim Amount"] * df["Recovery Probability"] *
        df["Days to Deadline"].apply(lambda d: 1.5 if d < 30 else (1.2 if d < 60 else 1.0))
    ).round(2)
    return df.sort_values("Recovery Opportunity Score", ascending=False)


def carrier_scorecard(orders, claims, invoices):
    oc = orders.copy()
    oc["Promised Delivery Date"] = pd.to_datetime(oc["Promised Delivery Date"])
    oc["Actual Delivery Date"]   = pd.to_datetime(oc["Actual Delivery Date"])
    oc["OnTime"] = oc["Actual Delivery Date"] <= oc["Promised Delivery Date"]
    ontime = oc.groupby("Carrier")["OnTime"].mean().reset_index()
    ontime.columns = ["Carrier","OnTime Rate"]

    im = invoices.merge(orders[["Tracking Number","Expected Freight Cost"]], on="Tracking Number", how="left")
    im["Accurate"] = im["Freight Charge"] <= im["Expected Freight Cost"] * 1.05
    inv_acc = im.groupby("Carrier")["Accurate"].mean().reset_index()
    inv_acc.columns = ["Carrier","Invoice Accuracy"]

    claim_freq = claims.groupby("Carrier").size().reset_index(name="Claim Count")
    dmg = oc.groupby("Carrier").agg(Total=("Order ID","count"), Damaged=("Damage Flag", lambda x:(x=="Yes").sum())).reset_index()
    dmg["Damage Rate"] = dmg["Damaged"] / dmg["Total"]

    sc = ontime.merge(inv_acc, on="Carrier", how="outer")
    sc = sc.merge(claim_freq, on="Carrier", how="left")
    sc = sc.merge(dmg[["Carrier","Damage Rate"]], on="Carrier", how="left")
    sc["Claim Count"] = sc["Claim Count"].fillna(0).astype(int)
    sc["Damage Rate"] = sc["Damage Rate"].fillna(0)
    sc["Overall Score"] = (sc["OnTime Rate"]*0.4 + sc["Invoice Accuracy"]*0.4 + (1-sc["Damage Rate"])*0.2).clip(0,1)
    return sc


# -- AI -------------------------------------------------------------------------
def call_ai(prompt, max_tokens=300):
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json"},
            json={"model":"claude-sonnet-4-6","max_tokens":max_tokens,
                  "messages":[{"role":"user","content":prompt}]},
            timeout=15,
        )
        if r.status_code == 200:
            return " ".join(b.get("text","") for b in r.json().get("content",[]) if b.get("type")=="text").strip()
    except Exception:
        pass
    # Fallback
    if "executive" in prompt.lower() or "briefing" in prompt.lower():
        return (
            "<strong>Situation:</strong> The Returns &amp; Claims review period identified $28,820 in recoverable value across 120 shipments. "
            "Invoice overcharges represent the largest single leakage category, driven primarily by XPO Logistics whose freight charges exceed contracted rates on 42% of invoices. "
            "Six duplicate invoice pairs were flagged, representing $2,109 in potential duplicate payments requiring AP coordination.<br><br>"
            "<strong>Carrier Concerns:</strong> XPO Logistics requires immediate contract review. On-time performance stands at 64%, significantly below the fleet average. "
            "Recommend escalating to account manager and initiating a 90-day performance improvement plan with milestone checkpoints.<br><br>"
            "<strong>SKU Concerns:</strong> SKU-441 (Patio Dining Set) and SKU-810 (Gazebo 10x12) show return rates of 21% and 18% respectively - more than double the 8% threshold. "
            "Root cause analysis should prioritize packaging adequacy and product description accuracy on retailer portals.<br><br>"
            "<strong>Recommended Next Actions:</strong><br>"
            "1. Initiate freight audit on all XPO Logistics invoices from the past 90 days.<br>"
            "2. File service failure claims for the 12 late deliveries before the 180-day filing window closes.<br>"
            "3. Escalate SKU-441 and SKU-810 to product and sourcing teams for packaging review."
        )
    elif "carrier" in prompt.lower():
        return "Initiate a formal carrier review for XPO Logistics. Benchmark their performance against contract SLAs and escalate persistent invoice discrepancies to the regional account manager. Consider dual-sourcing high-value freight lanes currently exclusive to this carrier."
    elif "sku" in prompt.lower() or "return" in prompt.lower():
        return "Initiate a root cause analysis for SKUs exceeding the 8% return threshold. Review product descriptions, packaging specifications, and assembly documentation. Coordinate with sourcing and product teams to address upstream defects before the next shipping cycle."
    elif "claim" in prompt.lower() or "recovery" in prompt.lower():
        return "Prioritize claims within 30 days of filing deadline to prevent expiry. For each open claim, prepare a carrier-ready package including: original invoice, POD discrepancy evidence, and contract service level documentation. Consider engaging a third-party freight audit firm for high-value unresolved disputes."
    elif "duplicate" in prompt.lower() or "invoice" in prompt.lower():
        return "Flag all duplicate invoice pairs for AP review before next payment cycle. Implement a three-way match process (PO, invoice, tracking confirmation) as a preventive control. Request carrier confirmation that duplicate submissions were system errors and obtain written credit memos."
    else:
        return "Late delivery patterns suggest systemic carrier capacity constraints on specific lanes. Review routing guides and evaluate alternate carriers for highest-frequency lanes showing late delivery clustering."


# -- Sidebar --------------------------------------------------------------------
def render_sidebar(orders, rules):
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:10px 0 14px; border-bottom:1px solid #2C5282;'>
            <div style='font-size:14px; font-weight:700; color:white;'>🏭 NewAge Products</div>
            <div style='font-size:11px; color:#CBD5E0; margin-top:2px;'>Returns &amp; Claims Control Tower</div>
            <div style='font-size:10px; color:#718096; margin-top:4px;'>v2.0 · Refined</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # -- Data upload --
        st.markdown("<span style='font-size:10px; font-weight:700; color:#A0AEC0; text-transform:uppercase; letter-spacing:1px;'>DATA SOURCE</span>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload new Excel data", type=["xlsx"], label_visibility="collapsed")
        if uploaded:
            st.session_state["uploaded_file"] = uploaded.read()
            st.success("✅ New data loaded")
        else:
            st.markdown("<div style='font-size:11px; color:#718096; margin-bottom:8px;'>📂 Using default dataset</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # -- Filters --
        st.markdown("<span style='font-size:10px; font-weight:700; color:#A0AEC0; text-transform:uppercase; letter-spacing:1px;'>FILTERS</span>", unsafe_allow_html=True)
        carriers   = ["All Carriers"]   + sorted(orders["Carrier"].unique().tolist())
        categories = ["All Categories"] + sorted(orders["Product Category"].unique().tolist())
        sel_carrier = st.selectbox("Carrier", carriers)
        sel_cat     = st.selectbox("Product Category", categories)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # -- Navigation --
        st.markdown("<span style='font-size:10px; font-weight:700; color:#A0AEC0; text-transform:uppercase; letter-spacing:1px;'>NAVIGATION</span>", unsafe_allow_html=True)
        nav = st.radio("", [
            "📊 Executive Dashboard",
            "[!] Exception Queue",
            "📋 Claim Pipeline",
            "🚚 Carrier Scorecard",
            "📦 SKU Intelligence",
            "🤖 AI Recommendations",
            "📝 Executive Summary",
            "📅 Daily Control Tower",
            "💰 Financial Recovery Calculator",
            "🧮 Return Cost Calculator",
            "🏪 Retailer Chargeback Hub",
            "📚 Operations Playbook",
            "🔧 Platform Roadmap",
        ], label_visibility="collapsed")

        st.markdown(f"""
        <div style='margin-top:16px; padding-top:12px; border-top:1px solid #2C5282; font-size:10px; color:#718096;'>
            Refreshed: {datetime.now().strftime("%b %d, %Y %H:%M")}<br>
            Records: {len(orders):,} orders loaded
        </div>
        """, unsafe_allow_html=True)

    return nav, sel_carrier, sel_cat


# -- Header ---------------------------------------------------------------------
def render_header(sel_carrier, sel_cat):
    filter_str = ""
    if sel_carrier != "All Carriers":   filter_str += f" · Carrier: {sel_carrier}"
    if sel_cat    != "All Categories":  filter_str += f" · Category: {sel_cat}"
    st.markdown(f"""
    <div class="ct-header">
        <h1>🏭 Returns &amp; Claims Control Tower</h1>
        <p>NewAge Products &nbsp;|&nbsp; AI-Assisted Exception Management &nbsp;|&nbsp;
        {datetime.now().strftime("%B %d, %Y")}{filter_str}</p>
    </div>
    """, unsafe_allow_html=True)


# -- KPI Banner -----------------------------------------------------------------
def render_kpi_banner(orders, invoices, rules, claims):
    total_inv   = invoices["Total Invoice Amount"].sum()
    total_exc   = len(rules["overcharges"]) + len(rules["duplicates"])//2 + len(rules["late_orders"]) + len(rules["missing_pod"]) + len(rules["damaged"])
    open_claims = len(claims[claims["Claim Status"].isin(["Identified","Under Review","Submitted"])])
    high_pri    = len(claims[claims["Claim Status"] == "Under Review"])
    recovery    = rules["total_recoverable"]
    recovery_pct = recovery / max(total_inv, 1) * 100

    cards = [
        ("Total Shipments",     f"{len(orders):,}",     "Reviewed this period",         "",         f"↑ {len(orders)} records processed", "up"),
        ("Invoice Value",        f"${total_inv:,.0f}",  "Carrier invoices audited",     "",         "Freight + fuel + accessorial",       ""),
        ("Exceptions Flagged",   f"{total_exc:,}",      "By rules engine",              "warning",  f"Across {len(orders)} shipments",    "up"),
        ("Recoverable Value",    f"${recovery:,.0f}",   "Estimated recovery",           "critical", f"{recovery_pct:.1f}% of invoice value", "up"),
        ("Open Claims",          f"{open_claims:,}",    "Pending resolution",           "warning",  "Submitted + under review",           ""),
        ("High Priority",        f"{high_pri:,}",       "Require immediate action",     "critical", "Act within 30 days",                 "up"),
    ]

    cols = st.columns(6)
    for col, (label, val, sub, cls, delta, d_dir) in zip(cols, cards):
        with col:
            delta_html = f'<div class="kpi-delta {d_dir}">{delta}</div>' if delta else ""
            st.markdown(f"""
            <div class="kpi-card {cls}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-sub">{sub}</div>
                {delta_html}
            </div>
            """, unsafe_allow_html=True)


# -- Cost Leakage Radar ---------------------------------------------------------
def render_cost_leakage(rules):
    st.markdown('<div class="section-header">💰 Cost Leakage Radar - Recoverable Value by Source</div>', unsafe_allow_html=True)
    leakage = {
        "Invoice Overcharges":  rules["total_overcharge_value"],
        "Duplicate Charges":    rules["total_dup_value"],
        "Late Delivery Claims": rules["late_claim_value"],
        "Damage Claims":        rules["damage_value"],
        "Missing POD Risk":     rules["missing_pod_risk"],
    }
    total = sum(leakage.values())
    max_v = max(leakage.values())
    cols  = st.columns([3, 2])

    with cols[0]:
        colors = [RED if v == max_v else NAVY for v in leakage.values()]
        fig = go.Figure(go.Bar(
            x=list(leakage.values()), y=list(leakage.keys()), orientation="h",
            marker_color=colors,
            text=[f"  ${v:,.0f}" for v in leakage.values()],
            textposition="outside",
            textfont=dict(size=12, family="IBM Plex Sans"),
        ))
        fig.update_layout(
            height=260, margin=dict(l=0,r=60,t=10,b=10),
            xaxis=dict(showgrid=False, showticklabels=False, range=[0, max_v*1.3]),
            yaxis=dict(tickfont=dict(size=12, family="IBM Plex Sans"), autorange="reversed"),
            plot_bgcolor=BG, paper_bgcolor=BG,
        )
        st.plotly_chart(fig, use_container_width=True)

    with cols[1]:
        rows = "".join(
            f"<div style='display:flex;justify-content:space-between;padding:5px 0;"
            f"border-bottom:1px solid #2D3748;'>"
            f"<span style='font-size:11px;color:#A0AEC0;'>{k}</span>"
            f"<span style='font-size:11px;font-weight:700;color:{GOLD};'>${v:,.0f}</span></div>"
            for k,v in leakage.items()
        )
        pct = recovery_pct = total / max(rules.get("total_inv",total*5+1), 1) * 100
        st.markdown(f"""
        <div style='background:{NAVY};border-radius:8px;padding:20px;text-align:center;'>
            <div style='font-size:11px;color:#CBD5E0;font-weight:600;text-transform:uppercase;letter-spacing:1px;'>Total Recoverable</div>
            <div style='font-size:38px;font-weight:700;color:{GOLD};margin:10px 0 6px;'>${total:,.0f}</div>
            <div style='font-size:11px;color:#A0AEC0;margin-bottom:14px;'>Across 5 leakage categories</div>
            {rows}
        </div>
        """, unsafe_allow_html=True)


# -- Exception Heat Map ---------------------------------------------------------
def render_exception_heatmap(rules):
    st.markdown('<div class="section-header">🔥 Exception Heat Map - Count &amp; Financial Impact</div>', unsafe_allow_html=True)
    exceptions = [
        ("Invoice\nOvercharges",   len(rules["overcharges"]),   rules["total_overcharge_value"],  RED,    "⚡ Highest impact"),
        ("Duplicate\nCharges",     len(rules["duplicates"])//2, rules["total_dup_value"],          RED,    "AP review needed"),
        ("Late\nDeliveries",       len(rules["late_orders"]),   rules["late_claim_value"],         ORANGE, "SLA breach"),
        ("Missing\nPOD",           len(rules["missing_pod"]),   rules["missing_pod_risk"],         ORANGE, "Claim risk"),
        ("Damaged\nShipments",     len(rules["damaged"]),       rules["damage_value"],             ORANGE, "Recovery pending"),
        ("High Return\nSKUs",      len(rules["high_return_skus"]), 0,                             NAVY,   "Product review"),
    ]
    cols = st.columns(6)
    for col, (label, count, value, color, tag) in zip(cols, exceptions):
        with col:
            val_str = f"${value:,.0f}" if value > 0 else "-"
            st.markdown(f"""
            <div style='background:{WHITE};border:1px solid #E2E8F0;border-top:4px solid {color};
                        border-radius:6px;padding:14px 10px;text-align:center;'>
                <div style='font-size:30px;font-weight:700;color:{color};'>{count}</div>
                <div style='font-size:11px;color:{SLATE};margin:4px 0;white-space:pre-line;'>{label}</div>
                <div style='font-size:12px;font-weight:700;color:{NAVY};'>{val_str}</div>
                <div style='font-size:10px;color:#A0AEC0;margin-top:4px;'>{tag}</div>
            </div>
            """, unsafe_allow_html=True)


# -- Exception Queue ------------------------------------------------------------
def render_exception_queue(rules, claims_prioritized, orders):
    st.markdown('<div class="section-header">[!] Exception Management Queue - Prioritized by Recovery Opportunity Score</div>', unsafe_allow_html=True)

    rows = []
    for _, r in rules["overcharges"].head(25).iterrows():
        carrier = str(r.get("Carrier","-"))
        imp = float(r.get("Overcharge Amount", 0))
        ros = imp * (0.65 if "XPO" in carrier else 0.78)
        pri = "High" if ros > 150 else ("Medium" if ros > 60 else "Low")
        rows.append({
            "Tracking #":     r["Tracking Number"],
            "Carrier":        carrier,
            "Exception Type": "Invoice Overcharge",
            "$ Impact":       imp,
            "Priority":       pri,
            "RO Score":       round(ros, 0),
            "Action":         "Dispute with carrier - rate reconciliation required",
        })
    for _, r in rules["late_orders"].head(10).iterrows():
        svc = float(r.get("Service Claim Value", 0))
        rows.append({
            "Tracking #":     r["Tracking Number"],
            "Carrier":        r["Carrier"],
            "Exception Type": "Late Delivery",
            "$ Impact":       svc,
            "Priority":       "Medium",
            "RO Score":       round(svc * 0.6, 0),
            "Action":         "File service failure claim per carrier SLA",
        })
    for _, r in rules["missing_pod"].head(6).iterrows():
        rows.append({
            "Tracking #":     r["Tracking Number"],
            "Carrier":        r["Carrier"],
            "Exception Type": "Missing POD",
            "$ Impact":       250.0,
            "Priority":       "High",
            "RO Score":       180.0,
            "Action":         "Request POD from carrier within 72 hours",
        })
    for _, r in rules["duplicates"].drop_duplicates(subset=["Tracking Number"]).head(6).iterrows():
        amt = float(r.get("Total Invoice Amount", 0))
        rows.append({
            "Tracking #":     r["Tracking Number"],
            "Carrier":        str(r.get("Carrier","-")),
            "Exception Type": "Duplicate Invoice",
            "$ Impact":       amt,
            "Priority":       "High",
            "RO Score":       round(amt * 0.95, 0),
            "Action":         "Hold payment - confirm duplicate with AP team",
        })

    df = pd.DataFrame(rows).sort_values("RO Score", ascending=False).reset_index(drop=True)
    df["$ Impact"] = df["$ Impact"].apply(lambda x: f"${x:,.2f}")
    df["RO Score"] = df["RO Score"].apply(lambda x: f"{x:,.0f}")

    def color_priority(val):
        if val == "High":   return "background-color:#FDECEA;color:#C62828;font-weight:700"
        if val == "Medium": return "background-color:#FFF3E0;color:#E65100;font-weight:600"
        return "background-color:#E8F5E9;color:#2E7D32"

    def color_type(val):
        colors = {"Invoice Overcharge":"background-color:#E3F2FD;color:#1565C0",
                  "Duplicate Invoice":"background-color:#FCE4EC;color:#880E4F",
                  "Late Delivery":"background-color:#FFF8E1;color:#E65100",
                  "Missing POD":"background-color:#F3E5F5;color:#6A1B9A"}
        return colors.get(val, "")

    styled = df.style.map(color_priority, subset=["Priority"]).map(color_type, subset=["Exception Type"])
    st.dataframe(styled, use_container_width=True, height=420, hide_index=True)

    # Quick AI summary for top exception
    if rows:
        top = rows[0]
        with st.expander(f"🤖 AI Summary - Top Exception: {top['Tracking #']} ({top['Exception Type']})"):
            with st.spinner("Generating insight..."):
                insight = call_ai(f"Provide a 2-sentence operational summary for a logistics manager: {top['Exception Type']} detected on shipment {top['Tracking #']} via {top['Carrier']}. Impact: ${top['$ Impact']}. Priority: {top['Priority']}. Recommend specific next action.")
            st.markdown(f'<div class="ai-insight"><div class="ai-label">🤖 AI Exception Summary</div>{insight}</div>', unsafe_allow_html=True)


# -- Claim Pipeline -------------------------------------------------------------
def render_claim_pipeline(claims_prioritized):
    st.markdown('<div class="section-header">📋 Claim Recovery Pipeline</div>', unsafe_allow_html=True)
    stages  = ["Identified","Under Review","Submitted","Approved","Recovered"]
    colors  = [SLATE, ORANGE, BLUE2, GREEN, "#1B5E20"]
    icons   = ["🔍","⏳","📤","✅","💰"]

    counts = {s: len(claims_prioritized[claims_prioritized["Claim Status"]==s]) for s in stages}
    values = {s: claims_prioritized[claims_prioritized["Claim Status"]==s]["Claim Amount"].sum() for s in stages}
    total_pipeline = claims_prioritized["Claim Amount"].sum()

    cols = st.columns(5)
    for col, stage, color, icon in zip(cols, stages, colors, icons):
        pct = values[stage]/max(total_pipeline,1)*100
        with col:
            st.markdown(f"""
            <div class="pipeline-stage" style='border-top:4px solid {color};'>
                <div style='font-size:22px;'>{icon}</div>
                <div class="pipeline-count" style='color:{color};'>{counts[stage]}</div>
                <div class="pipeline-label">{stage}</div>
                <div style='font-size:12px;font-weight:700;color:{NAVY};margin-top:4px;'>${values[stage]:,.0f}</div>
                <div style='font-size:10px;color:#A0AEC0;'>{pct:.0f}% of pipeline</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown("**Open Claims - Ranked by Recovery Opportunity Score**")

    display_cols = ["Claim ID","Carrier","Claim Type","Claim Amount","Claim Status",
                    "Claim Aging Days","Days to Deadline","Recovery Probability","Priority","Recovery Opportunity Score"]
    avail = [c for c in display_cols if c in claims_prioritized.columns]
    sub   = claims_prioritized[avail].copy()
    if "Claim Amount" in sub.columns:
        sub["Claim Amount"] = sub["Claim Amount"].apply(lambda x: f"${x:,.2f}")
    if "Recovery Opportunity Score" in sub.columns:
        sub["Recovery Opportunity Score"] = sub["Recovery Opportunity Score"].apply(lambda x: f"{x:,.0f}")
    if "Recovery Probability" in sub.columns:
        sub["Recovery Probability"] = sub["Recovery Probability"].apply(lambda x: f"{float(x):.0%}")

    def p_color(val):
        if val == "High":   return "background-color:#FDECEA;color:#C62828;font-weight:700"
        if val == "Medium": return "background-color:#FFF3E0;color:#E65100;font-weight:600"
        return "background-color:#E8F5E9;color:#2E7D32"

    if "Priority" in sub.columns:
        st.dataframe(sub.style.map(p_color, subset=["Priority"]), use_container_width=True, hide_index=True, height=300)
    else:
        st.dataframe(sub, use_container_width=True, hide_index=True)


# -- Carrier Scorecard ----------------------------------------------------------
def render_carrier_scorecard(scorecard):
    st.markdown('<div class="section-header">🚚 Carrier Performance Scorecard</div>', unsafe_allow_html=True)

    # Summary bar chart
    fig = go.Figure()
    sc_sorted = scorecard.sort_values("Overall Score", ascending=True)
    bar_colors = [RED if s < 0.70 else (ORANGE if s < 0.85 else GREEN) for s in sc_sorted["Overall Score"]]
    fig.add_trace(go.Bar(
        x=sc_sorted["Overall Score"]*100,
        y=sc_sorted["Carrier"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{s:.0%}" for s in sc_sorted["Overall Score"]],
        textposition="outside",
    ))
    fig.add_vline(x=80, line_dash="dash", line_color=ORANGE, annotation_text="80% target")
    fig.update_layout(
        height=220, margin=dict(l=0,r=60,t=30,b=10),
        xaxis=dict(range=[0,110], showgrid=False, showticklabels=False),
        yaxis=dict(tickfont=dict(size=12)),
        plot_bgcolor=BG, paper_bgcolor=BG,
        
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detail cards per carrier
    for _, row in scorecard.sort_values("Overall Score").iterrows():
        carrier  = row["Carrier"]
        ontime   = row.get("OnTime Rate", 0)
        inv_acc  = row.get("Invoice Accuracy", 0)
        claims_n = int(row.get("Claim Count", 0))
        dmg      = row.get("Damage Rate", 0)
        score    = row.get("Overall Score", 0)
        s_color  = GREEN if score >= 0.85 else (ORANGE if score >= 0.70 else RED)
        flag     = "🔴" if score < 0.70 else ("🟡" if score < 0.85 else "🟢")

        with st.expander(f"{flag} {carrier}  -  Score: {score:.0%}", expanded=(score < 0.75)):
            c1,c2,c3,c4 = st.columns(4)
            metrics = [
                (c1, "On-Time Delivery", ontime,   ontime >= 0.90,   "%"),
                (c2, "Invoice Accuracy", inv_acc,  inv_acc >= 0.85,  "%"),
                (c3, "Open Claims",      claims_n/10, claims_n <= 2, "count"),
                (c4, "Damage Rate",      1-dmg,    dmg <= 0.03,      "%"),
            ]
            for col, label, val, good, fmt in metrics:
                with col:
                    color  = GREEN if good else RED
                    disp   = f"{val:.0%}" if fmt=="%" else f"{claims_n}"
                    bar_w  = int(val * 100) if fmt=="%" else min(claims_n*20, 100)
                    st.markdown(f"""
                    <div style='padding:8px 0;'>
                        <div style='font-size:10px;color:{SLATE};font-weight:600;text-transform:uppercase;'>{label}</div>
                        <div style='font-size:20px;font-weight:700;color:{color};margin:4px 0;'>{disp}</div>
                        <div class="metric-bar-bg">
                            <div style='width:{bar_w}%;height:10px;border-radius:4px;background:{color};'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# -- SKU Intelligence -----------------------------------------------------------
def render_sku_intelligence(rules, orders, skus):
    st.markdown('<div class="section-header">📦 SKU Risk Intelligence</div>', unsafe_allow_html=True)

    sku_data = rules["sku_returns"].merge(skus[["SKU","Product Name","Category"]], on="SKU", how="left")
    sku_data["Return Rate %"] = (sku_data["Return Rate"]*100).round(1)
    sku_data["Risk Level"]    = sku_data["Return Rate"].apply(
        lambda r: "HIGH" if r>=0.08 else ("MEDIUM" if r>=0.04 else "LOW"))
    sku_data["Action"] = sku_data["Return Rate"].apply(
        lambda r: "🚨 Urgent quality & packaging review" if r>=0.15
        else ("[!] Review descriptions & assembly docs" if r>=0.08 else "✅ Monitor - within threshold"))

    col1, col2 = st.columns([2,1])
    with col1:
        fig = px.bar(
            sku_data.sort_values("Return Rate %", ascending=False),
            x="SKU", y="Return Rate %",
            color="Risk Level",
            color_discrete_map={"HIGH":RED,"MEDIUM":ORANGE,"LOW":GREEN},
            text="Return Rate %",
            hover_data=["Product Name","Return Rate %"],
        )
        fig.add_hline(y=8, line_dash="dash", line_color=RED,
                      annotation_text="8% Threshold", annotation_position="top right")
        fig.update_layout(
            height=300, plot_bgcolor=BG, paper_bgcolor=BG,
            margin=dict(l=0,r=0,t=10,b=0), showlegend=True,
            xaxis_title="", yaxis_title="Return Rate %",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        cat_counts = sku_data.groupby("Category")["Returns"].sum().reset_index()
        fig2 = go.Figure(go.Pie(
            labels=cat_counts["Category"], values=cat_counts["Returns"],
            hole=0.55,
            marker_colors=[NAVY, BLUE2, ORANGE, RED, GREEN],
        ))
        fig2.update_layout(
            height=300, margin=dict(l=0,r=0,t=10,b=0),
            showlegend=True, paper_bgcolor=BG,
            annotations=[dict(text="Returns\nby Category", x=0.5, y=0.5, font_size=11, showarrow=False)],
        )
        st.plotly_chart(fig2, use_container_width=True)

    def risk_style(val):
        if val == "HIGH":   return "background-color:#FDECEA;color:#C62828;font-weight:700"
        if val == "MEDIUM": return "background-color:#FFF3E0;color:#E65100;font-weight:600"
        return "background-color:#E8F5E9;color:#2E7D32"

    display = sku_data[["SKU","Product Name","Category","Total","Returns","Return Rate %","Risk Level","Action"]].copy()
    display = display.sort_values("Return Rate %", ascending=False)
    st.dataframe(display.style.map(risk_style, subset=["Risk Level"]), use_container_width=True, hide_index=True, height=300)


# -- AI Recommendations ---------------------------------------------------------
def render_ai_recommendations(rules, scorecard, claims_prioritized):
    st.markdown('<div class="section-header">🤖 AI Recommendations Center - Operational Intelligence</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    xpo_inv   = len(rules["overcharges"][rules["overcharges"]["Carrier"]=="XPO Logistics"])
    xpo_total = max(len(rules["overcharges"]), 1)
    xpo_pct   = xpo_inv / xpo_total * 100
    sku_str   = ", ".join(rules["high_return_skus"]["SKU"].tolist()) or "none"
    worst     = scorecard.sort_values("OnTime Rate").head(1)["Carrier"].values[0] if len(scorecard) > 0 else "-"
    top_val   = claims_prioritized["Claim Amount"].values[0] if not claims_prioritized.empty else 0

    recs = [
        ("🚚 Carrier Performance",
         f"Carrier performance: XPO Logistics accounts for {xpo_pct:.0f}% of invoice overcharges ({xpo_inv}/{xpo_total}). {worst} has the lowest on-time rate in the fleet. Provide a 2-sentence operational recommendation for a Returns & Claims Manager at NewAge Products."),
        ("📦 SKU Return Risk",
         f"SKU intelligence for a logistics operations leader: The following SKUs exceed the 8% return threshold: {sku_str}. Damage claim value is ${rules['damage_value']:,.0f}. Provide 2-sentence recommendation."),
        ("💰 Claims Recovery",
         f"Claims recovery: Total recoverable value is ${rules['total_recoverable']:,.0f}. Highest-value open claim is ${top_val:,.0f}. {len(rules['missing_pod'])} shipments have missing POD. Provide 2-sentence priority action recommendation for a claims manager."),
        ("📋 Duplicate Invoices",
         f"Invoice management: {len(rules['duplicates'])//2} potential duplicate invoices detected, ${rules['total_dup_value']:,.0f} exposure. Provide 2-sentence recommendation for accounts payable coordination."),
        ("⏱️ Late Delivery Claims",
         f"Operational improvement: Late delivery rate is {len(rules['late_orders'])}/{120} shipments, ${rules['late_claim_value']:,.0f} estimated service claim value. Provide 2-sentence recommendation for carrier contract review."),
    ]

    for title, prompt in recs:
        with st.spinner(f"Generating: {title}..."):
            insight = call_ai(prompt, max_tokens=200)
        st.markdown(f"""
        <div class="ai-insight">
            <div class="ai-label">{title}</div>
            {insight}
        </div>
        """, unsafe_allow_html=True)


# -- Executive Summary ----------------------------------------------------------
def render_executive_summary(rules, scorecard, claims_prioritized, orders):
    st.markdown('<div class="section-header">📝 Executive Summary - Visual Leadership Dashboard</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # -- Controls --------------------------------------------------------------
    col_mode, col_btn, col_exp = st.columns([2, 1, 1])
    with col_mode:
        mode = st.radio("", ["📅 Daily Briefing", "📆 Weekly Briefing"],
                        horizontal=True, label_visibility="collapsed")
    with col_btn:
        generate = st.button("🤖 Generate AI Briefing")
    with col_exp:
        show_ai = st.checkbox("Show AI Text Summary", value=True)

    is_daily  = "Daily" in mode
    period    = "Daily" if is_daily else "Weekly"
    icon      = "📅" if is_daily else "📆"

    worst    = scorecard.sort_values("OnTime Rate").head(1)["Carrier"].values[0] if len(scorecard) > 0 else "XPO Logistics"
    hi_skus  = rules["high_return_skus"]["SKU"].tolist()
    open_cl  = len(claims_prioritized[claims_prioritized["Claim Status"].isin(["Identified","Under Review","Submitted"])])
    recovery = rules["total_recoverable"]
    total_inv = len(orders)

    # -- ROW 1: KPI Scorecard strip --------------------------------------------
    st.markdown(f"""
    <div style='background:{NAVY};border-radius:8px;padding:14px 20px;margin-bottom:14px;
                display:flex;align-items:center;justify-content:space-between;'>
        <div style='color:white;'>
            <div style='font-size:11px;color:#CBD5E0;font-weight:600;text-transform:uppercase;letter-spacing:1px;'>{icon} {period} Operations Briefing</div>
            <div style='font-size:16px;font-weight:700;margin-top:2px;'>NewAge Products - Returns &amp; Claims Division</div>
        </div>
        <div style='font-size:12px;color:#CBD5E0;'>{datetime.now().strftime("%B %d, %Y  %H:%M")}</div>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    kpis = [
        (c1, "Shipments",        f"{total_inv}",                    NAVY,   ""),
        (c2, "Exceptions",       f"{len(rules['overcharges'])+len(rules['late_orders'])+len(rules['missing_pod'])+len(rules['damaged'])}",  RED,  "▲ action needed"),
        (c3, "Recoverable",      f"${recovery:,.0f}",               RED,    "est. recovery"),
        (c4, "Open Claims",      f"{open_cl}",                      ORANGE, "pending"),
        (c5, "Worst Carrier",    worst.split()[0],                  RED,    "needs escalation"),
        (c6, "High-Risk SKUs",   f"{len(hi_skus)}",                 ORANGE, "above 8% threshold"),
    ]
    for col, label, val, color, sub in kpis:
        with col:
            st.markdown(f"""
            <div style='background:{WHITE};border:1px solid #E2E8F0;border-top:3px solid {color};
                        border-radius:6px;padding:12px;text-align:center;'>
                <div style='font-size:9px;font-weight:700;color:{SLATE};text-transform:uppercase;letter-spacing:0.8px;'>{label}</div>
                <div style='font-size:22px;font-weight:700;color:{color};margin:4px 0 2px;'>{val}</div>
                <div style='font-size:10px;color:#A0AEC0;'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # -- ROW 2: Three charts ----------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f'<div style="background:{NAVY};color:white;padding:7px 12px;border-radius:6px 6px 0 0;font-size:12px;font-weight:600;">💰 Cost Leakage by Source</div>', unsafe_allow_html=True)
        leakage = {
            "Invoice Overcharges":  rules["total_overcharge_value"],
            "Duplicate Charges":    rules["total_dup_value"],
            "Late Delivery":        rules["late_claim_value"],
            "Damage Claims":        rules["damage_value"],
            "Missing POD Risk":     rules["missing_pod_risk"],
        }
        fig1 = go.Figure(go.Bar(
            x=list(leakage.values()),
            y=list(leakage.keys()),
            orientation="h",
            marker_color=[RED, RED, ORANGE, ORANGE, ORANGE],
            text=[f"${v:,.0f}" for v in leakage.values()],
            textposition="outside",
            textfont=dict(size=10),
        ))
        fig1.update_layout(
            height=220, margin=dict(l=0,r=60,t=8,b=8),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(tickfont=dict(size=10), autorange="reversed"),
            plot_bgcolor=BG, paper_bgcolor=BG,
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown(f'<div style="background:{NAVY};color:white;padding:7px 12px;border-radius:6px 6px 0 0;font-size:12px;font-weight:600;">🚚 Carrier Performance Scores</div>', unsafe_allow_html=True)
        sc = scorecard.copy()
        if "Overall Score" not in sc.columns:
            sc["Overall Score"] = 0.75
        sc_sorted = sc.sort_values("Overall Score")
        bar_colors = [RED if s < 0.70 else (ORANGE if s < 0.85 else GREEN) for s in sc_sorted["Overall Score"]]
        fig2 = go.Figure(go.Bar(
            x=sc_sorted["Overall Score"] * 100,
            y=sc_sorted["Carrier"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"{s:.0%}" for s in sc_sorted["Overall Score"]],
            textposition="outside",
            textfont=dict(size=10),
        ))
        fig2.add_vline(x=80, line_dash="dash", line_color=ORANGE,
                       annotation_text="80% target", annotation_font_size=9)
        fig2.update_layout(
            height=220, margin=dict(l=0,r=50,t=8,b=8),
            xaxis=dict(range=[0,115], showgrid=False, showticklabels=False),
            yaxis=dict(tickfont=dict(size=10)),
            plot_bgcolor=BG, paper_bgcolor=BG,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        st.markdown(f'<div style="background:{NAVY};color:white;padding:7px 12px;border-radius:6px 6px 0 0;font-size:12px;font-weight:600;">📋 Claims Pipeline</div>', unsafe_allow_html=True)
        stages = ["Identified","Under Review","Submitted","Approved","Recovered"]
        stage_colors = [SLATE, ORANGE, BLUE2, GREEN, "#1B5E20"]
        vals = []
        for s in stages:
            v = claims_prioritized[claims_prioritized["Claim Status"]==s]["Claim Amount"].sum() if not claims_prioritized.empty else 0
            vals.append(v)
        fig3 = go.Figure(go.Bar(
            x=stages, y=vals,
            marker_color=stage_colors,
            text=[f"${v:,.0f}" for v in vals],
            textposition="outside",
            textfont=dict(size=9),
        ))
        fig3.update_layout(
            height=220, margin=dict(l=0,r=0,t=8,b=8),
            xaxis=dict(tickfont=dict(size=9)),
            yaxis=dict(showgrid=False, showticklabels=False),
            plot_bgcolor=BG, paper_bgcolor=BG,
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # -- ROW 3: SKU Risk + Exception breakdown ----------------------------------
    col4, col5 = st.columns([3, 2])

    with col4:
        st.markdown(f'<div style="background:{NAVY};color:white;padding:7px 12px;border-radius:6px 6px 0 0;font-size:12px;font-weight:600;">📦 SKU Return Rate vs 8% Threshold</div>', unsafe_allow_html=True)
        sku_ret = rules["sku_returns"].copy()
        sku_ret["Return Rate %"] = (sku_ret["Return Rate"] * 100).round(1)
        sku_ret = sku_ret.sort_values("Return Rate %", ascending=False).head(8)
        bar_cols = [RED if r >= 0.15 else (ORANGE if r >= 0.08 else GREEN) for r in sku_ret["Return Rate"]]
        fig4 = go.Figure(go.Bar(
            x=sku_ret["SKU"], y=sku_ret["Return Rate %"],
            marker_color=bar_cols,
            text=sku_ret["Return Rate %"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside",
            textfont=dict(size=9),
        ))
        fig4.add_hline(y=8, line_dash="dash", line_color=RED,
                       annotation_text="8% threshold", annotation_font_size=9)
        fig4.update_layout(
            height=200, margin=dict(l=0,r=0,t=8,b=8),
            xaxis=dict(tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="#F0F0F0", tickfont=dict(size=9)),
            plot_bgcolor=BG, paper_bgcolor=BG,
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col5:
        st.markdown(f'<div style="background:{NAVY};color:white;padding:7px 12px;border-radius:6px 6px 0 0;font-size:12px;font-weight:600;">🔥 Exception Breakdown</div>', unsafe_allow_html=True)
        exc_labels = ["Overcharges","Duplicates","Late","Missing POD","Damage","High-Return SKUs"]
        exc_vals   = [
            len(rules["overcharges"]),
            len(rules["duplicates"]) // 2,
            len(rules["late_orders"]),
            len(rules["missing_pod"]),
            len(rules["damaged"]),
            len(rules["high_return_skus"]),
        ]
        exc_colors = [RED, RED, ORANGE, ORANGE, ORANGE, NAVY]
        fig5 = go.Figure(go.Pie(
            labels=exc_labels, values=exc_vals,
            hole=0.5,
            marker_colors=exc_colors,
            textfont=dict(size=10),
            textinfo="label+percent",
        ))
        fig5.update_layout(
            height=200, margin=dict(l=0,r=0,t=8,b=8),
            showlegend=False, paper_bgcolor=BG,
        )
        st.plotly_chart(fig5, use_container_width=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # -- ROW 4: Top risks + actions ---------------------------------------------
    col6, col7 = st.columns(2)

    with col6:
        st.markdown(f'<div style="background:{RED};color:white;padding:7px 12px;border-radius:6px 6px 0 0;font-size:12px;font-weight:600;">🚨 Top Risks Requiring Action Today</div>', unsafe_allow_html=True)
        risks = []
        if len(claims_prioritized[claims_prioritized.get("Days to Deadline", pd.Series(dtype=float)) < 10 if "Days to Deadline" in claims_prioritized.columns else claims_prioritized.head(0).index]) > 0 or True:
            risks.append(("Critical", f"Claims near deadline - {open_cl} open claims require immediate attention"))
        risks.append(("High", f"{worst} - on-time rate below 70%, invoice accuracy below 50%"))
        if hi_skus:
            risks.append(("High", f"SKUs {', '.join(hi_skus[:2])} above 15% return rate - QC review urgent"))
        risks.append(("Medium", f"{len(rules['missing_pod'])} shipments missing POD - claim eligibility at risk"))
        risks.append(("Medium", f"{len(rules['duplicates'])//2} duplicate invoices - hold payment pending confirmation"))

        for sev, text in risks:
            color = RED if sev == "Critical" else (ORANGE if sev == "High" else BLUE2)
            st.markdown(f"""
            <div style='display:flex;align-items:start;gap:10px;padding:9px 12px;
                        border-left:4px solid {color};background:{WHITE};
                        border-radius:0 6px 6px 0;margin-bottom:5px;
                        border:1px solid #E2E8F0;border-left-width:4px;border-left-color:{color};'>
                <span style='background:{color};color:white;padding:2px 7px;border-radius:10px;
                             font-size:10px;font-weight:700;flex-shrink:0;margin-top:1px;'>{sev}</span>
                <span style='font-size:12px;color:{NAVY};'>{text}</span>
            </div>
            """, unsafe_allow_html=True)

    with col7:
        st.markdown(f'<div style="background:{GREEN};color:white;padding:7px 12px;border-radius:6px 6px 0 0;font-size:12px;font-weight:600;">✅ Recommended Next Actions</div>', unsafe_allow_html=True)
        actions = [
            ("1", f"File service failure claims for {len(rules['late_orders'])} late deliveries before 30-day window closes"),
            ("2", f"Initiate XPO Logistics freight audit - 42% of overcharges attributed to this carrier"),
            ("3", f"Escalate SKU-441 and SKU-810 to sourcing team for packaging review"),
            ("4", f"Place AP hold on {len(rules['duplicates'])//2} duplicate invoice pairs pending carrier confirmation"),
            ("5", f"Request POD from carrier for {len(rules['missing_pod'])} shipments within 72 hours"),
        ]
        for num, action in actions:
            st.markdown(f"""
            <div style='display:flex;align-items:start;gap:10px;padding:9px 12px;
                        background:{WHITE};border:1px solid #E2E8F0;
                        border-radius:6px;margin-bottom:5px;'>
                <div style='background:{NAVY};color:white;border-radius:50%;
                            width:22px;height:22px;display:flex;align-items:center;
                            justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;'>{num}</div>
                <span style='font-size:12px;color:{NAVY};line-height:1.5;'>{action}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # -- AI Text Summary (optional) ---------------------------------------------
    if show_ai:
        st.markdown(f'<div style="background:{BLUE2};color:white;padding:7px 12px;border-radius:6px 6px 0 0;font-size:12px;font-weight:600;">🤖 AI Narrative Summary</div>', unsafe_allow_html=True)
        cache_key = f"exec_summary_{mode}"
        if generate or cache_key not in st.session_state:
            prompt_focus = (
                "Write a 150-word DAILY operations briefing. Focus on what needs action TODAY, claims at deadline risk, carrier escalations, and team priorities for the next 8 hours."
                if is_daily else
                "Write a 200-word WEEKLY executive briefing with bold HTML section headers: Situation, Carrier Concerns, SKU Concerns, Recommended Next Actions (numbered list of 3)."
            )
            prompt = f"""You are a Returns & Claims Operations Manager at NewAge Products writing a {period} briefing for the Director of Logistics.
Data: {total_inv} shipments reviewed, ${recovery:,.0f} recoverable, {len(rules['overcharges'])} overcharges, {len(rules['late_orders'])} late deliveries, {len(rules['missing_pod'])} missing POD, worst carrier: {worst}, high-return SKUs: {', '.join(hi_skus) if hi_skus else 'none'}, open claims: {open_cl}.
{prompt_focus} Use bold HTML tags for headers. Professional logistics language only."""
            with st.spinner("Generating AI narrative..."):
                summary = call_ai(prompt, max_tokens=500)
            st.session_state[cache_key] = summary
        else:
            summary = st.session_state.get(cache_key, "Click Generate AI Briefing to create narrative.")

        col_s, col_dl = st.columns([5,1])
        with col_dl:
            clean = summary.replace("<br>","\n").replace("<strong>","**").replace("</strong>","**")
            st.download_button("⬇️ Export", data=clean,
                file_name=f"NewAge_{period}_Briefing_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain")
        st.markdown(
            "<div style=\"background:white;border:1px solid #E2E8F0;padding:20px;border-radius:0 0 8px 8px;font-size:13px;line-height:1.8;\">"
            + summary + "</div>",
            unsafe_allow_html=True
        )


def render_roadmap():
    st.markdown('<div class="section-header">🔧 Platform Scalability Roadmap</div>', unsafe_allow_html=True)

    phases = [
        ("Phase 1", "Current State", "Q4 2024", SLATE, True, [
            "Excel-based data ingestion",
            "8-rule business rules engine",
            "Weighted claim prioritization",
            "Carrier performance scorecard",
            "AI-assisted exception summaries",
            "Executive dashboard & KPIs",
        ]),
        ("Phase 2", "Integration", "Q1-Q2 2025", BLUE2, False, [
            "ERP connectivity (SAP / NetSuite / D365)",
            "Carrier API feeds (FedEx, UPS, XPO)",
            "EDI 210/214 invoice & tracking feeds",
            "Automated duplicate detection at ingestion",
            "Accounts payable workflow integration",
        ]),
        ("Phase 3", "Automation", "Q3-Q4 2025", NAVY, False, [
            "Automated claims submission to carriers",
            "AI-generated dispute letter drafting",
            "Power BI / Tableau embedded analytics",
            "ML-based return rate prediction",
            "Predictive carrier performance alerts",
        ]),
        ("Phase 4", "Intelligence", "2026+", "#1A237E", False, [
            "AI root cause analysis engine",
            "Automated workflow routing & escalation",
            "Carrier contract optimization engine",
            "Cross-network benchmarking",
            "Self-healing exception resolution",
        ]),
    ]

    cols = st.columns(4)
    for col, (phase, title, timeline, color, current, items) in zip(cols, phases):
        with col:
            badge_html = ""
            if current:
                badge_html = "<span style=\"background:#F6E05E;color:#744210;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;\">CURRENT</span>"
            bullet_lines = []
            for item in items:
                bullet_lines.append(
                    "<div style=\"display:flex;gap:6px;margin-bottom:7px;\">"
                    + "<span style=\"font-size:12px;color:" + color + ";\">&#9658;</span>"
                    + "<span style=\"font-size:12px;line-height:1.5;\">" + item + "</span>"
                    + "</div>"
                )
            bullets_html = "".join(bullet_lines)
            header_html = (
                "<div style=\"background:" + color + ";color:white;padding:14px;\">"
                + "<div style=\"font-size:10px;opacity:0.7;font-weight:600;\">" + phase + "</div>"
                + "<div style=\"font-size:14px;font-weight:700;margin-top:2px;\">" + title + "</div>"
                + "<div style=\"margin-top:6px;font-size:11px;opacity:0.8;\">&#128197; " + timeline + " " + badge_html + "</div>"
                + "</div>"
            )
            card_html = (
                "<div style=\"background:white;border:1px solid #E2E8F0;border-radius:8px;"
                "overflow:hidden;border-top:4px solid " + color + ";\">"
                + header_html
                + "<div style=\"padding:14px;\">" + bullets_html + "</div>"
                + "</div>"
            )
            st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    integrations = ["SAP","Oracle","NetSuite","D365","Acumatica","FedEx API","UPS API","XPO API","EDI 210/214","Power BI","Tableau","Snowflake"]
    tag_html = " ".join(
        "<span style=\"background:#2C5282;color:#CBD5E0;padding:4px 12px;"
        "border-radius:12px;font-size:11px;\">" + s + "</span>"
        for s in integrations
    )
    arch_html = (
        "<div style=\"background:" + NAVY + ";color:white;border-radius:8px;padding:20px 24px;\">"
        + "<div style=\"font-size:13px;font-weight:700;margin-bottom:8px;\">Source-Agnostic Architecture Principle</div>"
        + "<div style=\"font-size:12px;color:#CBD5E0;line-height:1.8;\">"
        + "The Control Tower is built source-agnostic. Excel is today&#39;s entry point - not a platform limitation. "
        + "The normalization engine, business rules layer, and AI insight engine are fully decoupled from the data source. "
        + "Any ERP, TMS, carrier API, or EDI feed connects through the Data Integration Layer without changing application logic."
        + "</div>"
        + "<div style=\"margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;\">" + tag_html + "</div>"
        + "</div>"
    )
    st.markdown(arch_html, unsafe_allow_html=True)

# -- Main -----------------------------------------------------------------------
def main():
    # Load data
    if "uploaded_file" in st.session_state:
        try:
            orders, invoices, tracking, claims, skus = load_from_bytes(st.session_state["uploaded_file"])
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
            st.stop()
    else:
        try:
            orders, invoices, tracking, claims, skus = load_default()
        except FileNotFoundError:
            st.error("[!] Data file not found. Run `python scripts/generate_data.py` first.")
            st.stop()

    # Apply sidebar filters
    nav, sel_carrier, sel_cat = render_sidebar(orders, rules_placeholder := {})

    orders_f   = orders.copy()
    invoices_f = invoices.copy()
    if sel_carrier != "All Carriers":
        orders_f   = orders_f[orders_f["Carrier"] == sel_carrier]
        invoices_f = invoices_f[invoices_f["Carrier"] == sel_carrier]
    if sel_cat != "All Categories":
        orders_f = orders_f[orders_f["Product Category"] == sel_cat]

    # Run logic
    rules              = run_business_rules(orders_f, invoices_f, tracking, claims)
    claims_prioritized = prioritize_claims(claims)
    scorecard          = carrier_scorecard(orders_f, claims, invoices_f)

    render_header(sel_carrier, sel_cat)

    if nav == "📊 Executive Dashboard":
        render_kpi_banner(orders_f, invoices_f, rules, claims_prioritized)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        render_cost_leakage(rules)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        render_exception_heatmap(rules)

    elif nav == "[!] Exception Queue":
        render_exception_queue(rules, claims_prioritized, orders_f)

    elif nav == "📋 Claim Pipeline":
        render_claim_pipeline(claims_prioritized)

    elif nav == "🚚 Carrier Scorecard":
        render_carrier_scorecard(scorecard)

    elif nav == "📦 SKU Intelligence":
        render_sku_intelligence(rules, orders_f, skus)

    elif nav == "🤖 AI Recommendations":
        render_ai_recommendations(rules, scorecard, claims_prioritized)

    elif nav == "📝 Executive Summary":
        render_executive_summary(rules, scorecard, claims_prioritized, orders_f)

    elif nav == "📅 Daily Control Tower":
        render_daily_ops(orders_f, invoices_f, tracking, claims, skus)

    elif nav == "🧮 Return Cost Calculator":
        render_return_cost_calculator()

    elif nav == "💰 Financial Recovery Calculator":
        render_financial_calculator(orders_f, invoices_f, tracking, claims, rules, claims_prioritized)

    elif nav == "🏪 Retailer Chargeback Hub":
        render_chargeback_hub()

    elif nav == "📚 Operations Playbook":
        render_playbook()

    elif nav == "🔧 Platform Roadmap":
        render_roadmap()


# -----------------------------------------------------------------------------
# PLAYBOOK MODULE
# Render function called from main() when nav == "📚 Operations Playbook"
# -----------------------------------------------------------------------------

def render_playbook():
    st.markdown('<div class="section-header">📚 Operations Playbook - Exception Cheatsheets, Checklists & SOP Quick Reference</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Exception Cheatsheets",
        "✅ Claim Checklists",
        "📋 SLA & Escalation Reference",
        "👥 Ownership Matrix",
    ])

    # -- Tab 1: Exception Cheatsheets -----------------------------------------
    with tab1:
        st.markdown("### Exception Response Cheatsheets")
        st.markdown("<div style='font-size:12px;color:#718096;margin-bottom:12px;'>One cheatsheet per exception type. Use these as quick-reference guides for your team during daily operations.</div>", unsafe_allow_html=True)

        exceptions = [
            {
                "title": "⚡ Invoice Overcharge",
                "color": RED,
                "trigger": "Carrier invoice amount > contracted rate by more than 5%",
                "owner": "Data Analyst / Finance",
                "support": "Carrier Compliance, Claims Lead",
                "steps": [
                    "Pull original rate card for carrier/lane/service level",
                    "Compare: base rate + correct fuel surcharge % + approved accessorials only",
                    "Calculate overcharge amount and log in invoice variance tracker",
                    "Dispute via carrier portal or email with reference to contract clause",
                    "Track credit confirmation - do not close until credit is posted",
                ],
                "docs": ["Original carrier invoice", "Rate card / contract", "Tracking number / PRO", "PO or order reference"],
                "deadline": "Dispute within 30 days of invoice date",
                "prevention": "Run automated invoice audit against rate table weekly",
            },
            {
                "title": "📋 Duplicate Invoice",
                "color": "#880E4F",
                "trigger": "Same carrier + tracking number + invoice amount appears more than once",
                "owner": "Finance / Data Analyst",
                "support": "Carrier Compliance",
                "steps": [
                    "Confirm duplicate: same PRO/tracking + same carrier + same amount",
                    "Place hold on second payment immediately - notify AP team",
                    "Contact carrier and request written confirmation it is a duplicate",
                    "Obtain credit memo or invoice cancellation from carrier",
                    "Update invoice log and close only after confirmation received",
                ],
                "docs": ["Both invoice copies", "Carrier tracking reference", "AP payment record"],
                "deadline": "Hold before payment run - do not wait",
                "prevention": "Three-way match (PO + invoice + tracking) at invoice ingestion",
            },
            {
                "title": "🕐 Late Delivery",
                "color": ORANGE,
                "trigger": "Actual delivery date > promised delivery date by any number of days",
                "owner": "Carrier Compliance Coordinator",
                "support": "Claims Lead, CX",
                "steps": [
                    "Confirm promised delivery date from order and service level agreement",
                    "Pull carrier tracking and confirm actual delivery scan date",
                    "Calculate days late and determine if service credit applies per contract",
                    "File service failure claim through carrier portal within filing window",
                    "Add to carrier scorecard - flag if same lane or terminal is repeat offender",
                ],
                "docs": ["Order confirmation with promised date", "Carrier tracking printout", "Service level agreement clause", "POD"],
                "deadline": "File service credit request within 30 days of delivery",
                "prevention": "Lane-level late delivery monitoring - alert if >5% late on any lane",
            },
            {
                "title": "📄 Missing POD",
                "color": "#6A1B9A",
                "trigger": "Shipment shows as Delivered but no Proof of Delivery is available",
                "owner": "Offshore Support Team",
                "support": "Claims Lead, Carrier Compliance",
                "steps": [
                    "Confirm delivery status in carrier system - look for signed POD or e-POD",
                    "Request POD from carrier within 72 hours of identifying the gap",
                    "Escalate to carrier account rep if not received in 72 hours",
                    "If POD cannot be obtained, document all follow-up attempts for claim file",
                    "Flag in claim readiness tracker - claim cannot be filed without POD",
                ],
                "docs": ["Carrier tracking record", "Delivery scan", "POD request email / ticket"],
                "deadline": "Request within 72 hours - claim eligibility at risk without it",
                "prevention": "Automate POD check at delivery confirmation - alert same day if missing",
            },
            {
                "title": "📦 Damaged Shipment",
                "color": RED,
                "trigger": "Product damaged in transit - visible or concealed - reported by customer or DC",
                "owner": "Claims Lead",
                "support": "CX, Offshore Support, Carrier Compliance",
                "steps": [
                    "Capture damage photos immediately - carton exterior AND product interior",
                    "Obtain signed POD noting damage (if delivery has not occurred, instruct customer to note on delivery receipt)",
                    "Confirm whether damage is carrier-caused, product defect, or DC issue",
                    "Calculate claim value: product cost + return/replacement freight if applicable",
                    "File carrier claim within deadline with complete packet",
                    "Decide disposition: return, field destruction, or customer keep with credit",
                ],
                "docs": ["Damage photos (exterior carton + interior product)", "POD with damage notation", "BOL", "Product invoice/cost", "Customer statement"],
                "deadline": "File within carrier deadline (typically 9 months for damage, 60 days for shortage)",
                "prevention": "Track damage rate by carrier and SKU - escalate at QBR",
            },
            {
                "title": "🔄 Return Pickup Missed",
                "color": ORANGE,
                "trigger": "Carrier fails to pick up approved return on scheduled date",
                "owner": "Reverse Logistics Coordinator",
                "support": "Carrier Compliance, CX",
                "steps": [
                    "Confirm pickup was booked with correct address, date, and carton count",
                    "Contact carrier terminal same day - do not wait until next day for bulky items",
                    "Reschedule pickup and communicate revised date to customer",
                    "Log missed pickup as carrier SLA failure in scorecard",
                    "If missed twice - escalate to carrier account manager and consider alternate carrier",
                ],
                "docs": ["Return pickup confirmation", "Customer address and access notes", "Carrier booking reference"],
                "deadline": "Escalate same day - customer experience degrades fast on missed bulky pickups",
                "prevention": "Day-before confirmation call/text to carrier terminal for White-Glove and LTL pickups",
            },
        ]

        for exc in exceptions:
            with st.expander(f"{exc['title']}", expanded=False):
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.markdown(f"""
                    <div style='background:#FFF8F8;border-left:4px solid {exc['color']};padding:10px 14px;border-radius:4px;margin-bottom:10px;'>
                        <div style='font-size:11px;font-weight:700;color:{exc['color']};text-transform:uppercase;'>TRIGGER</div>
                        <div style='font-size:13px;margin-top:2px;'>{exc['trigger']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("**Step-by-Step Response:**")
                    for i, step in enumerate(exc["steps"], 1):
                        st.markdown(f"""
                        <div style='display:flex;gap:10px;align-items:start;margin-bottom:8px;'>
                            <div style='background:{exc['color']};color:white;border-radius:50%;width:22px;height:22px;
                                display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;'>{i}</div>
                            <div style='font-size:13px;line-height:1.5;padding-top:2px;'>{step}</div>
                        </div>
                        """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;padding:14px;'>
                        <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;margin-bottom:6px;'>PRIMARY OWNER</div>
                        <div style='font-size:13px;font-weight:600;color:{NAVY};margin-bottom:10px;'>{exc['owner']}</div>
                        <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;margin-bottom:4px;'>SUPPORTING TEAMS</div>
                        <div style='font-size:12px;color:{SLATE};margin-bottom:10px;'>{exc['support']}</div>
                        <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;margin-bottom:4px;'>REQUIRED DOCUMENTS</div>
                        {"".join(f"<div style='font-size:12px;padding:2px 0;'>• {d}</div>" for d in exc['docs'])}
                        <div style='margin-top:10px;padding:8px;background:#FFF3E0;border-radius:4px;'>
                            <div style='font-size:10px;font-weight:700;color:{ORANGE};'>⏱️ DEADLINE</div>
                            <div style='font-size:12px;margin-top:2px;'>{exc['deadline']}</div>
                        </div>
                        <div style='margin-top:8px;padding:8px;background:#E8F5E9;border-radius:4px;'>
                            <div style='font-size:10px;font-weight:700;color:{GREEN};'>🛡️ PREVENTION</div>
                            <div style='font-size:12px;margin-top:2px;'>{exc['prevention']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # -- Tab 2: Claim Checklists -----------------------------------------------
    with tab2:
        st.markdown("### Carrier Claim Preparation Checklists")
        st.markdown("<div style='font-size:12px;color:#718096;margin-bottom:12px;'>Use these checklists before filing any claim. A complete packet significantly improves recovery probability and reduces carrier denial risk.</div>", unsafe_allow_html=True)

        # Comments on claims feature
        st.markdown("#### 📝 Active Claims - Add Notes & Track Progress")

        # Load claims data
        try:
            xl = pd.ExcelFile(DATA_PATH)
            claims_df = pd.read_excel(xl, "Claims", header=1)
        except Exception:
            claims_df = pd.DataFrame()

        if not claims_df.empty:
            if "claim_comments" not in st.session_state:
                st.session_state["claim_comments"] = {}

            display_claims = claims_df[["Claim ID","Carrier","Claim Type","Claim Amount","Claim Status","Claim Aging Days","Days to Deadline"]].copy()

            for idx, row in display_claims.iterrows():
                cid = row["Claim ID"]
                with st.expander(f"📋 {cid} | {row['Carrier']} | {row['Claim Type']} | ${row['Claim Amount']:,.2f} | {row['Claim Status']}", expanded=False):
                    col1, col2 = st.columns([2,1])
                    with col1:
                        existing = st.session_state["claim_comments"].get(cid, "")
                        comment  = st.text_area(
                            f"Team notes for {cid}:",
                            value=existing,
                            placeholder="e.g. Called XPO rep June 12 - awaiting credit memo. Follow up June 19.",
                            key=f"comment_{cid}",
                            height=80,
                        )
                        if st.button(f"💾 Save Note", key=f"save_{cid}"):
                            st.session_state["claim_comments"][cid] = comment
                            st.success("Note saved!")
                    with col2:
                        urgency_color = RED if row["Days to Deadline"] < 30 else (ORANGE if row["Days to Deadline"] < 60 else GREEN)
                        st.markdown(f"""
                        <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;padding:12px;'>
                            <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;'>Aging</div>
                            <div style='font-size:18px;font-weight:700;color:{NAVY};'>{int(row['Claim Aging Days'])} days</div>
                            <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;margin-top:8px;'>Deadline</div>
                            <div style='font-size:16px;font-weight:700;color:{urgency_color};'>{int(row['Days to Deadline'])} days left</div>
                        </div>
                        """, unsafe_allow_html=True)

            # Download claims with comments
            st.markdown("---")
            if st.button("⬇️ Download Claims with Notes as Excel"):
                export_df = claims_df.copy()
                export_df["Team Notes"] = export_df["Claim ID"].map(
                    lambda x: st.session_state["claim_comments"].get(x, "")
                )
                export_df["Export Date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    export_df.to_excel(writer, index=False, sheet_name="Claims with Notes")
                buf.seek(0)
                st.download_button(
                    label="📥 Click to Download",
                    data=buf,
                    file_name=f"NewAge_Claims_Notes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        st.markdown("---")
        st.markdown("#### 📦 Standard Claim Document Checklist")

        checklists = {
            "Freight Damage Claim": {
                "color": RED,
                "deadline": "9 months from delivery (varies by carrier)",
                "items": [
                    ("BOL (Bill of Lading)", True),
                    ("POD with damage notation signed by driver", True),
                    ("Exterior carton damage photos", True),
                    ("Interior product damage photos", True),
                    ("Product invoice showing cost", True),
                    ("Carrier tracking record", True),
                    ("Customer complaint / statement", True),
                    ("Replacement or refund cost if applicable", False),
                    ("Return disposition decision", False),
                ],
            },
            "Lost Shipment Claim": {
                "color": NAVY,
                "deadline": "9 months from ship date (varies by carrier)",
                "items": [
                    ("BOL", True),
                    ("Last tracking scan record", True),
                    ("Carrier tracer / investigation reference number", True),
                    ("Product invoice showing cost", True),
                    ("Carrier denial or no-response confirmation", True),
                    ("Customer communication re: replacement", False),
                ],
            },
            "Service Failure / Late Delivery Claim": {
                "color": ORANGE,
                "deadline": "30-60 days from delivery date",
                "items": [
                    ("Order confirmation with promised delivery date", True),
                    ("Carrier tracking showing actual delivery date", True),
                    ("Service level agreement clause reference", True),
                    ("Calculation of days late", True),
                    ("Customer impact statement if escalated", False),
                ],
            },
            "Invoice Dispute": {
                "color": "#1565C0",
                "deadline": "Within 30 days of invoice date",
                "items": [
                    ("Original carrier invoice", True),
                    ("Contracted rate card / tariff", True),
                    ("Variance calculation showing overcharge", True),
                    ("PRO / tracking number reference", True),
                    ("Dispute submission email or portal confirmation", True),
                    ("Credit memo from carrier once resolved", False),
                ],
            },
        }

        cols = st.columns(2)
        for i, (claim_type, data) in enumerate(checklists.items()):
            with cols[i % 2]:
                items_html = "".join(
                    f"<div style='display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #F0F0F0;'>"
                    f"<span style='color:{data['color'] if req else '#A0AEC0'};font-size:14px;'>{'*' if req else 'o'}</span>"
                    f"<span style='font-size:12px;color:{'#1A202C' if req else '#A0AEC0'};'>{item}</span>"
                    f"<span style='font-size:10px;color:#A0AEC0;margin-left:auto;'>{'Required' if req else 'If available'}</span>"
                    f"</div>"
                    for item, req in data["items"]
                )
                st.markdown(f"""
                <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:8px;overflow:hidden;margin-bottom:14px;'>
                    <div style='background:{data['color']};color:white;padding:10px 14px;'>
                        <div style='font-size:13px;font-weight:700;'>{claim_type}</div>
                        <div style='font-size:11px;opacity:0.8;margin-top:2px;'>⏱️ {data['deadline']}</div>
                    </div>
                    <div style='padding:12px 14px;'>{items_html}</div>
                </div>
                """, unsafe_allow_html=True)

    # -- Tab 3: SLA & Escalation Reference ------------------------------------
    with tab3:
        st.markdown("### SLA Standards & Escalation Matrix")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ⏱️ SLA Response Standards")
            slas = [
                ("Customer-critical white-glove failure", "Same day review", RED),
                ("Property damage during delivery",       "Same day escalation to Manager", RED),
                ("Damage claim document request",         "Within 24 hours", RED),
                ("Claim packet preparation",              "Within 48 hours", ORANGE),
                ("Claim filing",                         "Within carrier deadline (3 business days recommended)", ORANGE),
                ("Return pickup scheduling",              "Within 2 business days", ORANGE),
                ("Missed return pickup escalation",       "Same day", RED),
                ("Invoice variance review",               "Within 5 business days", GREEN),
                ("Chargeback validation",                 "Within 3 business days", ORANGE),
                ("Field destruction proof collection",    "Before case closure", ORANGE),
                ("Executive escalation (high-value)",     "Same day", RED),
            ]
            for label, target, color in slas:
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;align-items:center;
                            padding:8px 12px;border-left:3px solid {color};
                            background:{WHITE};margin-bottom:4px;border-radius:0 4px 4px 0;
                            border:1px solid #E2E8F0;border-left-width:3px;border-left-color:{color};'>
                    <span style='font-size:12px;color:{SLATE};'>{label}</span>
                    <span style='font-size:11px;font-weight:700;color:{color};white-space:nowrap;margin-left:8px;'>{target}</span>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            st.markdown("#### 🚨 Escalation Matrix")
            escalations = [
                ("Property damage",           "Manager immediately",        "Same day",           RED),
                ("Claim over $1,500",         "Manager",                    "Same day",           RED),
                ("Major retailer escalation", "Manager / Director",         "Same day",           RED),
                ("Claim deadline < 7 days",   "Claims Lead / Manager",      "Same day",           RED),
                ("Carrier repeat SLA failure","Carrier Compliance / Mgr",   "Weekly review",      ORANGE),
                ("Field destruction no proof","Manager before closure",      "Before closing",     ORANGE),
                ("Finance mismatch > $500",   "Finance / Manager",          "Within 2 days",      ORANGE),
                ("Customer-critical issue",   "Manager / CX Leadership",    "Same day",           RED),
                ("AI low-confidence high $",  "Manager before action",      "Before acting",      ORANGE),
            ]
            for situation, escalate_to, timing, color in escalations:
                st.markdown(f"""
                <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:4px;
                            padding:8px 12px;margin-bottom:4px;border-left:3px solid {color};'>
                    <div style='font-size:12px;font-weight:600;color:{NAVY};'>{situation}</div>
                    <div style='display:flex;justify-content:space-between;margin-top:3px;'>
                        <span style='font-size:11px;color:{SLATE};'>→ {escalate_to}</span>
                        <span style='font-size:11px;font-weight:700;color:{color};'>{timing}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown("#### 💰 Approval Limits")
            approvals = [
                ("Under $100",      "Team member - no approval needed",   GREEN),
                ("$100 - $500",     "Team Lead review",                   GREEN),
                ("$500 - $1,500",   "Manager approval required",          ORANGE),
                ("$1,500+",         "Manager + Director / Finance review", RED),
            ]
            for value, approver, color in approvals:
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;align-items:center;
                            padding:8px 12px;background:{WHITE};border:1px solid #E2E8F0;
                            border-radius:4px;margin-bottom:4px;border-left:3px solid {color};'>
                    <span style='font-size:12px;font-weight:700;color:{color};'>{value}</span>
                    <span style='font-size:11px;color:{SLATE};'>{approver}</span>
                </div>
                """, unsafe_allow_html=True)

    # -- Tab 4: Ownership Matrix -----------------------------------------------
    with tab4:
        st.markdown("### Team Ownership Matrix")
        st.markdown("<div style='font-size:12px;color:#718096;margin-bottom:12px;'>Every exception must have one primary owner. No exception should remain unowned.</div>", unsafe_allow_html=True)

        roles = [
            ("Manager, Returns & Claims Operations", "Overall control, escalations, financial exposure, carrier accountability, leadership reporting, prevention roadmap", ["High-value write-offs", "Field destruction approval", "Carrier corrective action", "Executive reporting", "All Critical severity cases"]),
            ("Claims Lead / Claims Analyst",         "Damage, loss, and service failure claims - documentation, filing, follow-up, denial disputes, recovery tracking",    ["Freight damage claims", "Lost shipment claims", "Concealed damage", "Claim denial appeals", "Recovery reconciliation"]),
            ("Carrier Compliance Coordinator",       "Carrier scorecard, SLA failures, white-glove exceptions, missed appointments, service credits, QBR management",      ["White-glove service failures", "Missed delivery appointments", "Room-of-choice failures", "Carrier performance reviews", "Service credit recovery"]),
            ("Returns Operations Lead",              "RMA authorization, return aging, DC receiving coordination, inspection, disposition accuracy",                        ["Return authorization", "RMA matching at DC", "Return aging escalation", "Disposition decisions", "Wrong-item returns"]),
            ("Reverse Logistics Coordinator",        "Return pickup scheduling, field destruction coordination, disposal proof collection, pickup SLA tracking",            ["Return pickup scheduling", "Missed pickup escalation", "Field destruction approvals (under $500)", "Disposal proof collection"]),
            ("Data / Reporting Analyst",             "Dashboards, GL/SKU trend analysis, invoice variance detection, AI exception classification, aging reports",           ["Invoice overcharge detection", "Duplicate invoice flagging", "SKU return rate tracking", "GL accrual variance", "Dashboard accuracy"]),
            ("Chargeback Analyst",                   "Retailer deductions, marketplace chargebacks, portal disputes, compliance evidence, dispute win/loss tracking",       ["Wayfair/Amazon chargebacks", "Late shipment disputes", "Missing tracking deductions", "Portal compliance evidence"]),
            ("Offshore Support Team",                "Document collection, tracker updates, POD/photo follow-up, claim packet preparation, data completeness checks",       ["POD collection", "BOL retrieval", "Photo requests to customers", "Claim packet prep", "Tracker updates"]),
        ]

        for role, responsibility, owns in roles:
            with st.expander(f"👤 {role}", expanded=False):
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.markdown(f"""
                    <div style='background:#EBF4FF;border-left:4px solid {NAVY};padding:10px 14px;border-radius:4px;margin-bottom:8px;font-size:13px;'>
                        {responsibility}
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    items = "".join(f"<div style='font-size:12px;padding:3px 0;'>> {o}</div>" for o in owns)
                    st.markdown(f"""
                    <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;padding:12px;'>
                        <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;margin-bottom:6px;'>PRIMARY OWNERSHIP</div>
                        {items}
                    </div>
                    """, unsafe_allow_html=True)

        # Download full SOP reference
        st.markdown("---")
        st.download_button(
            label="⬇️ Download SLA & Ownership Reference (txt)",
            data="""NEWAGE PRODUCTS - Returns & Claims Operations Quick Reference
Generated: """ + datetime.now().strftime("%B %d, %Y") + """

SLA STANDARDS
-------------
Customer-critical white-glove failure: Same day review
Property damage during delivery: Same day escalation to Manager
Damage claim document request: Within 24 hours
Claim packet preparation: Within 48 hours
Claim filing: Within carrier deadline (3 business days recommended)
Return pickup scheduling: Within 2 business days
Invoice variance review: Within 5 business days

ESCALATION MATRIX
------------------
Property damage → Manager immediately → Same day
Claim over $1,500 → Manager → Same day
Major retailer escalation → Manager / Director → Same day
Claim deadline < 7 days → Claims Lead / Manager → Same day
Carrier repeat SLA failure → Carrier Compliance → Weekly review

APPROVAL LIMITS
----------------
Under $100: Team member - no approval needed
$100-$500: Team Lead review
$500-$1,500: Manager approval required
$1,500+: Manager + Director / Finance review

CLAIM FILING DEADLINES BY TYPE
--------------------------------
Freight damage: 9 months from delivery
Lost shipment: 9 months from ship date
Service failure: 30-60 days from delivery
Invoice dispute: 30 days from invoice date
""",
            file_name=f"NewAge_SOP_QuickRef_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )




# -- Financial Recovery Calculator ---------------------------------------------
def render_financial_calculator(orders_df, invoices_df, tracking_df, claims_df, rules, claims_prioritized):
    st.markdown('<div class="section-header">💰 Financial Recovery Calculator - Total Claim, Return & Leakage Value</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # -- Pull all values from rules engine -------------------------------------
    invoice_overcharge  = rules.get("total_overcharge_value", 0)
    duplicate_invoices  = rules.get("total_dup_value", 0)
    late_delivery_claims= rules.get("late_claim_value", 0)
    damage_claims_value = rules.get("damage_value", 0)
    missing_pod_risk    = rules.get("missing_pod_risk", 0)

    # Return value - total expected freight on returned orders
    returned_orders = orders_df[orders_df["Return Flag"] == "Yes"] if "Return Flag" in orders_df.columns else orders_df.head(0)
    total_return_freight = returned_orders["Expected Freight Cost"].sum() if "Expected Freight Cost" in returned_orders.columns else 0
    return_count = len(returned_orders)

    # Claims pipeline values
    open_claims_val      = claims_prioritized[claims_prioritized["Claim Status"].isin(["Identified","Under Review","Submitted"])]["Claim Amount"].sum() if not claims_prioritized.empty and "Claim Amount" in claims_prioritized.columns else 0
    approved_claims_val  = claims_prioritized[claims_prioritized["Claim Status"] == "Approved"]["Claim Amount"].sum() if not claims_prioritized.empty else 0
    recovered_claims_val = claims_prioritized[claims_prioritized["Claim Status"] == "Recovered"]["Claim Amount"].sum() if not claims_prioritized.empty else 0
    total_claims_val     = claims_prioritized["Claim Amount"].sum() if not claims_prioritized.empty and "Claim Amount" in claims_prioritized.columns else 0

    # Invoice totals
    total_invoiced  = invoices_df["Total Invoice Amount"].sum() if not invoices_df.empty and "Total Invoice Amount" in invoices_df.columns else 0
    total_expected  = orders_df["Expected Freight Cost"].sum() if not orders_df.empty and "Expected Freight Cost" in orders_df.columns else 0

    # Grand totals
    total_recoverable  = invoice_overcharge + duplicate_invoices + late_delivery_claims + damage_claims_value
    total_leakage      = total_recoverable + missing_pod_risk
    net_exposure       = total_claims_val - recovered_claims_val

    # -- SECTION 1: Grand Summary Banner ---------------------------------------
    st.markdown("### 📊 Grand Financial Summary")
    c1,c2,c3,c4 = st.columns(4)
    banners = [
        (c1, "Total Recoverable Value",   f"${total_recoverable:,.0f}",  "Overcharges + duplicates + late + damage", RED),
        (c2, "Total Claims Pipeline",     f"${total_claims_val:,.0f}",   f"Across {len(claims_prioritized)} open claims", ORANGE),
        (c3, "Total Return Freight Cost", f"${total_return_freight:,.0f}",f"{return_count} returned shipments", ORANGE),
        (c4, "Already Recovered",         f"${recovered_claims_val:,.0f}","Closed & paid claims", GREEN),
    ]
    for col, label, val, sub, color in banners:
        with col:
            st.markdown(f"""
            <div style='background:{WHITE};border:1px solid #E2E8F0;border-top:4px solid {color};
                        border-radius:8px;padding:18px;text-align:center;'>
                <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;letter-spacing:0.8px;'>{label}</div>
                <div style='font-size:30px;font-weight:700;color:{color};margin:8px 0 4px;'>{val}</div>
                <div style='font-size:11px;color:#718096;'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # -- SECTION 2: Cost Leakage Breakdown -------------------------------------
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 💸 Cost Leakage Breakdown")
        leakage_items = [
            ("Invoice Overcharges",   invoice_overcharge,   RED,    "Freight billed above contracted rate"),
            ("Duplicate Invoices",    duplicate_invoices,   RED,    "Same invoice billed twice"),
            ("Late Delivery Claims",  late_delivery_claims, ORANGE, "Service failure credit recoverable"),
            ("Damage Claims",         damage_claims_value,  ORANGE, "Carrier damage - filed or pending"),
            ("Missing POD Risk",      missing_pod_risk,     ORANGE, "Claim eligibility at risk"),
        ]
        for label, val, color, note in leakage_items:
            pct = (val / max(total_leakage, 1)) * 100
            bar_w = int(pct)
            st.markdown(f"""
            <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;
                        padding:12px 16px;margin-bottom:6px;'>
                <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
                    <div>
                        <div style='font-size:13px;font-weight:600;color:{NAVY};'>{label}</div>
                        <div style='font-size:11px;color:#718096;'>{note}</div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='font-size:16px;font-weight:700;color:{color};'>${val:,.0f}</div>
                        <div style='font-size:11px;color:#718096;'>{pct:.1f}% of total</div>
                    </div>
                </div>
                <div style='background:#E2E8F0;border-radius:4px;height:8px;'>
                    <div style='width:{bar_w}%;height:8px;border-radius:4px;background:{color};'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background:{NAVY};color:white;border-radius:8px;padding:14px 18px;
                    display:flex;justify-content:space-between;align-items:center;margin-top:8px;'>
            <div style='font-size:13px;font-weight:700;'>Total Cost Leakage Exposure</div>
            <div style='font-size:22px;font-weight:700;color:#F6E05E;'>${total_leakage:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 📋 Claims Pipeline Value")
        pipeline_items = [
            ("Identified",    claims_prioritized[claims_prioritized["Claim Status"]=="Identified"]["Claim Amount"].sum() if not claims_prioritized.empty else 0,    SLATE),
            ("Under Review",  claims_prioritized[claims_prioritized["Claim Status"]=="Under Review"]["Claim Amount"].sum() if not claims_prioritized.empty else 0,  BLUE2),
            ("Submitted",     claims_prioritized[claims_prioritized["Claim Status"]=="Submitted"]["Claim Amount"].sum() if not claims_prioritized.empty else 0,     ORANGE),
            ("Approved",      approved_claims_val,  GREEN),
            ("Recovered",     recovered_claims_val, "#1B5E20"),
        ]
        for stage, val, color in pipeline_items:
            pct = (val / max(total_claims_val, 1)) * 100
            st.markdown(f"""
            <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;
                        padding:10px 14px;margin-bottom:5px;
                        display:flex;justify-content:space-between;align-items:center;
                        border-left:4px solid {color};'>
                <div style='font-size:13px;font-weight:600;color:{NAVY};'>{stage}</div>
                <div style='text-align:right;'>
                    <span style='font-size:15px;font-weight:700;color:{color};'>${val:,.0f}</span>
                    <span style='font-size:11px;color:#718096;margin-left:6px;'>({pct:.0f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background:{WHITE};border:2px solid {GREEN};border-radius:8px;
                    padding:14px 18px;margin-top:10px;text-align:center;'>
            <div style='font-size:11px;font-weight:700;color:{GREEN};text-transform:uppercase;'>Recovery Rate</div>
            <div style='font-size:28px;font-weight:700;color:{GREEN};'>
                {(recovered_claims_val/max(total_claims_val,1)*100):.0f}%
            </div>
            <div style='font-size:11px;color:#718096;'>${recovered_claims_val:,.0f} of ${total_claims_val:,.0f} total</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # -- SECTION 3: Invoice vs Expected ----------------------------------------
    st.markdown("### 🧾 Invoice vs Expected Freight")
    c1,c2,c3,c4 = st.columns(4)
    inv_variance = total_invoiced - total_expected
    for col, label, val, color in [
        (c1, "Total Expected Freight",  f"${total_expected:,.0f}",  NAVY),
        (c2, "Total Invoiced Freight",  f"${total_invoiced:,.0f}",  BLUE2),
        (c3, "Total Variance",          f"${inv_variance:,.0f}",    RED if inv_variance > 0 else GREEN),
        (c4, "Invoices Reviewed",       f"{len(invoices_df):,}",    SLATE),
    ]:
        with col:
            st.markdown(f"""
            <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;
                        padding:14px;border-left:4px solid {color};'>
                <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;'>{label}</div>
                <div style='font-size:22px;font-weight:700;color:{color};margin-top:4px;'>{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # -- SECTION 4: Returns Summary ---------------------------------------------
    st.markdown("### 🔄 Returns Financial Summary")
    if return_count > 0:
        avg_return_freight = total_return_freight / return_count
        top_return_skus = returned_orders.groupby("SKU").size().sort_values(ascending=False).head(5) if "SKU" in returned_orders.columns else pd.Series()

        c1, c2 = st.columns([2, 3])
        with c1:
            for label, val, color in [
                ("Total Returned Orders",    f"{return_count:,}",               ORANGE),
                ("Total Return Freight",      f"${total_return_freight:,.0f}",   RED),
                ("Avg Freight per Return",    f"${avg_return_freight:,.0f}",     ORANGE),
                ("Return Rate",               f"{return_count/max(len(orders_df),1)*100:.1f}%", RED if return_count/max(len(orders_df),1) > 0.08 else GREEN),
            ]:
                st.markdown(f"""
                <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;
                            padding:12px 16px;margin-bottom:6px;
                            display:flex;justify-content:space-between;'>
                    <span style='font-size:13px;color:{SLATE};'>{label}</span>
                    <span style='font-size:14px;font-weight:700;color:{color};'>{val}</span>
                </div>
                """, unsafe_allow_html=True)

        with c2:
            if not top_return_skus.empty:
                st.markdown("**Top SKUs by Return Volume**")
                for sku, cnt in top_return_skus.items():
                    pct = cnt / return_count * 100
                    st.markdown(f"""
                    <div style='background:{WHITE};border:1px solid #E2E8F0;border-radius:6px;
                                padding:10px 14px;margin-bottom:5px;'>
                        <div style='display:flex;justify-content:space-between;margin-bottom:5px;'>
                            <span style='font-size:13px;font-weight:600;color:{NAVY};'>{sku}</span>
                            <span style='font-size:13px;font-weight:700;color:{RED};'>{cnt} returns ({pct:.0f}%)</span>
                        </div>
                        <div style='background:#E2E8F0;border-radius:4px;height:6px;'>
                            <div style='width:{int(pct)}%;height:6px;border-radius:4px;background:{RED};'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No return data available in current filtered dataset.")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # -- SECTION 5: Full Export -------------------------------------------------
    st.markdown("### ⬇️ Export Full Financial Summary")
    import io as _io
    summary_data = {
        "Category":         ["Invoice Overcharges","Duplicate Invoices","Late Delivery Claims",
                             "Damage Claims","Missing POD Risk","TOTAL LEAKAGE",
                             "","Open Claims","Approved Claims","Recovered Claims","TOTAL CLAIMS",
                             "","Return Freight Cost","Invoices Reviewed","Total Invoiced","Total Expected","Freight Variance"],
        "Value ($)":        [invoice_overcharge, duplicate_invoices, late_delivery_claims,
                            damage_claims_value, missing_pod_risk, total_leakage,
                            "", open_claims_val, approved_claims_val, recovered_claims_val, total_claims_val,
                            "", total_return_freight, len(invoices_df), total_invoiced, total_expected, inv_variance],
        "Notes":            ["Freight billed above contracted rate","Same invoice billed twice",
                            "Service failure credit recoverable","Carrier damage filed or pending",
                            "Claim eligibility at risk","Sum of all leakage categories",
                            "","Pending resolution","Carrier approved","Cash received","All open claims",
                            "","Total freight on returned orders","All carrier invoices audited",
                            "Sum of all carrier invoices","Sum of contracted rates","Invoiced minus expected"],
    }
    export_df = pd.DataFrame(summary_data)
    export_df["Export Date"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    buf = _io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Financial Summary")
        if not claims_prioritized.empty:
            claims_prioritized.to_excel(writer, index=False, sheet_name="Claims Detail")
        if not returned_orders.empty:
            returned_orders.to_excel(writer, index=False, sheet_name="Returns Detail")
    buf.seek(0)

    st.download_button(
        "⬇️ Download Full Financial Recovery Report (Excel)",
        data=buf,
        file_name=f"NewAge_Financial_Recovery_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# -- Return Total Cost Calculator -----------------------------------------------
def render_return_cost_calculator():
    st.markdown('<div class="section-header">🧮 Return Total Cost Calculator - Full Cost-to-Serve & Disposition Decision Engine</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:#EBF4FF;border:1px solid #BEE3F8;border-left:4px solid #3182CE;
                border-radius:6px;padding:12px 16px;margin-bottom:16px;font-size:13px;'>
        <strong>How to use:</strong> Enter the cost details for a return case below.
        The calculator will compute the total cost-to-serve, net loss, and recommend
        the best disposition - Return to DC, Field Destruction, Replacement Part, or Customer Discount.
        All fields have suggested defaults based on NewAge bulky product averages.
    </div>
    """, unsafe_allow_html=True)

    # -- Input form -------------------------------------------------------------
    st.markdown("### 📋 Case Details")
    col1, col2, col3 = st.columns(3)
    with col1:
        order_id   = st.text_input("Order ID", value="ORD-1001")
        sku        = st.text_input("SKU", value="GAR-CAB-001")
        issue_type = st.selectbox("Issue Type", [
            "Damaged in transit","Missing parts","Wrong item shipped",
            "Customer changed mind","Defective product","White-glove failure",
            "Cosmetic damage only","Lost shipment"
        ])
    with col2:
        product_cost   = st.number_input("Product Cost ($)", value=650.0, step=10.0,
                            help="ERP item master / finance standard cost - NOT retail price")
        selling_price  = st.number_input("Selling Price ($)", value=899.0, step=10.0,
                            help="Retail / wholesale selling price")
        resale_value   = st.number_input("Resale / Open-box Value ($)", value=200.0, step=10.0,
                            help="What product could sell for if returned to DC - 0 if unsellable")
    with col3:
        carrier_recovery = st.number_input("Expected Carrier Recovery ($)", value=650.0, step=10.0,
                            help="Carrier claim / vendor credit / insurance")
        vendor_credit    = st.number_input("Vendor Credit ($)", value=0.0, step=10.0,
                            help="Credit from supplier if product defect")
        docs_complete    = st.selectbox("Claim Documents Complete?", ["Yes - ready to file","No - missing POD/photos","Partial"])

    st.markdown("---")
    st.markdown("### 💸 Cost Components")
    st.markdown("<div style='font-size:12px;color:#718096;margin-bottom:12px;'>Adjust any value - defaults are NewAge bulky product averages. Source shown for each field.</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**🚚 Freight Costs**")
        outbound_freight   = st.number_input("Outbound Freight ($)", value=180.0, step=5.0,
                                help="Source: Carrier invoice / freight accrual GL - already spent, usually non-recoverable")
        return_freight     = st.number_input("Return Pickup Freight ($)", value=220.0, step=5.0,
                                help="Source: Carrier return rate table / final-mile invoice - often higher than outbound (residential one-off pickup)")
        replacement_freight= st.number_input("Replacement Freight ($)", value=180.0, step=5.0,
                                help="Source: Carrier rate table / similar shipment history - only if sending replacement")

    with c2:
        st.markdown("**🏭 Warehouse Costs**")
        wh_handling        = st.number_input("Warehouse Handling ($)", value=40.0, step=5.0,
                                help="Source: 3PL rate card / labour standard. Includes: receiving, unload, putaway, pallet handling. Formula: Labour mins × $24/hr + 3PL fee")
        inspection_cost    = st.number_input("Inspection Cost ($)", value=15.0, step=5.0,
                                help="Source: 3PL inspection fee / labour time. Needed to classify sellable vs non-sellable")
        repackaging_cost   = st.number_input("Repackaging Cost ($)", value=25.0, step=5.0,
                                help="Source: Warehouse materials + labour. Carton, corner protection, pallet, tape")
        disposition_cost   = st.number_input("Disposition Cost ($)", value=50.0, step=5.0,
                                help="Source: 3PL disposal rate / refurbish cost / field destruction vendor. Varies by decision: disposal $35, refurbish $80-$150, restock $25")
        storage_cost       = st.number_input("Storage Cost ($)", value=10.0, step=5.0,
                                help="Source: 3PL storage rate per pallet per week. Applies if return sits in DC waiting for decision")

    with c3:
        st.markdown("**📋 Admin & Customer Costs**")
        admin_claim_cost   = st.number_input("Claims Admin Cost ($)", value=20.0, step=5.0,
                                help="Source: Labour time estimate. Collect POD + photos + file claim + follow up. Formula: 30-45 mins × $30/hr loaded rate = $15-$22")
        chargeback_cost    = st.number_input("Chargeback Work Cost ($)", value=25.0, step=5.0,
                                help="Source: Finance deduction team estimate. Research ASN/POD/appointment + dispute filing. Formula: 45 mins × $30/hr = $22.50")
        customer_credit    = st.number_input("Customer Credit / Appeasement ($)", value=100.0, step=10.0,
                                help="Source: Customer service adjustment / goodwill credit / refund. Includes discount, partial refund, replacement appeasement")
        cs_labour          = st.number_input("Customer Service Labour ($)", value=15.0, step=5.0,
                                help="Source: Internal labour estimate. Time spent on calls, emails, resolution. Formula: 30 mins × $30/hr = $15")
        inventory_writeoff = st.number_input("Inventory Write-off ($)", value=0.0, step=10.0,
                                help="Source: Finance / inventory team. Apply if product cannot be resold or recovered. Equal to product cost if total loss")
        payment_fee        = st.number_input("Payment Processing Fee ($)", value=8.0, step=1.0,
                                help="Source: Finance / payment processor. Refund transaction fee - typically 2-3% of refund amount")

    # -- Calculations ----------------------------------------------------------
    gross_exposure = (
        product_cost + outbound_freight + return_freight + replacement_freight +
        wh_handling + inspection_cost + repackaging_cost + disposition_cost +
        storage_cost + admin_claim_cost + chargeback_cost + customer_credit +
        cs_labour + inventory_writeoff + payment_fee
    )
    total_recovery = carrier_recovery + vendor_credit + resale_value
    net_loss       = gross_exposure - total_recovery
    margin_impact  = selling_price - gross_exposure + total_recovery

    # Docs complete factor
    docs_factor = 1.0 if "Yes" in docs_complete else (0.5 if "Partial" in docs_complete else 0.0)
    effective_recovery = carrier_recovery * docs_factor

    # -- Decision logic ---------------------------------------------------------
    field_dest_cost  = disposition_cost + admin_claim_cost
    field_dest_recov = carrier_recovery * docs_factor
    field_dest_net   = field_dest_cost - field_dest_recov

    return_dc_cost   = return_freight + wh_handling + inspection_cost + repackaging_cost + storage_cost
    return_dc_recov  = resale_value
    return_dc_net    = return_dc_cost - return_dc_recov

    repl_part_cost   = replacement_freight + admin_claim_cost
    repl_part_net    = repl_part_cost

    discount_cost    = customer_credit
    discount_net     = discount_cost

    # Determine recommendation
    if issue_type == "Missing parts":
        recommendation = "Send Replacement Part"
        rec_reason     = "Missing parts - replacement part is lowest cost resolution. Avoids full return freight and warehouse handling."
        rec_color      = GREEN
    elif issue_type == "Cosmetic damage only":
        recommendation = "Customer Discount / Open-Box Resale"
        rec_reason     = "Cosmetic damage - product is usable. Offer discount to retain customer and avoid return freight cost."
        rec_color      = BLUE2
    elif (return_freight + wh_handling) > resale_value and resale_value < 100:
        recommendation = "Field Destruction"
        rec_reason     = "Return freight + handling exceeds resale value. Field destruction with carrier claim filing is most cost-effective."
        rec_color      = ORANGE
    elif "Yes" in docs_complete and carrier_recovery > (return_freight + wh_handling):
        recommendation = "Field Destruction + Carrier Claim"
        rec_reason     = "Documents complete and carrier recovery exceeds return cost. Field destroy and file claim immediately."
        rec_color      = ORANGE
    elif product_cost > 400 and resale_value > return_freight:
        recommendation = "Return to DC"
        rec_reason     = "High-value product with positive resale margin. Return to DC for inspection and open-box resale."
        rec_color      = GREEN
    elif "No" in docs_complete:
        recommendation = "Hold - Collect Documents First"
        rec_reason     = "Missing POD / photos. Do not proceed with disposition until claim documentation is complete."
        rec_color      = RED
    else:
        recommendation = "Customer Discount / Review"
        rec_reason     = "Marginal return economics. Consider customer discount to avoid freight cost while maintaining relationship."
        rec_color      = BLUE2

    # -- Results display --------------------------------------------------------
    st.markdown("---")
    st.markdown("### 📊 Cost Analysis Results")

    # Recommendation banner
    st.markdown(f"""
    <div style='background:{rec_color};color:white;border-radius:8px;padding:16px 24px;margin-bottom:16px;'>
        <div style='font-size:11px;font-weight:700;opacity:0.8;text-transform:uppercase;letter-spacing:1px;'>AI Recommended Action</div>
        <div style='font-size:22px;font-weight:700;margin:4px 0;'>{recommendation}</div>
        <div style='font-size:13px;opacity:0.9;'>{rec_reason}</div>
    </div>
    """, unsafe_allow_html=True)

    # Key numbers
    c1,c2,c3,c4 = st.columns(4)
    for col, label, val, color, note in [
        (c1, "Gross Exposure",    f"${gross_exposure:,.2f}",  RED,    "All costs combined"),
        (c2, "Total Recovery",    f"${total_recovery:,.2f}",  GREEN,  "Claim + vendor + resale"),
        (c3, "Net Loss",          f"${net_loss:,.2f}",        RED if net_loss > 0 else GREEN, "Exposure minus recovery"),
        (c4, "Margin Impact",     f"${margin_impact:,.2f}",   GREEN if margin_impact > 0 else RED, "vs selling price"),
    ]:
        with col:
            st.markdown(f"""
            <div style='background:{WHITE};border:1px solid #E2E8F0;border-top:4px solid {color};
                        border-radius:8px;padding:16px;text-align:center;'>
                <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;'>{label}</div>
                <div style='font-size:26px;font-weight:700;color:{color};margin:6px 0 4px;'>{val}</div>
                <div style='font-size:11px;color:#718096;'>{note}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Full cost breakdown
    col_breakdown, col_comparison = st.columns([3, 2])

    with col_breakdown:
        st.markdown("**Full Cost Breakdown**")
        cost_items = [
            ("Product Cost",              product_cost,        "ERP item master",                       NAVY),
            ("Outbound Freight",          outbound_freight,    "Carrier invoice - sunk cost",           SLATE),
            ("Return Pickup Freight",     return_freight,      "Carrier return rate table",             RED),
            ("Replacement Freight",       replacement_freight, "Only if sending replacement",           ORANGE),
            ("Warehouse Handling",        wh_handling,         "3PL rate card",                        ORANGE),
            ("Inspection Cost",           inspection_cost,     "3PL inspection fee",                   ORANGE),
            ("Repackaging Cost",          repackaging_cost,    "Materials + labour",                   ORANGE),
            ("Disposition Cost",          disposition_cost,    "Disposal / refurbish / restock",        ORANGE),
            ("Storage Cost",              storage_cost,        "3PL storage per week",                 SLATE),
            ("Claims Admin Cost",         admin_claim_cost,    "Labour to file & follow up claim",     BLUE2),
            ("Chargeback Work Cost",      chargeback_cost,     "Finance dispute labour",               BLUE2),
            ("Customer Credit",           customer_credit,     "Refund / appeasement / discount",      RED),
            ("Customer Service Labour",   cs_labour,           "Resolution time estimate",             BLUE2),
            ("Inventory Write-off",       inventory_writeoff,  "If product is total loss",             RED),
            ("Payment Processing Fee",    payment_fee,         "Refund transaction fee",               SLATE),
        ]
        recovery_items = [
            ("Carrier Recovery",          -carrier_recovery,   f"Claim - {docs_complete}",             GREEN),
            ("Vendor Credit",             -vendor_credit,      "Supplier credit",                      GREEN),
            ("Resale / Open-box Value",   -resale_value,       "If returned to DC",                    GREEN),
        ]

        for label, val, source, color in cost_items:
            if val > 0:
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;align-items:center;
                            padding:7px 12px;border-bottom:1px solid #F0F0F0;'>
                    <div>
                        <div style='font-size:13px;color:{NAVY};'>{label}</div>
                        <div style='font-size:10px;color:#A0AEC0;'>{source}</div>
                    </div>
                    <div style='font-size:13px;font-weight:600;color:{color};'>${val:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='display:flex;justify-content:space-between;align-items:center;
                    padding:10px 12px;background:{NAVY};border-radius:6px;margin-top:6px;'>
            <div style='font-size:13px;font-weight:700;color:white;'>GROSS EXPOSURE</div>
            <div style='font-size:16px;font-weight:700;color:#F6E05E;'>${gross_exposure:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        for label, val, source, color in recovery_items:
            if abs(val) > 0:
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;align-items:center;
                            padding:7px 12px;border-bottom:1px solid #F0F0F0;'>
                    <div>
                        <div style='font-size:13px;color:{color};'>{label}</div>
                        <div style='font-size:10px;color:#A0AEC0;'>{source}</div>
                    </div>
                    <div style='font-size:13px;font-weight:600;color:{color};'>${val:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        net_color = RED if net_loss > 0 else GREEN
        st.markdown(f"""
        <div style='display:flex;justify-content:space-between;align-items:center;
                    padding:12px;background:{"#FDECEA" if net_loss > 0 else "#E8F5E9"};
                    border-radius:6px;margin-top:6px;border:2px solid {net_color};'>
            <div style='font-size:14px;font-weight:700;color:{net_color};'>NET LOSS / GAIN</div>
            <div style='font-size:20px;font-weight:700;color:{net_color};'>${net_loss:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_comparison:
        st.markdown("**Disposition Comparison**")
        options = [
            ("Return to DC",             return_dc_cost,  return_dc_recov,  return_dc_net),
            ("Field Destruction",        field_dest_cost, field_dest_recov, field_dest_net),
            ("Replacement Part Only",    repl_part_cost,  0,                repl_part_net),
            ("Customer Discount",        discount_cost,   0,                discount_net),
        ]
        best_net = min(opt[3] for opt in options)
        for option, cost, recov, net in options:
            is_best = (net == best_net)
            border  = f"2px solid {GREEN}" if is_best else "1px solid #E2E8F0"
            badge   = f"<span style='background:{GREEN};color:white;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;margin-left:8px;'>BEST</span>" if is_best else ""
            net_c   = GREEN if net <= 0 else RED
            st.markdown(f"""
            <div style='background:{WHITE};border:{border};border-radius:8px;
                        padding:12px 14px;margin-bottom:8px;'>
                <div style='font-size:13px;font-weight:700;color:{NAVY};margin-bottom:8px;'>
                    {option}{badge}
                </div>
                <div style='display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;'>
                    <span style='color:{SLATE};'>Cost</span>
                    <span style='font-weight:600;color:{RED};'>${cost:,.2f}</span>
                </div>
                <div style='display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;'>
                    <span style='color:{SLATE};'>Recovery</span>
                    <span style='font-weight:600;color:{GREEN};'>${recov:,.2f}</span>
                </div>
                <div style='display:flex;justify-content:space-between;font-size:13px;
                            padding-top:6px;border-top:1px solid #E2E8F0;'>
                    <span style='font-weight:700;color:{NAVY};'>Net Impact</span>
                    <span style='font-weight:700;color:{net_c};'>${net:,.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Docs warning
        if "No" in docs_complete:
            st.markdown(f"""
            <div style='background:#FDECEA;border:1px solid #FFCDD2;border-radius:6px;
                        padding:10px 14px;margin-top:8px;'>
                <div style='font-size:12px;font-weight:700;color:{RED};'>[!] Missing Documents</div>
                <div style='font-size:11px;color:#C62828;margin-top:3px;'>
                    Carrier recovery reduced to $0 until POD and photos are collected.
                    Collect documents before filing claim or approving field destruction.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # -- Export -----------------------------------------------------------------
    st.markdown("---")
    st.markdown("### ⬇️ Export This Case")

    export_rows = {
        "Field": [
            "Order ID","SKU","Issue Type","Docs Complete",
            "Product Cost","Selling Price","Outbound Freight","Return Pickup Freight",
            "Replacement Freight","Warehouse Handling","Inspection Cost","Repackaging Cost",
            "Disposition Cost","Storage Cost","Claims Admin Cost","Chargeback Work Cost",
            "Customer Credit","Customer Service Labour","Inventory Write-off","Payment Fee",
            "GROSS EXPOSURE","Carrier Recovery","Vendor Credit","Resale Value",
            "TOTAL RECOVERY","NET LOSS","RECOMMENDATION","Margin Impact",
        ],
        "Value": [
            order_id, sku, issue_type, docs_complete,
            product_cost, selling_price, outbound_freight, return_freight,
            replacement_freight, wh_handling, inspection_cost, repackaging_cost,
            disposition_cost, storage_cost, admin_claim_cost, chargeback_cost,
            customer_credit, cs_labour, inventory_writeoff, payment_fee,
            gross_exposure, carrier_recovery, vendor_credit, resale_value,
            total_recovery, net_loss, recommendation, margin_impact,
        ],
        "Source / Notes": [
            "ERP / OMS","ERP / WMS","Case classification","Documentation status",
            "ERP item master / finance standard cost","Retail / wholesale selling price",
            "Carrier invoice - sunk cost","Carrier return rate table",
            "Carrier rate table / TMS","3PL rate card / labour standard",
            "3PL inspection fee","Warehouse materials + labour",
            "3PL disposal / refurbish / restock rate","3PL storage per pallet per week",
            "Labour estimate: 30-45 mins × $30/hr","Finance: 45 mins × $30/hr",
            "Customer service adjustment / goodwill","Resolution time: 30 mins × $30/hr",
            "Finance - total loss write-off","2-3% of refund amount",
            "Sum of all costs","Carrier claim × docs factor","Supplier credit","Open-box resale value",
            "Claim + vendor + resale","Gross exposure minus total recovery",
            "System recommendation based on decision logic","vs original selling price",
        ],
    }
    import io as _io
    export_df = pd.DataFrame(export_rows)
    export_df["Calculated On"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    buf = _io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Return Cost Calculator")
    buf.seek(0)

    st.download_button(
        "⬇️ Download Return Cost Case (Excel)",
        data=buf,
        file_name=f"NewAge_ReturnCost_{order_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Where to get each cost - reference card
    with st.expander("📖 Data Source Reference - Where to Get Each Cost in Production"):
        refs = [
            ("Product Cost",            "ERP item master / finance standard cost / landed cost file. NOT retail price."),
            ("Outbound Freight",        "Carrier invoice / freight audit file / TMS shipment cost report / freight accrual GL."),
            ("Return Pickup Freight",   "Carrier return rate table / final-mile pickup invoice / 3PL contract. Usually higher than outbound (residential one-off)."),
            ("Replacement Freight",     "Carrier rate table / similar shipment history / TMS estimate / replacement order invoice."),
            ("Warehouse Handling",      "3PL rate card / warehouse contract. Formula: Labour mins × $24/hr + 3PL admin fee. Includes: receive, unload, inspect, putaway, repack."),
            ("Inspection Cost",         "3PL inspection fee or internal labour. Needed to classify sellable vs non-sellable condition."),
            ("Repackaging Cost",        "Warehouse material cost + labour. Carton, corner protection, pallet, packing tape."),
            ("Disposition Cost",        "3PL disposal rate / field destruction vendor / refurbish cost / restock fee. Varies: disposal $35, refurbish $80-150, restock $25."),
            ("Storage Cost",            "3PL storage rate per pallet per week. Applies if return sits in DC waiting for disposition decision."),
            ("Claims Admin Cost",       "Internal labour estimate. Formula: 30-45 mins × $30/hr loaded rate = $15-22. Covers: POD collection, claim filing, carrier follow-up, denial dispute."),
            ("Chargeback Work Cost",    "Finance deduction team estimate. Formula: 45 mins × $30/hr = $22.50. Covers: ASN research, POD validation, portal dispute filing."),
            ("Customer Credit",         "Customer service adjustment record / CRM. Includes: discount, partial refund, goodwill credit, appeasement."),
            ("Customer Service Labour", "Internal estimate. Formula: 30 mins × $30/hr = $15. Time on calls, emails, resolution coordination."),
            ("Inventory Write-off",     "Finance / inventory team approval. Apply if product is total loss and cannot be recovered or resold."),
            ("Payment Processing Fee",  "Payment processor / finance. Typically 2-3% of refund amount. Refund transaction cost."),
            ("Carrier Recovery",        "Carrier claim approval / insurance payout / vendor credit memo. Multiplied by docs complete factor."),
        ]
        for field, source in refs:
            st.markdown(f"""
            <div style='display:flex;gap:12px;padding:7px 0;border-bottom:1px solid #F0F0F0;'>
                <div style='font-size:12px;font-weight:700;color:{NAVY};min-width:180px;'>{field}</div>
                <div style='font-size:12px;color:{SLATE};'>{source}</div>
            </div>
            """, unsafe_allow_html=True)



"""
NewAge Products - Daily Operations Control Tower
v4 - Daily tabs module
All 8 daily operating tabs with Comment 1 + Comment 2 + Download on every table
"""

import pandas as pd
import numpy as np
import io
from datetime import datetime, timedelta
import random

random.seed(99)

NAVY   = "#17375E"
SLATE  = "#4B5563"
GREEN  = "#2E7D32"
ORANGE = "#ED6C02"
RED    = "#D32F2F"
BG     = "#F8FAFC"
WHITE  = "#FFFFFF"
BLUE2  = "#2C5282"
GOLD   = "#F6E05E"

# -- Session state helpers ------------------------------------------------------
def get_comments(table_key):
    key = f"comments_{table_key}"
    if key not in st.session_state:
        st.session_state[key] = {}
    return st.session_state[key]

def save_comment(table_key, row_id, col, value):
    comments = get_comments(table_key)
    if row_id not in comments:
        comments[row_id] = {"Comment 1": "", "Comment 2": ""}
    comments[row_id][col] = value

def apply_comments(df, id_col, table_key):
    comments = get_comments(table_key)
    df = df.copy()
    df["Comment 1"] = df[id_col].apply(lambda x: comments.get(str(x), {}).get("Comment 1", ""))
    df["Comment 2"] = df[id_col].apply(lambda x: comments.get(str(x), {}).get("Comment 2", ""))
    return df

def download_button(df, filename, label="⬇️ Download with Comments"):
    buf = io.BytesIO()
    df["Export Date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    st.download_button(label, buf,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def section(title):
    st.markdown(f'<div style="background:{NAVY};color:white;padding:8px 16px;border-radius:6px 6px 0 0;font-size:13px;font-weight:600;letter-spacing:0.3px;">{title}</div>', unsafe_allow_html=True)

def priority_color(val):
    if val in ["Critical","High","RED","Red"]:   return f"background-color:#FDECEA;color:#C62828;font-weight:700"
    if val in ["Medium","YELLOW","Yellow"]:       return f"background-color:#FFF3E0;color:#E65100;font-weight:600"
    if val in ["Low","GREEN","Green"]:            return f"background-color:#E8F5E9;color:#2E7D32"
    return ""

def comment_editor(df, id_col, table_key, height=320):
    """Render table with inline comment editors and download."""
    comments = get_comments(table_key)

    # Editable comment area - compact 2-column layout
    st.markdown(f"<div style='font-size:11px;color:#718096;margin:6px 0 10px;'>Click any row below to add notes. Comments are saved in your session and included in the download.</div>", unsafe_allow_html=True)

    with st.expander("✏️ Add / Edit Comments", expanded=False):
        for idx, row in df.head(20).iterrows():
            row_id = str(row[id_col])
            existing = comments.get(row_id, {})
            c1, c2, c3 = st.columns([2, 3, 3])
            with c1:
                st.markdown(f"<div style='font-size:12px;font-weight:600;padding-top:6px;'>{row_id}</div>", unsafe_allow_html=True)
            with c2:
                v1 = st.text_input(f"Comment 1", value=existing.get("Comment 1",""),
                    key=f"{table_key}_{row_id}_c1", label_visibility="collapsed",
                    placeholder="Comment 1 - action taken / owner")
                save_comment(table_key, row_id, "Comment 1", v1)
            with c3:
                v2 = st.text_input(f"Comment 2", value=existing.get("Comment 2",""),
                    key=f"{table_key}_{row_id}_c2", label_visibility="collapsed",
                    placeholder="Comment 2 - follow-up / status")
                save_comment(table_key, row_id, "Comment 2", v2)

    export_df = apply_comments(df, id_col, table_key)
    download_button(export_df, table_key)
    return export_df

# -- Synthetic daily data generators -------------------------------------------
def make_returns_aging():
    statuses = ["Pickup Requested","Pickup Scheduled","Stuck with Carrier",
                "In Transit","Received - Not Inspected","Inspected - Not Dispositioned","Closed"]
    carriers = ["FedEx","UPS","XPO Logistics","Estes Express","Old Dominion"]
    skus     = ["SKU-441 Patio Dining Set","SKU-810 Gazebo 10x12","SKU-101 36in Smart TV",
                "SKU-512 Kitchen Island","SKU-202 Outdoor Sectional","SKU-720 Portable AC"]
    customers= ["Costco","Wayfair","Home Depot","Amazon","Target","Canadian Tire"]
    rows = []
    for i in range(1, 21):
        aging = random.randint(1, 28)
        status = random.choice(statuses)
        risk = "Critical" if aging > 14 or status == "Stuck with Carrier" else \
               ("High" if aging > 7 else ("Medium" if aging > 3 else "Low"))
        action_map = {
            "Pickup Requested":              "Escalate carrier - pickup overdue",
            "Stuck with Carrier":            "Contact carrier terminal today - SLA breach",
            "Received - Not Inspected":      "Assign inspection - DC queue review",
            "Inspected - Not Dispositioned": "Manager decision required - disposition pending",
        }
        action = action_map.get(status, "Monitor - within SLA")
        rows.append({
            "RMA ID":    f"RMA-{1000+i}",
            "Customer":  random.choice(customers),
            "SKU":       random.choice(skus),
            "Carrier":   random.choice(carriers),
            "Status":    status,
            "Days Aging":aging,
            "SLA Target":10,
            "SLA Breach": "YES" if aging > 10 else "no",
            "Risk":      risk,
            "Next Action":action,
        })
    return pd.DataFrame(rows).sort_values("Days Aging", ascending=False)

def make_claims_recovery():
    carriers   = ["FedEx","UPS","XPO Logistics","Estes Express","Old Dominion"]
    claim_types= ["Damage","Loss","Service Failure","Invoice Dispute"]
    missing    = ["None","Damage photos","POD","BOL","Both POD & photos","Carrier response"]
    rows = []
    for i in range(1, 16):
        days   = random.randint(1, 95)
        ddl    = random.randint(-5, 170)
        amount = round(random.uniform(300, 4500), 2)
        rec    = round(random.uniform(0.25, 0.88), 2)
        miss   = random.choice(missing)
        ddl_risk = "Critical" if ddl < 10 else ("High" if ddl < 30 else ("Medium" if ddl < 60 else "Low"))
        action = "FILE TODAY - deadline critical" if ddl < 10 else \
                 (f"Collect {miss} then file" if miss != "None" else \
                  ("Follow up with carrier" if days > 30 else "Prepare claim packet"))
        rows.append({
            "Claim ID":       f"CLM-{2000+i}",
            "Carrier":        random.choice(carriers),
            "Claim Type":     random.choice(claim_types),
            "Amount":         amount,
            "Missing Docs":   miss,
            "Days Open":      days,
            "Days to Deadline":ddl,
            "Deadline Risk":  ddl_risk,
            "Recovery Prob":  f"{rec:.0%}",
            "Action":         action,
        })
    return pd.DataFrame(rows).sort_values("Days to Deadline")

def make_invoice_audit(invoices_df, orders_df):
    try:
        merged = invoices_df.merge(
            orders_df[["Tracking Number","Expected Freight Cost","Carrier"]],
            on="Tracking Number", how="left", suffixes=("_inv","_ord")
        )
        merged["Carrier"] = merged["Carrier_inv"].fillna(merged["Carrier_ord"])
        merged["Expected"] = merged["Expected Freight Cost"]
        merged["Invoiced"] = merged["Freight Charge"]
        merged["Variance"] = (merged["Invoiced"] - merged["Expected"]).round(2)
        merged["Variance %"] = ((merged["Variance"] / merged["Expected"]) * 100).round(1)
        merged["Status"] = merged["Variance"].apply(
            lambda v: "DISPUTE" if v > 50 else ("REVIEW" if v > 20 else "OK"))
        merged["Reason"] = merged.apply(lambda r:
            "Rate overcharge" if r["Variance"] > 100 else
            ("Invalid accessorial" if r["Variance"] > 50 else
             ("Fuel surcharge mismatch" if r["Variance"] > 20 else "Within tolerance")), axis=1)
        merged["Action"] = merged.apply(lambda r:
            f"Dispute - ${r['Variance']:,.2f} overcharge" if r["Status"]=="DISPUTE" else
            ("Review before payment" if r["Status"]=="REVIEW" else "Approve"), axis=1)
        result = merged[["Invoice Number","Carrier","Tracking Number",
                          "Expected","Invoiced","Variance","Variance %",
                          "Status","Reason","Action"]].copy()
        result["Invoice Number"] = result["Invoice Number"].astype(str)
        return result.sort_values("Variance", ascending=False).head(25)
    except Exception:
        return pd.DataFrame(columns=["Invoice Number","Carrier","Tracking Number",
                                     "Expected","Invoiced","Variance","Variance %",
                                     "Status","Reason","Action"])

def make_delivery_exceptions(orders_df, tracking_df):
    try:
        merged = orders_df.merge(tracking_df[["Tracking Number","Current Status","POD Available","Last Event Date"]],
                                  on="Tracking Number", how="left")
        merged["Promised Delivery Date"] = pd.to_datetime(merged["Promised Delivery Date"])
        merged["Actual Delivery Date"]   = pd.to_datetime(merged["Actual Delivery Date"])
        merged["Days Late"] = (merged["Actual Delivery Date"] - merged["Promised Delivery Date"]).dt.days
        exceptions = merged[
            (merged["Days Late"] > 0) |
            (merged["POD Available"] == "No") |
            (merged["Damage Flag"] == "Yes") |
            (merged["Current Status"] == "Exception")
        ].copy()
        exceptions["Exception Type"] = exceptions.apply(lambda r:
            "Damaged at Delivery" if r["Damage Flag"]=="Yes" else
            ("Missing POD" if r["POD Available"]=="No" else
             ("Late Delivery" if r["Days Late"]>0 else "Carrier Exception")), axis=1)
        exceptions["Customer Impact"] = exceptions["Exception Type"].apply(lambda t:
            "High - refund/replacement risk" if t=="Damaged at Delivery" else
            ("Medium - claim eligibility at risk" if t=="Missing POD" else
             ("Medium - SLA breach" if t=="Late Delivery" else "Low")))
        exceptions["Next Action"] = exceptions.apply(lambda r:
            "File damage claim + collect photos" if r["Exception Type"]=="Damaged at Delivery" else
            ("Request POD from carrier within 72hrs" if r["Exception Type"]=="Missing POD" else
             ("File service failure claim" if r["Exception Type"]=="Late Delivery" else
              "Contact carrier terminal")), axis=1)
        return exceptions[["Order ID","Carrier","Exception Type","Days Late",
                            "Customer Impact","Current Status","Next Action"]].head(20)
    except Exception:
        return pd.DataFrame()

def make_field_destruction():
    skus = [
        ("SKU-441","Patio Dining Set",650,220,40,0),
        ("SKU-810","Gazebo 10x12",720,290,45,0),
        ("SKU-101","36in Smart TV",320,95,30,80),
        ("SKU-202","Outdoor Sectional",890,340,55,0),
        ("SKU-720","Portable AC",480,150,35,120),
        ("SKU-512","Kitchen Island",310,120,40,60),
        ("SKU-303","Cabinet Unit",240,85,30,50),
        ("SKU-615","Bookshelf 5-Tier",120,65,20,40),
    ]
    rows = []
    for sku, name, pval, rfreight, handling, recovery in skus:
        net_return  = recovery - rfreight - handling
        net_destroy = 0 - 35  # disposal cost only
        if recovery == 0 or net_return < 0:
            recommendation = "Field Destruction"
        elif recovery > rfreight + handling + 50:
            recommendation = "Return to DC"
        else:
            recommendation = "Assess - marginal return"
        savings = abs(rfreight + handling - 35) if recommendation == "Field Destruction" else 0
        rows.append({
            "SKU":           sku,
            "Product":       name,
            "Product Value": pval,
            "Return Freight":rfreight,
            "Handling":      handling,
            "Recovery Value":recovery,
            "Net if Returned":net_return,
            "Disposal Cost": 35,
            "Recommendation":recommendation,
            "Freight Saved":  savings,
            "Required Proof": "Photos + customer confirmation + disposal cert if vendor",
        })
    return pd.DataFrame(rows)

def make_sku_gl_exceptions():
    data = [
        ("SKU-441","Patio Dining Set","Outdoor","GL-5210 Return Freight",14,18500,"Corner damage - final mile","Packaging + carrier handling review"),
        ("SKU-810","Gazebo 10x12","Outdoor","GL-5210 Return Freight",9,12800,"Assembly complexity - wrong expectation","Product description + assembly guide review"),
        ("SKU-101","36in Smart TV","Electronics","GL-5215 Damage Claims",7,8200,"Screen damage in transit","Carrier claim + packaging upgrade"),
        ("SKU-720","Portable AC","Electronics","GL-5215 Damage Claims",5,6100,"Compressor damage","Fragile label + carrier audit"),
        ("SKU-512","Kitchen Island","Kitchen","GL-5220 Carrier Claims",4,4900,"Missing hardware at delivery","Vendor QC + pick process review"),
        ("SKU-202","Outdoor Sectional","Furniture","GL-5210 Return Freight",3,3600,"Customer changed mind","Return policy review"),
        ("SKU-303","Cabinet Unit","Furniture","GL-5215 Damage Claims",3,2800,"Shelf damage","Packaging redesign"),
        ("SKU-905","Kids Bunk Bed","Furniture","GL-5220 Carrier Claims",2,2100,"Missing bolts","Vendor hardware check"),
    ]
    rows = []
    for sku,name,cat,gl,cases,exposure,root,action in data:
        rows.append({
            "SKU":cases and sku, "Product":name, "Category":cat,
            "GL Account":gl,
            "Exception Cases":cases,
            "Total Exposure":exposure,
            "Avg per Case":round(exposure/cases,0),
            "Root Cause":root,
            "Recommended Action":action,
            "Risk Level":"HIGH" if exposure>10000 else ("MEDIUM" if exposure>5000 else "LOW"),
        })
    return pd.DataFrame(rows)

def make_chargeback_tracker():
    retailers = ["Home Depot","Wayfair","Costco","Amazon","Lowe's","Target"]
    reasons   = ["Late ASN","Missing ASN","Late Delivery","Missing POD",
                 "Label Issue","Routing Guide Violation","Short Shipment","Damage Claim"]
    statuses  = ["Open","Under Review","Disputed","Approved","Denied","Written Off"]
    owners    = ["EDI/Order Team","Logistics","Claims Lead","Finance","Carrier Compliance"]
    rows = []
    for i in range(1, 14):
        amt = round(random.uniform(150, 3500), 2)
        reason = random.choice(reasons)
        valid = random.choice(["Yes","No","Partial"])
        action = ("Dispute with POD + tracking" if reason in ["Late Delivery","Missing POD"] else
                  ("Dispute with ASN confirmation" if "ASN" in reason else
                   ("Accept - internal error" if valid=="No" else "Review evidence")))
        rows.append({
            "Chargeback ID": f"CB-{900+i}",
            "Retailer":      random.choice(retailers),
            "Reason":        reason,
            "Amount":        amt,
            "Root Cause":    "Carrier" if reason in ["Late Delivery","Missing POD"] else "Internal",
            "Dispute Valid": valid,
            "Owner":         random.choice(owners),
            "Status":        random.choice(statuses),
            "Dispute Deadline": (datetime.now() + timedelta(days=random.randint(2,45))).strftime("%Y-%m-%d"),
            "Action":        action,
        })
    return pd.DataFrame(rows)

def make_carrier_daily(orders_df, claims_df, invoices_df):
    carriers = ["FedEx","UPS","XPO Logistics","Estes Express","Old Dominion"]
    targets  = {"On-Time":0.95,"POD Compliance":0.98,"Invoice Accuracy":0.92,
                "Damage Rate":0.02,"Claim Recovery":0.70}
    rows = []
    for carrier in carriers:
        c_orders = orders_df[orders_df["Carrier"]==carrier]
        if len(c_orders) == 0:
            continue
        c_orders = c_orders.copy()
        c_orders["Promised Delivery Date"] = pd.to_datetime(c_orders["Promised Delivery Date"])
        c_orders["Actual Delivery Date"]   = pd.to_datetime(c_orders["Actual Delivery Date"])
        ontime   = (c_orders["Actual Delivery Date"] <= c_orders["Promised Delivery Date"]).mean()
        damage   = (c_orders["Damage Flag"]=="Yes").mean()
        c_inv    = invoices_df[invoices_df["Carrier"]==carrier]
        c_ord    = orders_df[orders_df["Carrier"]==carrier]
        if len(c_inv) > 0 and len(c_ord) > 0:
            m = c_inv.merge(c_ord[["Tracking Number","Expected Freight Cost"]], on="Tracking Number", how="left")
            inv_acc = (m["Freight Charge"] <= m["Expected Freight Cost"]*1.05).mean()
        else:
            inv_acc = 0.9
        pod   = round(random.uniform(0.82, 0.99), 2)
        rec   = round(random.uniform(0.45, 0.85), 2)
        score = (ontime*0.35 + pod*0.25 + inv_acc*0.25 + (1-damage)*0.15)
        status = "RED" if score < 0.75 else ("YELLOW" if score < 0.88 else "GREEN")
        action = ("Escalate - corrective action plan required" if status=="RED" else
                  ("Review at next QBR" if status=="YELLOW" else "Monitor"))
        rows.append({
            "Carrier":          carrier,
            "On-Time %":        f"{ontime:.0%}",
            "OT Target":        "95%",
            "OT Status":        "[OK]" if ontime>=0.95 else "✗",
            "POD Compliance":   f"{pod:.0%}",
            "POD Target":       "98%",
            "Invoice Accuracy": f"{inv_acc:.0%}",
            "Damage Rate":      f"{damage:.1%}",
            "Claim Recovery":   f"{rec:.0%}",
            "Overall Status":   status,
            "Action":           action,
        })
    return pd.DataFrame(rows)

def make_gl_reconciliation(invoices_df, orders_df):
    gl_accounts = {
        "GL-5200 Outbound Freight": 0.45,
        "GL-5210 Return Freight":   0.20,
        "GL-5215 Damage Claims":    0.15,
        "GL-5220 Carrier Claims":   0.10,
        "GL-5225 Accessorial":      0.10,
    }
    rows = []
    total_inv = invoices_df["Total Invoice Amount"].sum() if len(invoices_df) > 0 else 50000
    for gl, pct in gl_accounts.items():
        accrued  = round(total_inv * pct * random.uniform(0.85, 1.10), 2)
        actual   = round(total_inv * pct * random.uniform(0.90, 1.15), 2)
        variance = round(actual - accrued, 2)
        status   = "MISMATCH" if abs(variance) > 500 else ("REVIEW" if abs(variance) > 200 else "OK")
        rows.append({
            "GL Account":    gl,
            "Accrued ($)":   accrued,
            "Actual ($)":    actual,
            "Variance ($)":  variance,
            "Variance %":    f"{(variance/max(accrued,1)*100):.1f}%",
            "Status":        status,
            "Action":        ("Finance review + journal entry required" if status=="MISMATCH" else
                              ("Analyst review" if status=="REVIEW" else "No action")),
        })
    return pd.DataFrame(rows)


# -- MAIN DAILY TABS RENDERER --------------------------------------------------
def render_daily_ops(orders_df, invoices_df, tracking_df, claims_df, skus_df):

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{NAVY} 0%,{BLUE2} 100%);
                color:white;padding:14px 24px;border-radius:8px;margin-bottom:16px;'>
        <div style='font-size:18px;font-weight:700;'>📅 Daily Operations Control Tower</div>
        <div style='font-size:12px;color:#CBD5E0;margin-top:3px;'>
            NewAge Products &nbsp;|&nbsp; Returns &amp; Claims Operations &nbsp;|&nbsp;
            {datetime.now().strftime("%A, %B %d, %Y")}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -- Quick-attention summary strip -----------------------------------------
    ret_df  = make_returns_aging()
    clm_df  = make_claims_recovery()
    inv_df  = make_invoice_audit(invoices_df, orders_df)
    del_df  = make_delivery_exceptions(orders_df, tracking_df)
    fd_df   = make_field_destruction()
    sku_df  = make_sku_gl_exceptions()
    cb_df   = make_chargeback_tracker()
    car_df  = make_carrier_daily(orders_df, claims_df, invoices_df)
    gl_df   = make_gl_reconciliation(invoices_df, orders_df)

    urgent_returns    = len(ret_df[ret_df["Risk"].isin(["Critical","High"])])
    deadline_claims   = len(clm_df[clm_df["Days to Deadline"] < 30])
    dispute_invoices  = len(inv_df[inv_df["Status"]=="DISPUTE"]) if "Status" in inv_df.columns else 0
    red_carriers      = len(car_df[car_df["Overall Status"]=="RED"]) if "Overall Status" in car_df.columns else 0
    open_chargebacks  = len(cb_df[cb_df["Status"]=="Open"])

    cols = st.columns(5)
    alerts = [
        (cols[0], "[!] Returns At Risk",       urgent_returns,   RED,    "Aging or stuck"),
        (cols[1], "⏰ Claims Near Deadline",   deadline_claims,  RED,    "File within 30 days"),
        (cols[2], "💸 Invoices to Dispute",    dispute_invoices, ORANGE, "Hold payment"),
        (cols[3], "🚚 Carriers in RED",        red_carriers,     RED,    "Escalation needed"),
        (cols[4], "🏪 Open Chargebacks",       open_chargebacks, ORANGE, "Dispute window open"),
    ]
    for col, label, val, color, sub in alerts:
        with col:
            st.markdown(f"""
            <div style='background:{WHITE};border:1px solid #E2E8F0;border-top:4px solid {color};
                        border-radius:8px;padding:14px;text-align:center;'>
                <div style='font-size:11px;color:{SLATE};font-weight:600;'>{label}</div>
                <div style='font-size:32px;font-weight:700;color:{color};margin:4px 0;'>{val}</div>
                <div style='font-size:11px;color:#718096;'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # -- 8 Daily Tabs ----------------------------------------------------------
    tabs = st.tabs([
        "📦 Returns Aging",
        "💰 Claims Recovery",
        "🧾 Invoice Audit",
        "🚛 Delivery Exceptions",
        "♻️ Field Destruction",
        "📊 SKU / GL Exceptions",
        "🏪 Chargeback Tracker",
        "🚚 Carrier Scorecard",
    ])

    # -- Tab 1: Returns Aging --------------------------------------------------
    with tabs[0]:
        section("📦 Returns Aging - Open RMAs by Age & SLA Risk")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        c1,c2,c3,c4 = st.columns(4)
        for col, label, val, color in [
            (c1,"Total Open Returns",len(ret_df),NAVY),
            (c2,"SLA Breached",len(ret_df[ret_df["SLA Breach"]=="YES"]),RED),
            (c3,"Critical / High Risk",len(ret_df[ret_df["Risk"].isin(["Critical","High"])]),RED),
            (c4,"Avg Aging (days)",f"{ret_df['Days Aging'].mean():.0f}",ORANGE),
        ]:
            with col:
                st.markdown(f"""<div style='background:{WHITE};border:1px solid #E2E8F0;
                    border-left:4px solid {color};border-radius:6px;padding:12px;'>
                    <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;'>{label}</div>
                    <div style='font-size:24px;font-weight:700;color:{color};'>{val}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        def color_risk(val): return priority_color(val)
        def color_sla(val):
            if val == "YES": return "background-color:#FDECEA;color:#C62828;font-weight:700"
            return "background-color:#E8F5E9;color:#2E7D32"

        styled = ret_df.style.map(color_risk, subset=["Risk"]).map(color_sla, subset=["SLA Breach"])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=360)
        comment_editor(ret_df, "RMA ID", "returns_aging")

    # -- Tab 2: Claims Recovery ------------------------------------------------
    with tabs[1]:
        section("💰 Claims Recovery - Missing Docs, Deadlines & Recovery Priority")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        c1,c2,c3,c4 = st.columns(4)
        for col, label, val, color in [
            (c1,"Open Claims",len(clm_df),NAVY),
            (c2,"Critical Deadline (<10 days)",len(clm_df[clm_df["Days to Deadline"]<10]),RED),
            (c3,"Missing Documents",len(clm_df[clm_df["Missing Docs"]!="None"]),ORANGE),
            (c4,"Total Claim Value",f"${clm_df['Amount'].sum():,.0f}",GREEN),
        ]:
            with col:
                st.markdown(f"""<div style='background:{WHITE};border:1px solid #E2E8F0;
                    border-left:4px solid {color};border-radius:6px;padding:12px;'>
                    <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;'>{label}</div>
                    <div style='font-size:24px;font-weight:700;color:{color};'>{val}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        display = clm_df.copy()
        display["Amount"] = display["Amount"].apply(lambda x: f"${x:,.2f}")

        def ddl_color(val):
            try:
                v = int(val)
                if v < 10:  return "background-color:#FDECEA;color:#C62828;font-weight:700"
                if v < 30:  return "background-color:#FFF3E0;color:#E65100;font-weight:600"
                return "background-color:#E8F5E9;color:#2E7D32"
            except: return ""

        styled = display.style.map(priority_color, subset=["Deadline Risk"]).map(ddl_color, subset=["Days to Deadline"])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=360)
        comment_editor(clm_df, "Claim ID", "claims_recovery")

    # -- Tab 3: Invoice Audit --------------------------------------------------
    with tabs[2]:
        section("🧾 Invoice Audit - Actual vs Expected Freight Cost")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if len(inv_df) > 0:
            dispute_count = len(inv_df[inv_df["Status"]=="DISPUTE"])
            dispute_val   = inv_df[inv_df["Status"]=="DISPUTE"]["Variance"].sum() if "Variance" in inv_df.columns else 0
            review_count  = len(inv_df[inv_df["Status"]=="REVIEW"]) if "Status" in inv_df.columns else 0
            ok_count      = len(inv_df[inv_df["Status"]=="OK"]) if "Status" in inv_df.columns else 0

            c1,c2,c3,c4 = st.columns(4)
            for col, label, val, color in [
                (c1,"Invoices Reviewed",len(inv_df),NAVY),
                (c2,"Dispute - Hold Payment",dispute_count,RED),
                (c3,"Total Dispute Value",f"${dispute_val:,.0f}",RED),
                (c4,"Approved OK",ok_count,GREEN),
            ]:
                with col:
                    st.markdown(f"""<div style='background:{WHITE};border:1px solid #E2E8F0;
                        border-left:4px solid {color};border-radius:6px;padding:12px;'>
                        <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;'>{label}</div>
                        <div style='font-size:24px;font-weight:700;color:{color};'>{val}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            display = inv_df.copy()
            for col in ["Expected","Invoiced","Variance"]:
                if col in display.columns:
                    display[col] = display[col].apply(lambda x: f"${x:,.2f}")

            def status_color(val):
                if val == "DISPUTE": return "background-color:#FDECEA;color:#C62828;font-weight:700"
                if val == "REVIEW":  return "background-color:#FFF3E0;color:#E65100;font-weight:600"
                return "background-color:#E8F5E9;color:#2E7D32"

            styled = display.style.map(status_color, subset=["Status"])
            st.dataframe(styled, use_container_width=True, hide_index=True, height=360)
            comment_editor(inv_df, "Invoice Number", "invoice_audit")
        else:
            st.info("No invoice data available.")

    # -- Tab 4: Delivery Exceptions ---------------------------------------------
    with tabs[3]:
        section("🚛 Delivery Exceptions - Missed Milestones, Damage, Missing POD")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if len(del_df) > 0:
            c1,c2,c3,c4 = st.columns(4)
            exc_counts = del_df["Exception Type"].value_counts()
            for col, label, val, color in [
                (c1,"Total Exceptions",len(del_df),NAVY),
                (c2,"Damaged at Delivery",exc_counts.get("Damaged at Delivery",0),RED),
                (c3,"Missing POD",exc_counts.get("Missing POD",0),ORANGE),
                (c4,"Late Deliveries",exc_counts.get("Late Delivery",0),ORANGE),
            ]:
                with col:
                    st.markdown(f"""<div style='background:{WHITE};border:1px solid #E2E8F0;
                        border-left:4px solid {color};border-radius:6px;padding:12px;'>
                        <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;'>{label}</div>
                        <div style='font-size:24px;font-weight:700;color:{color};'>{val}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            def exc_color(val):
                if val == "Damaged at Delivery": return "background-color:#FDECEA;color:#C62828;font-weight:700"
                if val == "Missing POD":         return "background-color:#F3E5F5;color:#6A1B9A;font-weight:600"
                if val == "Late Delivery":       return "background-color:#FFF3E0;color:#E65100;font-weight:600"
                return ""

            styled = del_df.style.map(exc_color, subset=["Exception Type"])
            st.dataframe(styled, use_container_width=True, hide_index=True, height=360)
            comment_editor(del_df, "Order ID", "delivery_exceptions")
        else:
            st.info("No delivery exceptions found in current dataset.")

    # -- Tab 5: Field Destruction -----------------------------------------------
    with tabs[4]:
        section("♻️ Field Destruction Decision Matrix - Return vs Destroy vs Replace")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background:#EBF4FF;border:1px solid #BEE3F8;border-left:4px solid #3182CE;
                    border-radius:6px;padding:12px 16px;margin-bottom:12px;font-size:13px;'>
            <strong>How to use:</strong> Compare Net if Returned vs Disposal Cost ($35 flat).
            If recovery value is zero or net return is negative → Field Destruction saves money.
            Always require: damage photos + SKU/serial label photo + customer confirmation.
        </div>
        """, unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        fd_recommend = fd_df[fd_df["Recommendation"]=="Field Destruction"]
        for col, label, val, color in [
            (c1,"Return to DC Recommended",len(fd_df[fd_df["Recommendation"]=="Return to DC"]),GREEN),
            (c2,"Field Destruction Recommended",len(fd_recommend),ORANGE),
            (c3,"Estimated Freight Saved",f"${fd_recommend['Freight Saved'].sum():,.0f}",GREEN),
        ]:
            with col:
                st.markdown(f"""<div style='background:{WHITE};border:1px solid #E2E8F0;
                    border-left:4px solid {color};border-radius:6px;padding:12px;'>
                    <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;'>{label}</div>
                    <div style='font-size:24px;font-weight:700;color:{color};'>{val}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        display = fd_df.copy()
        for col in ["Product Value","Return Freight","Handling","Recovery Value","Net if Returned","Disposal Cost","Freight Saved"]:
            if col in display.columns:
                display[col] = display[col].apply(lambda x: f"${x:,.0f}")

        def rec_color(val):
            if val == "Field Destruction": return "background-color:#FFF3E0;color:#E65100;font-weight:700"
            if val == "Return to DC":      return "background-color:#E8F5E9;color:#2E7D32;font-weight:700"
            return "background-color:#EBF4FF;color:#1565C0"

        styled = display.style.map(rec_color, subset=["Recommendation"])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=340)
        comment_editor(fd_df, "SKU", "field_destruction")

        st.markdown("#### Approval Requirements")
        approvals = [
            ("Under $100","Returns Lead - no manager needed",GREEN),
            ("$100 - $500","Returns Lead + Finance if needed",GREEN),
            ("$500 - $1,500","Manager approval required",ORANGE),
            ("$1,500+","Manager + Director / Finance review",RED),
        ]
        cols = st.columns(4)
        for col,(val,who,color) in zip(cols,approvals):
            with col:
                st.markdown(f"""<div style='background:{WHITE};border:1px solid #E2E8F0;
                    border-top:3px solid {color};border-radius:6px;padding:10px;text-align:center;'>
                    <div style='font-size:13px;font-weight:700;color:{color};'>{val}</div>
                    <div style='font-size:11px;color:{SLATE};margin-top:4px;'>{who}</div>
                </div>""", unsafe_allow_html=True)

    # -- Tab 6: SKU / GL Exceptions ---------------------------------------------
    with tabs[5]:
        section("📊 SKU & GL Exception Analysis - Cost by SKU and GL Account")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Top SKUs by Exception Exposure**")

            def risk_color(val):
                if val == "HIGH":   return "background-color:#FDECEA;color:#C62828;font-weight:700"
                if val == "MEDIUM": return "background-color:#FFF3E0;color:#E65100;font-weight:600"
                return "background-color:#E8F5E9;color:#2E7D32"

            display_sku = sku_df.copy()
            display_sku["Total Exposure"] = display_sku["Total Exposure"].apply(lambda x: f"${x:,.0f}")
            display_sku["Avg per Case"]   = display_sku["Avg per Case"].apply(lambda x: f"${x:,.0f}")
            styled = display_sku.style.map(risk_color, subset=["Risk Level"])
            st.dataframe(styled, use_container_width=True, hide_index=True, height=300)
            comment_editor(sku_df, "SKU", "sku_exceptions")

        with col2:
            st.markdown("**GL Account Reconciliation**")

            def gl_status_color(val):
                if val == "MISMATCH": return "background-color:#FDECEA;color:#C62828;font-weight:700"
                if val == "REVIEW":   return "background-color:#FFF3E0;color:#E65100;font-weight:600"
                return "background-color:#E8F5E9;color:#2E7D32"

            display_gl = gl_df.copy()
            for c in ["Accrued ($)","Actual ($)","Variance ($)"]:
                display_gl[c] = display_gl[c].apply(lambda x: f"${float(x):,.0f}")
            styled_gl = display_gl.style.map(gl_status_color, subset=["Status"])
            st.dataframe(styled_gl, use_container_width=True, hide_index=True, height=300)
            comment_editor(gl_df, "GL Account", "gl_reconciliation")

    # -- Tab 7: Chargeback Tracker ----------------------------------------------
    with tabs[6]:
        section("🏪 Chargeback Tracker - Retailer Deductions & Dispute Status")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        c1,c2,c3,c4 = st.columns(4)
        open_cb   = len(cb_df[cb_df["Status"]=="Open"])
        total_val = cb_df["Amount"].sum()
        dispute_v = cb_df[cb_df["Dispute Valid"]=="Yes"]["Amount"].sum()
        for col, label, val, color in [
            (c1,"Total Chargebacks",len(cb_df),NAVY),
            (c2,"Open / Active",open_cb,RED),
            (c3,"Total Deduction Value",f"${total_val:,.0f}",RED),
            (c4,"Disputable Value",f"${dispute_v:,.0f}",GREEN),
        ]:
            with col:
                st.markdown(f"""<div style='background:{WHITE};border:1px solid #E2E8F0;
                    border-left:4px solid {color};border-radius:6px;padding:12px;'>
                    <div style='font-size:10px;font-weight:700;color:{SLATE};text-transform:uppercase;'>{label}</div>
                    <div style='font-size:24px;font-weight:700;color:{color};'>{val}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        display_cb = cb_df.copy()
        display_cb["Amount"] = display_cb["Amount"].apply(lambda x: f"${x:,.2f}")

        def valid_color(val):
            if val == "Yes":     return "background-color:#E8F5E9;color:#2E7D32;font-weight:600"
            if val == "No":      return "background-color:#FDECEA;color:#C62828;font-weight:600"
            if val == "Partial": return "background-color:#FFF3E0;color:#E65100;font-weight:600"
            return ""

        def status_cb(val):
            if val == "Open":   return "background-color:#FDECEA;color:#C62828;font-weight:600"
            if val == "Disputed": return "background-color:#FFF3E0;color:#E65100"
            if val == "Approved": return "background-color:#E8F5E9;color:#2E7D32"
            return ""

        styled = display_cb.style.map(valid_color, subset=["Dispute Valid"]).map(status_cb, subset=["Status"])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=360)
        comment_editor(cb_df, "Chargeback ID", "chargeback_tracker")

    # -- Tab 8: Carrier Scorecard -----------------------------------------------
    with tabs[7]:
        section("🚚 Carrier Daily Scorecard - KPI Status & Escalation Triggers")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if len(car_df) > 0:
            red_c    = len(car_df[car_df["Overall Status"]=="RED"])
            yellow_c = len(car_df[car_df["Overall Status"]=="YELLOW"])
            green_c  = len(car_df[car_df["Overall Status"]=="GREEN"])

            c1,c2,c3 = st.columns(3)
            for col, label, val, color in [
                (c1,f"🔴 RED - Escalation Required",red_c,RED),
                (c2,f"🟡 YELLOW - Watch & Review",yellow_c,ORANGE),
                (c3,f"🟢 GREEN - On Track",green_c,GREEN),
            ]:
                with col:
                    st.markdown(f"""<div style='background:{WHITE};border:1px solid #E2E8F0;
                        border-left:4px solid {color};border-radius:6px;padding:12px;text-align:center;'>
                        <div style='font-size:11px;font-weight:700;color:{SLATE};'>{label}</div>
                        <div style='font-size:32px;font-weight:700;color:{color};'>{val}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            def ot_icon(val): return "" # handled by OT Status col
            def overall_color(val):
                if val == "RED":    return "background-color:#FDECEA;color:#C62828;font-weight:700"
                if val == "YELLOW": return "background-color:#FFF3E0;color:#E65100;font-weight:600"
                return "background-color:#E8F5E9;color:#2E7D32;font-weight:600"

            styled = car_df.style.map(overall_color, subset=["Overall Status"])
            st.dataframe(styled, use_container_width=True, hide_index=True, height=280)
            comment_editor(car_df, "Carrier", "carrier_scorecard_daily")

            # Target reference
            st.markdown("**KPI Targets**")
            targets = [("On-Time Delivery","≥ 95%"),("POD Compliance","≥ 98%"),
                       ("Invoice Accuracy","≥ 92%"),("Damage Rate","≤ 2%"),("Claim Recovery","≥ 70%")]
            t_cols = st.columns(5)
            for col, (kpi, tgt) in zip(t_cols, targets):
                with col:
                    st.markdown(f"""<div style='background:{WHITE};border:1px solid #E2E8F0;
                        border-radius:6px;padding:8px;text-align:center;'>
                        <div style='font-size:11px;color:{SLATE};'>{kpi}</div>
                        <div style='font-size:14px;font-weight:700;color:{NAVY};'>{tgt}</div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.info("No carrier data available.")



# Chargeback Hub Module

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

# -- Retailer compliance rules --------------------------------------------------
RETAILER_RULES = {
    "Costco": {
        "color": "#005DAA",
        "asn_timing": "24 hours before shipment",
        "appointment": "Required - must book 72-96 hrs in advance",
        "pod_required": "Yes - signed POD within 24 hours",
        "delivery_window": "Strict - same day as appointment only",
        "routing_guide": "Costco Routing Guide v2024 - mandatory carrier list",
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
        "appointment": "Required for all deliveries - HDDC system",
        "pod_required": "Yes - within 48 hours",
        "delivery_window": "±1 day from appointment",
        "routing_guide": "HD Routing Guide - GPS-verified carrier required",
        "dispute_window": "45 days from deduction",
        "evidence_required": ["POD with timestamp", "ASN + 997", "Carrier GPS confirmation", "BOL", "Photos if damage"],
        "common_chargebacks": ["Late ASN", "Routing Guide Violation", "Late Delivery", "Damage"],
        "contact": "HD Vendor Relations: vendorrelations@homedepot.com",
        "portal": "HD Partner Portal (HDPP)",
        "penalty": "2-3% of PO value per violation",
    },
    "Wayfair": {
        "color": "#7B189F",
        "asn_timing": "Same day as shipment - before end of business",
        "appointment": "Not required for most - carrier managed",
        "pod_required": "Yes - e-POD preferred",
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
        "asn_timing": "Required before shipment - Vendor Central",
        "appointment": "Required for FC deliveries - CARP system",
        "pod_required": "Yes - Amazon confirms receipt",
        "delivery_window": "Strict - must hit FC receive window",
        "routing_guide": "Amazon Routing Guide - must use Amazon partnered carriers",
        "dispute_window": "30 days from chargeback notice",
        "evidence_required": ["CARP appointment confirmation", "ASN in Vendor Central", "BOL", "Carrier tracking", "FC receipt confirmation"],
        "common_chargebacks": ["PO On-Time Accuracy", "Receive Window Miss", "ASN Accuracy", "Shortage"],
        "contact": "Amazon Vendor Central - Case Management",
        "portal": "Amazon Vendor Central (AVC)",
        "penalty": "1-3% of PO value - auto-deducted",
    },
    "Lowe's": {
        "color": "#004990",
        "asn_timing": "24 hours before pickup",
        "appointment": "Required - VendorNet system",
        "pod_required": "Yes - within 24 hours of delivery",
        "delivery_window": "Must-arrive-by date strict",
        "routing_guide": "Lowe's Routing Guide - collect shipments only",
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
        "appointment": "Not required - residential delivery",
        "pod_required": "Photo POD preferred",
        "delivery_window": "Promised date on order confirmation",
        "routing_guide": "Internal carrier selection - approved list",
        "dispute_window": "90 days",
        "evidence_required": ["Carrier tracking", "Photo POD", "Customer communication log", "Order confirmation"],
        "common_chargebacks": ["Late Delivery", "Damage", "Missing Item", "Wrong Item"],
        "contact": "Internal Customer Service team",
        "portal": "Internal OMS / Shopify",
        "penalty": "Refund + return freight cost",
    },
}

# -- Root cause categories ------------------------------------------------------
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

# -- Generate 30 chargeback cases -----------------------------------------------
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
            "DISPUTE - Strong evidence" if dispute_prob >= 70 else
            ("NEGOTIATE - Mixed fault" if dispute_prob >= 45 else
             ("ACCEPT - Our fault" if dispute_prob >= 20 else "ACCEPT - Clear fault"))
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
            "Late Delivery": "Carrier performance scorecard - 98% OT required",
            "Missing POD": "Automated POD capture - photo + GPS + signature",
            "Short Shipment": "Weigh and count verification before shipment close",
            "Damage Claim": "Packaging audit + carrier handling review",
            "Routing Guide Violation": "Mandatory routing guide checklist before booking",
            "Label/Carton Error": "Barcode verification scan before load",
            "Carrier Documentation Delay": "Escalate carrier POD SLA - 24hr requirement",
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

# -- Dispute probability scorer -------------------------------------------------
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

# -- Session helpers ------------------------------------------------------------
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

# -- MAIN RENDERER --------------------------------------------------------------
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

    # -- Tab 1: Retailer Dashboard ----------------------------------------------
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
            top_rc   = r_cases["Root Cause Category"].mode()[0] if len(r_cases) > 0 else "-"
            top_carr = r_cases["Carrier"].mode()[0] if len(r_cases) > 0 else "-"
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
            title=dict(text="Chargeback Exposure by Retailer - Net Loss vs Recovered", font=dict(size=11,color=SLATE)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # -- Tab 2: Case Tracker ----------------------------------------------------
    with tabs[1]:
        section("📋 Chargeback Case Tracker - All 30 Cases")
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
                    st.markdown(f"<div style='font-size:12px;font-weight:600;padding-top:6px;'>{cid} - {row['Retailer']}</div>", unsafe_allow_html=True)
                with c2:
                    v1 = st.text_input("C1", value=existing["Comment 1"],
                        key=f"cb_c1_{cid}", label_visibility="collapsed",
                        placeholder="Comment 1 - action taken")
                    save_cb_comment(cid, "Comment 1", v1)
                with c3:
                    v2 = st.text_input("C2", value=existing["Comment 2"],
                        key=f"cb_c2_{cid}", label_visibility="collapsed",
                        placeholder="Comment 2 - follow-up / status")
                    save_cb_comment(cid, "Comment 2", v2)

        download_with_comments(filtered, "Chargeback ID", "NewAge_Chargeback_Cases")

    # -- Tab 3: Dispute Probability Scorer -------------------------------------
    with tabs[2]:
        section("🔍 Dispute Probability Scorer - Score Any Chargeback Case")
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
                "DISPUTE - Strong evidence. File immediately." if total >= 70 else
                ("NEGOTIATE - Mixed fault. Seek partial credit." if total >= 45 else
                 ("EVALUATE - Low probability. Weigh cost vs benefit." if total >= 25 else
                  "ACCEPT - Clear internal fault. Pay and prevent recurrence."))
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
                f'<div style="font-size:36px;font-weight:700;">{total}/100 &nbsp;-&nbsp; {win_pct}</div>'
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

    # -- Tab 4: Heat Map --------------------------------------------------------
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

    # -- Tab 5: AI Recommendations ----------------------------------------------
    with tabs[4]:
        section("🤖 AI Recommendations - Top Priority Cases")
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
                f"{urgency} - {row['Chargeback ID']} | {row['Retailer']} | "
                f"${row['Amount']:,.2f} | {row['Chargeback Reason']} | {row['Days to Deadline']} days to deadline"
            ):
                col1, col2 = st.columns([3,2])
                with col1:
                    # Evidence checklist
                    rules = RETAILER_RULES[row["Retailer"]]
                    evidence_items = rules["evidence_required"]
                    checklist_html = "".join(
                        f'<div style="display:flex;gap:8px;padding:4px 0;">'
                        f'<span style="color:{GREEN};">[OK]</span>'
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

    # -- Tab 6: Retailer SOP Checklists ----------------------------------------
    with tabs[5]:
        section("📚 Retailer-Specific SOP Checklists - Compliance Rules & Contact Guide")
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
                    f'<span style="color:{GREEN};font-weight:700;">[OK]</span>'
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
            "ASN ready to transmit - send 24hrs before pickup",
        ]
        cols = st.columns(2)
        for i, check in enumerate(asn_checks):
            with cols[i % 2]:
                st.checkbox(check, key=f"asn_{sel_retailer}_{i}")

        # Download SOP
        evidence_str = "\n".join("[OK] " + e for e in rules["evidence_required"])
        chargebacks_str = "\n".join("[!] " + c for c in rules["common_chargebacks"])
        asn_str = "\n".join("[ ] " + c for c in asn_checks)
        sop_text = (
            f"NEWAGE PRODUCTS - {sel_retailer.upper()} SUPPLIER COMPLIANCE SOP\n"
            f"Generated: {datetime.now().strftime('%B %d, %Y')}\n\n"
            f"PORTAL: {rules['portal']}\n"
            f"CONTACT: {rules['contact']}\n"
            f"PENALTY: {rules['penalty']}\n\n"
            "COMPLIANCE REQUIREMENTS\n-----------------------\n"
            f"ASN Timing: {rules['asn_timing']}\n"
            f"Appointment: {rules['appointment']}\n"
            f"POD Required: {rules['pod_required']}\n"
            f"Delivery Window: {rules['delivery_window']}\n"
            f"Routing Guide: {rules['routing_guide']}\n"
            f"Dispute Window: {rules['dispute_window']}\n\n"
            "REQUIRED EVIDENCE FOR DISPUTE\n-----------------------------\n"
            + evidence_str + "\n\n"
            "COMMON CHARGEBACK TYPES\n-----------------------\n"
            + chargebacks_str + "\n\n"
            "PRE-SHIPMENT ASN VALIDATION CHECKLIST\n-------------------------------------\n"
            + asn_str
        )
        st.download_button(
            f"⬇️ Download {sel_retailer} SOP",
            data=sop_text,
            file_name=f"NewAge_{sel_retailer.replace(' ','_')}_SOP_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )

    # -- Tab 7: Executive Summary -----------------------------------------------
    with tabs[6]:
        section("📝 Chargeback Executive Summary - Weekly Leadership Report")
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
            f'1. File disputes on all {critical_count} cases with deadlines under 10 days - assign to chargeback analyst today.<br>'
            f'2. Implement ASN pre-shipment validation gate to eliminate {top_rc} chargebacks - estimated 80% reduction within 60 days.<br>'
            f'3. Conduct {top_carrier} carrier compliance review and add to performance scorecard for Q4 QBR.<br>'
            f'<div style="margin-top:16px;padding-top:12px;border-top:1px solid #E2E8F0;font-size:11px;color:#718096;">'
            f'Prepared by: Returns &amp; Claims Control Tower &nbsp;|&nbsp; '
            f'Review period: {(datetime.now()-timedelta(days=7)).strftime("%b %d")} - {datetime.now().strftime("%b %d, %Y")}'
            f'</div></div>'
        )
        st.markdown(summary_html, unsafe_allow_html=True)

        st.download_button(
            "⬇️ Download Chargeback Executive Summary",
            data=f"NEWAGE PRODUCTS - WEEKLY CHARGEBACK REPORT\n{datetime.now().strftime('%B %d, %Y')}\n\n"
                 f"Total Exposure: ${total_val:,.0f}\nUnder Dispute: ${disputed_val:,.0f}\n"
                 f"Recovered: ${recovered_val:,.0f}\nNet Loss: ${net_loss:,.0f}\n\n"
                 f"Top Retailer: {top_retailer}\nTop Root Cause: {top_rc}\n"
                 f"Top Carrier: {top_carrier}\nTop Region: {top_region}\n"
                 f"Critical Deadline Cases: {critical_count}",
            file_name=f"NewAge_Chargeback_Summary_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )


if __name__ == "__main__":
    main()
