"""
NewAge Products — Daily Operations Control Tower
v4 — Daily tabs module
All 8 daily operating tabs with Comment 1 + Comment 2 + Download on every table
"""

import streamlit as st
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

# ── Session state helpers ──────────────────────────────────────────────────────
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

    # Editable comment area — compact 2-column layout
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
                    placeholder="Comment 1 — action taken / owner")
                save_comment(table_key, row_id, "Comment 1", v1)
            with c3:
                v2 = st.text_input(f"Comment 2", value=existing.get("Comment 2",""),
                    key=f"{table_key}_{row_id}_c2", label_visibility="collapsed",
                    placeholder="Comment 2 — follow-up / status")
                save_comment(table_key, row_id, "Comment 2", v2)

    export_df = apply_comments(df, id_col, table_key)
    download_button(export_df, table_key)
    return export_df

# ── Synthetic daily data generators ───────────────────────────────────────────
def make_returns_aging():
    statuses = ["Pickup Requested","Pickup Scheduled","Stuck with Carrier",
                "In Transit","Received — Not Inspected","Inspected — Not Dispositioned","Closed"]
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
            "Pickup Requested":              "Escalate carrier — pickup overdue",
            "Stuck with Carrier":            "Contact carrier terminal today — SLA breach",
            "Received — Not Inspected":      "Assign inspection — DC queue review",
            "Inspected — Not Dispositioned": "Manager decision required — disposition pending",
        }
        action = action_map.get(status, "Monitor — within SLA")
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
        action = "FILE TODAY — deadline critical" if ddl < 10 else \
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
            f"Dispute — ${r['Variance']:,.2f} overcharge" if r["Status"]=="DISPUTE" else
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
            "High — refund/replacement risk" if t=="Damaged at Delivery" else
            ("Medium — claim eligibility at risk" if t=="Missing POD" else
             ("Medium — SLA breach" if t=="Late Delivery" else "Low")))
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
            recommendation = "Assess — marginal return"
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
        ("SKU-441","Patio Dining Set","Outdoor","GL-5210 Return Freight",14,18500,"Corner damage — final mile","Packaging + carrier handling review"),
        ("SKU-810","Gazebo 10x12","Outdoor","GL-5210 Return Freight",9,12800,"Assembly complexity — wrong expectation","Product description + assembly guide review"),
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
                   ("Accept — internal error" if valid=="No" else "Review evidence")))
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
        action = ("Escalate — corrective action plan required" if status=="RED" else
                  ("Review at next QBR" if status=="YELLOW" else "Monitor"))
        rows.append({
            "Carrier":          carrier,
            "On-Time %":        f"{ontime:.0%}",
            "OT Target":        "95%",
            "OT Status":        "✓" if ontime>=0.95 else "✗",
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


# ── MAIN DAILY TABS RENDERER ──────────────────────────────────────────────────
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

    # ── Quick-attention summary strip ─────────────────────────────────────────
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
        (cols[0], "⚠️ Returns At Risk",       urgent_returns,   RED,    "Aging or stuck"),
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

    # ── 8 Daily Tabs ──────────────────────────────────────────────────────────
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

    # ── Tab 1: Returns Aging ──────────────────────────────────────────────────
    with tabs[0]:
        section("📦 Returns Aging — Open RMAs by Age & SLA Risk")
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

    # ── Tab 2: Claims Recovery ────────────────────────────────────────────────
    with tabs[1]:
        section("💰 Claims Recovery — Missing Docs, Deadlines & Recovery Priority")
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

    # ── Tab 3: Invoice Audit ──────────────────────────────────────────────────
    with tabs[2]:
        section("🧾 Invoice Audit — Actual vs Expected Freight Cost")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if len(inv_df) > 0:
            dispute_count = len(inv_df[inv_df["Status"]=="DISPUTE"])
            dispute_val   = inv_df[inv_df["Status"]=="DISPUTE"]["Variance"].sum() if "Variance" in inv_df.columns else 0
            review_count  = len(inv_df[inv_df["Status"]=="REVIEW"]) if "Status" in inv_df.columns else 0
            ok_count      = len(inv_df[inv_df["Status"]=="OK"]) if "Status" in inv_df.columns else 0

            c1,c2,c3,c4 = st.columns(4)
            for col, label, val, color in [
                (c1,"Invoices Reviewed",len(inv_df),NAVY),
                (c2,"Dispute — Hold Payment",dispute_count,RED),
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

    # ── Tab 4: Delivery Exceptions ─────────────────────────────────────────────
    with tabs[3]:
        section("🚛 Delivery Exceptions — Missed Milestones, Damage, Missing POD")
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

    # ── Tab 5: Field Destruction ───────────────────────────────────────────────
    with tabs[4]:
        section("♻️ Field Destruction Decision Matrix — Return vs Destroy vs Replace")
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
            ("Under $100","Returns Lead — no manager needed",GREEN),
            ("$100 – $500","Returns Lead + Finance if needed",GREEN),
            ("$500 – $1,500","Manager approval required",ORANGE),
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

    # ── Tab 6: SKU / GL Exceptions ─────────────────────────────────────────────
    with tabs[5]:
        section("📊 SKU & GL Exception Analysis — Cost by SKU and GL Account")
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

    # ── Tab 7: Chargeback Tracker ──────────────────────────────────────────────
    with tabs[6]:
        section("🏪 Chargeback Tracker — Retailer Deductions & Dispute Status")
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

    # ── Tab 8: Carrier Scorecard ───────────────────────────────────────────────
    with tabs[7]:
        section("🚚 Carrier Daily Scorecard — KPI Status & Escalation Triggers")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if len(car_df) > 0:
            red_c    = len(car_df[car_df["Overall Status"]=="RED"])
            yellow_c = len(car_df[car_df["Overall Status"]=="YELLOW"])
            green_c  = len(car_df[car_df["Overall Status"]=="GREEN"])

            c1,c2,c3 = st.columns(3)
            for col, label, val, color in [
                (c1,f"🔴 RED — Escalation Required",red_c,RED),
                (c2,f"🟡 YELLOW — Watch & Review",yellow_c,ORANGE),
                (c3,f"🟢 GREEN — On Track",green_c,GREEN),
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
