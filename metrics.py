"""
metrics.py
----------
Core business KPI calculations for the subscription analytics platform.
Every function takes a (filtered) DataFrame and returns a plain number,
so they can be reused for the full dataset, filtered slices, or the
what-if simulator.
"""

import pandas as pd
import numpy as np


def total_mrr(df: pd.DataFrame) -> float:
    active = df[df["renewal_status"] != "Churned"]
    return float(active["mrr"].sum())


def total_arr(df: pd.DataFrame) -> float:
    return total_mrr(df) * 12


def renewal_rate(df: pd.DataFrame) -> float:
    decided = df[df["renewal_status"].isin(["Renewed", "Churned"])]
    if len(decided) == 0:
        return 0.0
    return float((decided["renewal_status"] == "Renewed").mean() * 100)


def churn_rate(df: pd.DataFrame) -> float:
    decided = df[df["renewal_status"].isin(["Renewed", "Churned"])]
    if len(decided) == 0:
        return 0.0
    return float((decided["renewal_status"] == "Churned").mean() * 100)


def gross_revenue_retention(df: pd.DataFrame) -> float:
    """GRR = (Starting MRR - Churned MRR - Contraction MRR) / Starting MRR, capped at 100%."""
    starting_mrr = df["mrr"].sum()
    if starting_mrr == 0:
        return 0.0
    churned_mrr = df.loc[df["renewal_status"] == "Churned", "mrr"].sum()
    contraction = df["contraction_revenue"].sum()
    grr = (starting_mrr - churned_mrr - contraction) / starting_mrr * 100
    return float(np.clip(grr, 0, 100))


def net_revenue_retention(df: pd.DataFrame) -> float:
    """NRR = (Starting MRR - Churned MRR - Contraction MRR + Expansion MRR) / Starting MRR."""
    starting_mrr = df["mrr"].sum()
    if starting_mrr == 0:
        return 0.0
    churned_mrr = df.loc[df["renewal_status"] == "Churned", "mrr"].sum()
    contraction = df["contraction_revenue"].sum()
    expansion = df["expansion_revenue"].sum()
    nrr = (starting_mrr - churned_mrr - contraction + expansion) / starting_mrr * 100
    return float(nrr)


def total_expansion_revenue(df: pd.DataFrame) -> float:
    return float(df["expansion_revenue"].sum())


def total_contraction_revenue(df: pd.DataFrame) -> float:
    return float(df["contraction_revenue"].sum())


def avg_clv(df: pd.DataFrame) -> float:
    if len(df) == 0:
        return 0.0
    return float(df["customer_lifetime_value"].mean())


def arpa(df: pd.DataFrame) -> float:
    """Average Revenue Per Account (monthly)."""
    active = df[df["renewal_status"] != "Churned"]
    if len(active) == 0:
        return 0.0
    return float(active["mrr"].mean())


def acv(df: pd.DataFrame) -> float:
    """Average Contract Value = ARR-equivalent value per account, annualized."""
    active = df[df["renewal_status"] != "Churned"]
    if len(active) == 0:
        return 0.0
    return float((active["mrr"] * 12).mean())


def avg_customer_health(df: pd.DataFrame) -> float:
    if len(df) == 0:
        return 0.0
    return float(df["customer_health_score"].mean())


def avg_renewal_risk(df: pd.DataFrame) -> float:
    if len(df) == 0:
        return 0.0
    return float(df["renewal_risk_score"].mean())


def revenue_leakage(df: pd.DataFrame) -> float:
    """Revenue lost from churn + contraction (monthly)."""
    churned_mrr = df.loc[df["renewal_status"] == "Churned", "mrr"].sum()
    contraction = df["contraction_revenue"].sum()
    return float(churned_mrr + contraction)


def kpi_summary(df: pd.DataFrame) -> dict:
    """Convenience bundle used to populate the executive KPI cards."""
    return {
        "mrr": total_mrr(df),
        "arr": total_arr(df),
        "nrr": net_revenue_retention(df),
        "grr": gross_revenue_retention(df),
        "churn_rate": churn_rate(df),
        "renewal_rate": renewal_rate(df),
        "customer_health": avg_customer_health(df),
        "expansion_revenue": total_expansion_revenue(df),
        "contraction_revenue": total_contraction_revenue(df),
        "clv": avg_clv(df),
        "arpa": arpa(df),
        "acv": acv(df),
        "revenue_leakage": revenue_leakage(df),
        "customer_count": int(len(df)),
    }


def what_if_simulator(df: pd.DataFrame, churn_delta: float, renewal_delta: float,
                       upgrade_rate: float) -> dict:
    """Simulate the revenue impact of changing churn, renewal, and upgrade rates.

    churn_delta: percentage point change to churn rate (e.g. -5 = reduce churn by 5pp)
    renewal_delta: percentage point change to renewal rate
    upgrade_rate: assumed % of renewed accounts that upgrade, with a 25% MRR bump

    Returns a dict comparing current vs simulated MRR/ARR/NRR.
    """
    current_mrr = total_mrr(df)
    current_churn = churn_rate(df)
    current_renewal = renewal_rate(df)

    sim_churn = float(np.clip(current_churn + churn_delta, 0, 100))
    sim_renewal = float(np.clip(current_renewal + renewal_delta, 0, 100))

    active = df[df["renewal_status"] != "Churned"]
    at_stake_mrr = df.loc[df["renewal_status"].isin(["Renewed", "Churned", "At Risk", "Pending"]), "mrr"].sum()

    # Revenue retained under new churn assumption
    retained_mrr = at_stake_mrr * (1 - sim_churn / 100)
    # Upgrade uplift applied to the retained base
    upgrade_uplift = retained_mrr * (upgrade_rate / 100) * 0.25

    simulated_mrr = retained_mrr + upgrade_uplift
    simulated_arr = simulated_mrr * 12

    mrr_change = simulated_mrr - current_mrr
    mrr_change_pct = (mrr_change / current_mrr * 100) if current_mrr else 0.0

    return {
        "current_mrr": current_mrr,
        "current_arr": current_mrr * 12,
        "simulated_mrr": simulated_mrr,
        "simulated_arr": simulated_arr,
        "mrr_change": mrr_change,
        "mrr_change_pct": mrr_change_pct,
        "sim_churn_rate": sim_churn,
        "sim_renewal_rate": sim_renewal,
        "upgrade_uplift": upgrade_uplift,
    }