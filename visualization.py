"""
visualization.py
-----------------
Reusable Plotly chart builders, themed for the Navy / Emerald / Gold
fintech dashboard palette. Every function returns a go.Figure so the
app layer just calls st.plotly_chart(fig, use_container_width=True).
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------
NAVY = "#0B1E3D"
NAVY_LIGHT = "#16305C"
EMERALD = "#10B981"
GOLD = "#F5B700"
GRAY_BG = "#F4F6F9"
RED = "#DC2626"
ORANGE = "#F97316"
BLUE = "#3B82F6"
PURPLE = "#8B5CF6"

CATEGORICAL_PALETTE = [NAVY_LIGHT, EMERALD, GOLD, BLUE, PURPLE, ORANGE, RED, "#14B8A6"]

STATUS_COLORS = {
    "Renewed": EMERALD,
    "Churned": RED,
    "At Risk": ORANGE,
    "Pending": GOLD,
    "Upgraded": EMERALD,
    "Downgraded": RED,
    "No Change": "#94A3B8",
}


def _base_layout(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=NAVY, family="Inter, Segoe UI, sans-serif")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color="#334155", size=12),
        margin=dict(l=30, r=20, t=64 if title else 20, b=30),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.10, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#E5E9F0", zeroline=False)
    return fig


def mrr_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Area chart of MRR by month based on subscription start date."""
    data = df.copy()
    data["month"] = data["subscription_start_date"].dt.to_period("M").astype(str)
    monthly = data.groupby("month")["mrr"].sum().reset_index().sort_values("month")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["mrr"], mode="lines", fill="tozeroy",
        line=dict(color=EMERALD, width=2.5), fillcolor="rgba(16,185,129,0.15)", name="MRR",
    ))
    return _base_layout(fig, "MRR Growth Over Time")


def renewal_status_donut(df: pd.DataFrame) -> go.Figure:
    counts = df["renewal_status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    colors = [STATUS_COLORS.get(s, "#94A3B8") for s in counts["status"]]
    fig = go.Figure(data=[go.Pie(
        labels=counts["status"], values=counts["count"], hole=0.55,
        marker=dict(colors=colors), textinfo="label+percent",
    )])
    fig = _base_layout(fig, "Renewal Status Breakdown", height=420)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=60),
    )
    return fig


def revenue_bridge_chart(df: pd.DataFrame) -> go.Figure:
    """Waterfall showing MRR bridge: starting -> churn -> contraction -> expansion -> ending."""
    starting = df["mrr"].sum()
    churn_loss = -df.loc[df["renewal_status"] == "Churned", "mrr"].sum()
    contraction = -df["contraction_revenue"].sum()
    expansion = df["expansion_revenue"].sum()
    ending = starting + churn_loss + contraction + expansion

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Starting MRR", "Churn", "Contraction", "Expansion", "Ending MRR"],
        y=[starting, churn_loss, contraction, expansion, ending],
        connector=dict(line=dict(color="#CBD5E1")),
        decreasing=dict(marker=dict(color=RED)),
        increasing=dict(marker=dict(color=EMERALD)),
        totals=dict(marker=dict(color=NAVY_LIGHT)),
    ))
    return _base_layout(fig, "Revenue Bridge (MRR Movement)")


def plan_performance_bar(df: pd.DataFrame) -> go.Figure:
    grouped = df.groupby("plan").agg(mrr=("mrr", "sum"), customers=("customer_id", "count")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=grouped["plan"], y=grouped["mrr"], marker_color=EMERALD, name="MRR"))
    return _base_layout(fig, "MRR by Plan")


def industry_treemap(df: pd.DataFrame) -> go.Figure:
    grouped = df.groupby("industry")["mrr"].sum().reset_index()
    fig = px.treemap(
        grouped, path=["industry"], values="mrr",
        color="mrr", color_continuous_scale=["#0B1E3D", "#16305C", "#10B981"],
    )
    fig.update_traces(textinfo="label+value")
    return _base_layout(fig, "Revenue Concentration by Industry", height=420)


def regional_map_bar(df: pd.DataFrame) -> go.Figure:
    grouped = df.groupby("region").agg(mrr=("mrr", "sum"), customers=("customer_id", "count")).reset_index()
    grouped = grouped.sort_values("mrr", ascending=True)
    fig = go.Figure(go.Bar(
        x=grouped["mrr"], y=grouped["region"], orientation="h",
        marker_color=NAVY_LIGHT, text=grouped["customers"], texttemplate="%{text} accts",
        textposition="outside",
    ))
    return _base_layout(fig, "MRR by Region")


