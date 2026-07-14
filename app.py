"""
app.py
------
SaaS Subscription Renewal & Expansion Analytics — main Streamlit app.

Run with: streamlit run app.py
"""

import os
import pandas as pd
import streamlit as st

from data_generator import generate_subscription_data
from eda import (
    clean_data, cohort_retention_table, renewal_pipeline, high_risk_customers,
    retention_opportunities, segment_customers, revenue_insights, churn_insights, health_insights,
)
from metrics import kpi_summary, what_if_simulator
from utils import apply_filters, format_currency, format_percent, health_bucket, risk_bucket
from ai_insights import generate_executive_summary
from report_generator import generate_markdown_report
import visualization as viz

st.set_page_config(
    page_title="Renewal & Expansion Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    csv_path = os.path.join("data", "subscriptions.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, parse_dates=["subscription_start_date", "renewal_date"])
    else:
        df = generate_subscription_data(4200)
    return clean_data(df)


def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()
df_full = load_data()

TODAY = pd.Timestamp(2026, 7, 11)


# ---------------------------------------------------------------------
# Sidebar — filters
# ---------------------------------------------------------------------
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.svg")
    if os.path.exists(logo_path):
        st.markdown(
            "<div style='text-align:center; padding: 6px 0 12px 0;'>"
            f"<img src='data:image/svg+xml;base64,{__import__('base64').b64encode(open(logo_path,'rb').read()).decode()}' width='96'/>"
            "<div style='font-size:0.75rem; color:#94A3B8; margin-top:8px;'>Subscription Intelligence Platform</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='text-align:center; padding: 6px 0 18px 0;'>"
            "<div style='font-weight:800; font-size:1.05rem; letter-spacing:0.02em;'>APEX RENEWAL</div>"
            "<div style='font-size:0.75rem; color:#94A3B8;'>Subscription Intelligence Platform</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.markdown("**Filters**")

    min_date, max_date = df_full["renewal_date"].min(), df_full["renewal_date"].max()
    date_range = st.date_input(
        "Renewal date range", value=(min_date.date(), max_date.date()),
        min_value=min_date.date(), max_value=max_date.date(),
    )

    regions = st.multiselect("Region", sorted(df_full["region"].unique()))
    industries = st.multiselect("Industry", sorted(df_full["industry"].unique()))
    plans = st.multiselect("Subscription Plan", sorted(df_full["plan"].unique()))
    company_sizes = st.multiselect("Company Size", sorted(df_full["company_size"].unique()))

    st.markdown("---")
    theme_mode = st.radio("Theme", ["Light", "Dark"], horizontal=True, index=0)

    st.markdown("---")
    st.caption("Data refreshes on reload · synthetic dataset for portfolio/demo purposes")

filters = {
    "date_range": date_range if isinstance(date_range, tuple) and len(date_range) == 2 else None,
    "regions": regions,
    "industries": industries,
    "plans": plans,
    "company_sizes": company_sizes,
}
df = apply_filters(df_full, filters)

if theme_mode == "Dark":
    st.markdown(
        "<style>.stApp{background:linear-gradient(180deg,#0B1224 0%,#0F1A33 100%);} "
        ".kpi-card{background:rgba(22,32,58,0.75); border-color:rgba(255,255,255,0.08);} "
        ".kpi-value{color:#F1F5F9;} .section-title{color:#F1F5F9;} "
        "p, span, div, label, .section-subtitle{color:#CBD5E1 !important;}</style>",
        unsafe_allow_html=True,
    )

if len(df) == 0:
    st.warning("No accounts match the current filters. Try widening your filter selection.")
    st.stop()


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.markdown(
    "<div class='app-header'>"
    "<h1>Subscription Renewal &amp; Expansion Analytics</h1>"
    "<p>Executive intelligence for renewals, churn, expansion revenue, and customer health — updated in real time as filters change.</p>"
    "</div>",
    unsafe_allow_html=True,
)

kpis = kpi_summary(df)


# ---------------------------------------------------------------------
# Executive KPI cards
# ---------------------------------------------------------------------
def kpi_card(label, value, sub=None):
    sub_html = f"<div class='kpi-sub'>{sub}</div>" if sub else "<div class='kpi-sub kpi-sub-empty'>&nbsp;</div>"
    st.markdown(
        f"<div class='kpi-card'><div class='kpi-accent-bar'></div>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div>{sub_html}</div>",
        unsafe_allow_html=True,
    )


row1 = st.columns(4)
with row1[0]: kpi_card("Monthly Recurring Revenue", format_currency(kpis["mrr"]))
with row1[1]: kpi_card("Annual Recurring Revenue", format_currency(kpis["arr"]))
with row1[2]: kpi_card("Net Revenue Retention", format_percent(kpis["nrr"]), "Target: 100%+")
with row1[3]: kpi_card("Churn Rate", format_percent(kpis["churn_rate"]))

row2 = st.columns(4)
with row2[0]: kpi_card("Avg. Customer Health", f"{kpis['customer_health']:.0f}/100")
with row2[1]: kpi_card("Renewal Rate", format_percent(kpis["renewal_rate"]))
with row2[2]: kpi_card("Expansion Revenue", format_currency(kpis["expansion_revenue"]), "monthly")
with row2[3]: kpi_card("Avg. Customer LTV", format_currency(kpis["clv"]))

extra_row = st.columns(4)
with extra_row[0]: kpi_card("GRR", format_percent(kpis["grr"]))
with extra_row[1]: kpi_card("ARPA (monthly)", format_currency(kpis["arpa"]))
with extra_row[2]: kpi_card("ACV (annual)", format_currency(kpis["acv"]))
with extra_row[3]: kpi_card("Revenue Leakage", format_currency(kpis["revenue_leakage"]), "monthly")


# ---------------------------------------------------------------------
# Tabbed analytics sections
# ---------------------------------------------------------------------
tabs = st.tabs([
    "Revenue Analytics", "Customer Health", "Churn Analytics", "Cohort Analysis",
    "Industry & Region", "Plan Performance", "Feature Adoption", "Customer Intelligence",
    "Executive Insights", "What-If Simulator",
])

# ---- Revenue Analytics ----
with tabs[0]:
    st.markdown("<div class='section-title'>Revenue Analytics</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.plotly_chart(viz.mrr_trend_chart(df), use_container_width=True)
    with c2:
        st.plotly_chart(viz.renewal_status_donut(df), use_container_width=True)
    st.plotly_chart(viz.revenue_bridge_chart(df), use_container_width=True)
    for ins in revenue_insights(df):
        st.markdown(f"<div class='insight-box'>💡 {ins}</div>", unsafe_allow_html=True)

# ---- Customer Health ----
with tabs[1]:
    st.markdown("<div class='section-title'>Customer Health Dashboard</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(viz.health_gauge(kpis["customer_health"]), use_container_width=True)
    with c2:
        st.plotly_chart(viz.health_distribution_histogram(df), use_container_width=True)
    st.plotly_chart(viz.risk_vs_mrr_scatter(df), use_container_width=True)
    for ins in health_insights(df):
        st.markdown(f"<div class='insight-box'>💡 {ins}</div>", unsafe_allow_html=True)

# ---- Churn Analytics ----
with tabs[2]:
    st.markdown("<div class='section-title'>Churn Analytics</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(viz.churn_reason_bar(df), use_container_width=True)
    with c2:
        st.plotly_chart(viz.segment_stacked_bar(df), use_container_width=True)
    for ins in churn_insights(df):
        st.markdown(f"<div class='risk-box'>⚠️ {ins}</div>", unsafe_allow_html=True)

# ---- Cohort Analysis ----
with tabs[3]:
    st.markdown("<div class='section-title'>Cohort Retention Analysis</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Percentage of each monthly signup cohort still active, by months since subscription start.</div>",
        unsafe_allow_html=True,
    )
    cohort_table = cohort_retention_table(df)
    if cohort_table.shape[0] > 0 and cohort_table.shape[1] > 0:
        st.plotly_chart(viz.cohort_heatmap(cohort_table.iloc[-12:, :12]), use_container_width=True)
    else:
        st.info("Not enough data in the current filter to build a cohort table.")

# ---- Industry & Region ----
with tabs[4]:
    st.markdown("<div class='section-title'>Industry & Regional Performance</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(viz.industry_treemap(df), use_container_width=True)
    with c2:
        st.plotly_chart(viz.regional_map_bar(df), use_container_width=True)

# ---- Plan Performance ----
with tabs[5]:
    st.markdown("<div class='section-title'>Plan Performance</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(viz.plan_performance_bar(df), use_container_width=True)
    with c2:
        st.plotly_chart(viz.nps_by_plan_bar(df), use_container_width=True)

# ---- Feature Adoption ----
with tabs[6]:
    st.markdown("<div class='section-title'>Feature Adoption Analytics</div>", unsafe_allow_html=True)
    st.plotly_chart(viz.feature_adoption_box(df), use_container_width=True)
    avg_adoption = df["feature_adoption_rate"].mean()
    st.markdown(
        f"<div class='insight-box'>💡 Average feature adoption across the current view is {avg_adoption:.0f}%. "
        f"Accounts below 40% adoption are strong candidates for onboarding/enablement outreach.</div>",
        unsafe_allow_html=True,
    )

# ---- Customer Intelligence ----
with tabs[7]:
    st.markdown("<div class='section-title'>Customer Intelligence</div>", unsafe_allow_html=True)

    search_id = st.text_input("🔍 Search by Customer ID (e.g. CUST-100005)")
    if search_id:
        match = df_full[df_full["customer_id"].str.contains(search_id.strip(), case=False, na=False)]
        if len(match) > 0:
            st.dataframe(match, use_container_width=True, hide_index=True)
        else:
            st.info("No matching customer ID found.")

    st.markdown("**Renewal Pipeline — Next 90 Days**")
    pipeline = renewal_pipeline(df, TODAY)
    if len(pipeline) > 0:
        st.plotly_chart(viz.renewal_pipeline_funnel(pipeline), use_container_width=True)
        st.dataframe(
            pipeline[["customer_id", "company_name", "plan", "mrr", "renewal_date", "days_to_renewal",
                      "customer_health_score", "renewal_risk_score"]].head(25),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No renewals scheduled in the next 90 days for the current filter.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**High-Risk Customer Detection**")
        risk_accounts = high_risk_customers(df)
        st.dataframe(
            risk_accounts[["customer_id", "company_name", "plan", "mrr", "renewal_risk_score", "churn_reason"]].head(15),
            use_container_width=True, hide_index=True,
        )
    with col_b:
        st.markdown("**Retention Opportunity Finder**")
        opps = retention_opportunities(df)
        st.dataframe(
            opps[["customer_id", "company_name", "plan", "mrr", "renewal_risk_score", "opportunity_score"]].head(15),
            use_container_width=True, hide_index=True,
        )

    st.download_button(
        "⬇️ Export Filtered Data to CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_subscriptions.csv",
        mime="text/csv",
    )

# ---- Executive Insights ----
with tabs[8]:
    st.markdown("<div class='section-title'>Executive Insights</div>", unsafe_allow_html=True)
    all_insights = revenue_insights(df) + churn_insights(df) + health_insights(df)

    with st.spinner("Generating executive summary..."):
        summary = generate_executive_summary(kpis, all_insights)
    st.markdown(f"<div class='insight-box' style='font-size:1rem; line-height:1.6;'>{summary}</div>", unsafe_allow_html=True)

    st.markdown("#### All Business Insights")
    for ins in all_insights:
        st.markdown(f"- {ins}")

    st.markdown("---")
    st.markdown("#### Executive Report")
    insights_bundle = {"revenue": revenue_insights(df), "churn": churn_insights(df), "health": health_insights(df)}
    report_md = generate_markdown_report(
        kpis, summary, insights_bundle, high_risk_customers(df),
        {"Region": regions, "Industry": industries, "Plan": plans, "Company Size": company_sizes},
    )
    st.download_button(
        "⬇️ Download Executive Report (Markdown)",
        data=report_md.encode("utf-8"),
        file_name="executive_report.md",
        mime="text/markdown",
    )
    with st.expander("Preview report"):
        st.markdown(report_md)

# ---- What-If Simulator ----
with tabs[9]:
    st.markdown("<div class='section-title'>What-If Revenue Simulator</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Model the MRR/ARR impact of improving churn, renewal, and upgrade rates.</div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        churn_delta = st.slider("Change in churn rate (pp)", -20.0, 20.0, -5.0, 0.5)
    with c2:
        renewal_delta = st.slider("Change in renewal rate (pp)", -20.0, 20.0, 5.0, 0.5)
    with c3:
        upgrade_rate = st.slider("Assumed upgrade rate on retained accounts (%)", 0.0, 50.0, 15.0, 1.0)

    sim = what_if_simulator(df, churn_delta, renewal_delta, upgrade_rate)
    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Current MRR", format_currency(sim["current_mrr"]))
    with c2: kpi_card("Simulated MRR", format_currency(sim["simulated_mrr"]))
    with c3:
        delta_class = "kpi-delta-positive" if sim["mrr_change"] >= 0 else "kpi-delta-negative"
        arrow = "▲" if sim["mrr_change"] >= 0 else "▼"
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-accent-bar'></div>"
            f"<div class='kpi-label'>Projected Change</div>"
            f"<div class='kpi-value'>{format_currency(sim['mrr_change'])}</div>"
            f"<div class='{delta_class}'>{arrow} {sim['mrr_change_pct']:.1f}%</div></div>",
            unsafe_allow_html=True,
        )
    st.plotly_chart(viz.what_if_comparison_bar(sim["current_mrr"], sim["simulated_mrr"]), use_container_width=True)
    st.markdown(
        f"<div class='insight-box'>💡 At a {sim['sim_churn_rate']:.1f}% churn rate and {sim['sim_renewal_rate']:.1f}% "
        f"renewal rate with {upgrade_rate:.0f}% upgrade adoption, simulated ARR reaches "
        f"{format_currency(sim['simulated_arr'])} — a {sim['mrr_change_pct']:+.1f}% change from current MRR trajectory.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    "<div style='text-align:center; color:#94A3B8; font-size:0.8rem; margin-top:30px;'>"
    "Apex Renewal Analytics · Synthetic demo dataset · Built with Streamlit &amp; Plotly</div>",
    unsafe_allow_html=True,
)