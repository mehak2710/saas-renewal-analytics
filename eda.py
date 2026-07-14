"""
eda.py
------
Exploratory data analysis helpers: cleaning, cohort construction,
segmentation and auto-generated plain-English insights that get
attached under each analytics section in the app.
"""

import pandas as pd
import numpy as np
from utils import health_bucket, risk_bucket


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Defensive cleaning pass — safe to call even on already-clean data."""
    out = df.copy()
    out = out.drop_duplicates(subset="customer_id")
    out["subscription_start_date"] = pd.to_datetime(out["subscription_start_date"], errors="coerce")
    out["renewal_date"] = pd.to_datetime(out["renewal_date"], errors="coerce")
    out = out.dropna(subset=["customer_id", "mrr", "renewal_status"])
    numeric_cols = ["mrr", "arr", "customer_health_score", "renewal_risk_score",
                     "expansion_revenue", "contraction_revenue", "customer_lifetime_value"]
    for c in numeric_cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0).clip(lower=0)
    out["health_segment"] = out["customer_health_score"].apply(health_bucket)
    out["risk_segment"] = out["renewal_risk_score"].apply(risk_bucket)
    return out.reset_index(drop=True)


def cohort_retention_table(df: pd.DataFrame) -> pd.DataFrame:
    """Build a monthly-cohort retention matrix based on subscription_start_date.

    Each customer only gives us one observed data point (their status at their
    current renewal age), not a full monthly history. To avoid a sparse table
    full of nulls, we reconstruct the trajectory: a customer known to be
    retained at age N was necessarily active at every age before N too, and a
    churned customer is treated as retained up to age N-1 and churned at N.
    Ages beyond what any cohort has had time to reach are left as true NaN
    (nothing to report yet), which the heatmap renders as blank cells.
    """
    data = df.copy()
    data["cohort_month"] = data["subscription_start_date"].dt.to_period("M")
    data["age_months"] = (
        (data["renewal_date"].dt.year - data["subscription_start_date"].dt.year) * 12
        + (data["renewal_date"].dt.month - data["subscription_start_date"].dt.month)
    ).clip(lower=0)
    data["is_retained_final"] = (data["renewal_status"] != "Churned").astype(int)

    records = []
    for cohort, age, retained in zip(data["cohort_month"], data["age_months"], data["is_retained_final"]):
        for m in range(0, int(age)):
            records.append((cohort, m, 1))  # active at every age before the observed point
        records.append((cohort, int(age), retained))  # actual outcome at observed age

    exploded = pd.DataFrame(records, columns=["cohort_month", "age_months", "retained"])
    table = (
        exploded.groupby(["cohort_month", "age_months"])["retained"]
        .mean()
        .reset_index()
    )
    pivot = table.pivot(index="cohort_month", columns="age_months", values="retained")
    pivot = pivot.sort_index()
    pivot.index = pivot.index.astype(str)
    return (pivot * 100).round(1)


def renewal_pipeline(df: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Accounts renewing in the next 30/60/90 days, with risk flagged."""
    upcoming = df[(df["renewal_date"] >= today) & (df["renewal_date"] <= today + pd.Timedelta(days=90))].copy()
    upcoming["days_to_renewal"] = (upcoming["renewal_date"] - today).dt.days
    bins = [0, 30, 60, 90]
    labels = ["Next 30 days", "31-60 days", "61-90 days"]
    upcoming["window"] = pd.cut(upcoming["days_to_renewal"], bins=[-1, 30, 60, 90], labels=labels)
    return upcoming.sort_values("days_to_renewal")


def high_risk_customers(df: pd.DataFrame, threshold: float = 65) -> pd.DataFrame:
    return df[df["renewal_risk_score"] >= threshold].sort_values("renewal_risk_score", ascending=False)


def retention_opportunities(df: pd.DataFrame) -> pd.DataFrame:
    """Accounts with high MRR but declining health signals — best targets for
    proactive retention outreach (high revenue at stake, still salvageable)."""
    candidates = df[
        (df["renewal_risk_score"] >= 45) & (df["renewal_risk_score"] < 75) & (df["mrr"] >= df["mrr"].median())
    ].copy()
    candidates["opportunity_score"] = (candidates["mrr"] * candidates["renewal_risk_score"] / 100)
    return candidates.sort_values("opportunity_score", ascending=False)


def segment_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Simple rule-based segmentation combining revenue tier and health."""
    data = df.copy()
    revenue_tier = pd.qcut(data["mrr"], q=3, labels=["Low Value", "Mid Value", "High Value"], duplicates="drop")
    data["revenue_tier"] = revenue_tier
    data["segment"] = data["revenue_tier"].astype(str) + " / " + data["health_segment"]
    return data


# ---------------------------------------------------------------------
# Auto-generated business insights (plain-English, rule-based)
# ---------------------------------------------------------------------

def revenue_insights(df: pd.DataFrame) -> list:
    from metrics import total_mrr, net_revenue_retention, total_expansion_revenue, total_contraction_revenue
    insights = []
    nrr = net_revenue_retention(df)
    if nrr >= 110:
        insights.append(f"NRR is {nrr:.1f}%, indicating strong expansion revenue is outpacing churn and contraction — a healthy growth signal.")
    elif nrr >= 100:
        insights.append(f"NRR is {nrr:.1f}%, right around the break-even point; expansion is roughly offsetting losses from churn.")
    else:
        insights.append(f"NRR is {nrr:.1f}%, below 100% — churn and contraction are currently outpacing expansion revenue.")

    exp = total_expansion_revenue(df)
    con = total_contraction_revenue(df)
    if exp > con * 1.5:
        insights.append(f"Expansion revenue (${exp:,.0f}) significantly exceeds contraction (${con:,.0f}), suggesting upsell motion is working.")
    elif con > exp:
        insights.append(f"Contraction revenue (${con:,.0f}) exceeds expansion (${exp:,.0f}) — worth investigating downgrade drivers by plan/industry.")
    return insights


def churn_insights(df: pd.DataFrame) -> list:
    insights = []
    churned = df[df["renewal_status"] == "Churned"]
    if len(churned) == 0:
        return ["No churned accounts in the current filtered view."]
    top_reason = churned["churn_reason"].value_counts().idxmax()
    top_reason_pct = churned["churn_reason"].value_counts(normalize=True).max() * 100
    insights.append(f"'{top_reason}' is the leading churn driver, accounting for {top_reason_pct:.0f}% of churned accounts.")

    top_industry = churned["industry"].value_counts().idxmax()
    insights.append(f"{top_industry} shows the highest concentration of churned accounts among current filters.")

    avg_health_churned = churned["customer_health_score"].mean()
    insights.append(f"Churned accounts had an average health score of {avg_health_churned:.0f}/100 prior to churn, versus the overall book average.")
    return insights


def health_insights(df: pd.DataFrame) -> list:
    insights = []
    healthy_pct = (df["customer_health_score"] >= 75).mean() * 100
    critical_pct = (df["customer_health_score"] < 30).mean() * 100
    insights.append(f"{healthy_pct:.0f}% of accounts are in the 'Healthy' band (score 75+), while {critical_pct:.0f}% are 'Critical' (score below 30).")
    corr = df["customer_health_score"].corr(df["mrr"])
    if abs(corr) > 0.1:
        direction = "positively" if corr > 0 else "negatively"
        insights.append(f"Customer health score is {direction} correlated with MRR (r={corr:.2f}), relevant for prioritizing retention spend.")
    return insights