def health_distribution_histogram(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(df, x="customer_health_score", nbins=25, color_discrete_sequence=[EMERALD])
    return _base_layout(fig, "Customer Health Score Distribution")


def risk_vs_mrr_scatter(df: pd.DataFrame) -> go.Figure:
    sample = df.sample(min(len(df), 1200), random_state=1)
    fig = px.scatter(
        sample, x="renewal_risk_score", y="mrr", color="renewal_status",
        color_discrete_map=STATUS_COLORS, size="customer_lifetime_value",
        size_max=18, opacity=0.7, hover_data=["company_name", "industry"],
    )
    fig = _base_layout(fig, "Renewal Risk vs. MRR (bubble size = CLV)", height=480)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5, title=None),
        margin=dict(l=30, r=20, t=60, b=70),
    )
    return fig


def health_gauge(score: float) -> go.Figure:
    color = EMERALD if score >= 75 else GOLD if score >= 50 else ORANGE if score >= 30 else RED
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(suffix="", font=dict(size=36, color=NAVY)),
        domain=dict(x=[0.08, 0.92], y=[0.05, 0.95]),
        gauge=dict(
            axis=dict(range=[0, 100]),
            bar=dict(color=color),
            steps=[
                dict(range=[0, 30], color="#FEE2E2"),
                dict(range=[30, 50], color="#FFEDD5"),
                dict(range=[50, 75], color="#FEF9C3"),
                dict(range=[75, 100], color="#D1FAE5"),
            ],
        ),
    ))
    fig = _base_layout(fig, "Average Customer Health", height=280)
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=20))
    return fig


def feature_adoption_box(df: pd.DataFrame) -> go.Figure:
    fig = px.box(df, x="plan", y="feature_adoption_rate", color="plan",
                 color_discrete_sequence=CATEGORICAL_PALETTE)
    fig.update_layout(showlegend=False)
    return _base_layout(fig, "Feature Adoption Rate by Plan")


def cohort_heatmap(cohort_table: pd.DataFrame) -> go.Figure:
    z = cohort_table.values
    text = np.where(
        np.isnan(z), "",
        np.vectorize(lambda v: f"{v:.0f}%" if not np.isnan(v) else "")(z),
    )
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=[f"Month {c}" for c in cohort_table.columns],
        y=cohort_table.index,
        colorscale=[[0, "#FEE2E2"], [0.5, "#FEF9C3"], [1, "#10B981"]],
        text=text,
        texttemplate="%{text}",
        hoverongaps=False,
        xgap=2,
        ygap=2,
    ))
    return _base_layout(fig, "Cohort Retention Heatmap (% retained by month since start)", height=420)


def renewal_pipeline_funnel(pipeline_df: pd.DataFrame) -> go.Figure:
    counts = pipeline_df["window"].value_counts().reindex(["Next 30 days", "31-60 days", "61-90 days"]).fillna(0)
    fig = go.Figure(go.Funnel(
        y=counts.index, x=counts.values,
        marker=dict(color=[EMERALD, GOLD, ORANGE]),
    ))
    return _base_layout(fig, "Renewal Pipeline (Next 90 Days)")


def churn_reason_bar(df: pd.DataFrame) -> go.Figure:
    churned = df[df["renewal_status"] == "Churned"]
    if len(churned) == 0:
        fig = go.Figure()
        return _base_layout(fig, "Churn Reasons (no churned accounts in view)")
    counts = churned["churn_reason"].value_counts().reset_index()
    counts.columns = ["reason", "count"]
    counts = counts.sort_values("count")
    fig = go.Figure(go.Bar(x=counts["count"], y=counts["reason"], orientation="h", marker_color=RED))
    return _base_layout(fig, "Top Churn Reasons", height=420)


def segment_stacked_bar(df: pd.DataFrame) -> go.Figure:
    grouped = df.groupby(["industry", "health_segment"]).size().reset_index(name="count")
    fig = px.bar(
        grouped, x="industry", y="count", color="health_segment",
        color_discrete_map={"Healthy": EMERALD, "Neutral": GOLD, "At Risk": ORANGE, "Critical": RED},
        barmode="stack",
    )
    fig.update_xaxes(tickangle=-30)
    fig = _base_layout(fig, "Customer Health Segments by Industry", height=460)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.35, xanchor="center", x=0.5, title=None),
        margin=dict(l=30, r=20, t=60, b=110),
    )
    return fig


def nps_by_plan_bar(df: pd.DataFrame) -> go.Figure:
    grouped = df.groupby("plan")["nps_score"].mean().reset_index()
    fig = go.Figure(go.Bar(x=grouped["plan"], y=grouped["nps_score"], marker_color=GOLD))
    return _base_layout(fig, "Average NPS by Plan")


def what_if_comparison_bar(current_mrr: float, simulated_mrr: float) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=["Current MRR", "Simulated MRR"], y=[current_mrr, simulated_mrr],
        marker_color=[NAVY_LIGHT, EMERALD],
        text=[f"${current_mrr:,.0f}", f"${simulated_mrr:,.0f}"], textposition="outside",
    ))
    return _base_layout(fig, "What-If Impact on MRR", height=340)