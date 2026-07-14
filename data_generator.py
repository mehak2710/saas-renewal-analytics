"""
data_generator.py
------------------
Generates a realistic synthetic SaaS subscription dataset for the
Renewal & Expansion Analytics platform.

Run directly to write data/subscriptions.csv, or import
generate_subscription_data() to get a DataFrame in-memory.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

RANDOM_SEED = 42


def _weighted_choice(rng, options, weights):
    return rng.choice(options, p=np.array(weights) / np.sum(weights))


def generate_subscription_data(n_records: int = 4000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate a synthetic B2B SaaS subscription dataset.

    Returns a pandas DataFrame with one row per customer account, containing
    firmographic, product-usage, revenue and renewal-outcome fields designed
    to look and behave like a real subscription analytics export.
    """
    rng = np.random.default_rng(seed)
    random.seed(seed)

    n = n_records

    # ---------------------------------------------------------------
    # Firmographics
    # ---------------------------------------------------------------
    industries = [
        "Fintech", "Healthcare", "E-commerce", "Manufacturing", "Education",
        "Media & Entertainment", "Logistics", "Real Estate", "SaaS/Tech",
        "Retail", "Telecom", "Professional Services",
    ]
    industry_weights = [0.14, 0.10, 0.12, 0.08, 0.07, 0.06, 0.07, 0.05, 0.15, 0.08, 0.04, 0.04]

    regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]
    region_weights = [0.38, 0.28, 0.20, 0.09, 0.05]

    country_by_region = {
        "North America": ["United States", "Canada", "Mexico"],
        "Europe": ["United Kingdom", "Germany", "France", "Netherlands", "Spain"],
        "Asia Pacific": ["India", "Singapore", "Australia", "Japan", "Indonesia"],
        "Latin America": ["Brazil", "Argentina", "Chile", "Colombia"],
        "Middle East & Africa": ["UAE", "South Africa", "Saudi Arabia", "Nigeria"],
    }

    company_sizes = ["Startup (1-50)", "SMB (51-200)", "Mid-Market (201-1000)", "Enterprise (1000+)"]
    size_weights = [0.32, 0.30, 0.24, 0.14]

    plans = ["Starter", "Growth", "Professional", "Enterprise"]
    plan_weights = [0.30, 0.32, 0.24, 0.14]
    plan_base_mrr = {"Starter": 49, "Growth": 149, "Professional": 449, "Enterprise": 1499}
    plan_mrr_spread = {"Starter": 20, "Growth": 60, "Professional": 180, "Enterprise": 900}

    account_managers = [
        "Aisha Khan", "Daniel Cho", "Priya Nair", "Marco Rossi", "Emma Wilson",
        "Liam O'Connor", "Sara Ahmed", "Wei Zhang", "Carlos Mendes", "Olivia Brooks",
    ]

    name_prefixes = ["Nova", "Apex", "Vertex", "Bright", "Cobalt", "Summit", "Orbit", "Nexus",
                      "Halo", "Quantum", "Aster", "Falcon", "Cedar", "Lumen", "Vantage", "Terra",
                      "Pulse", "Zenith", "Anchor", "Drift", "Pioneer", "Sterling", "Rivet", "Beacon"]
    name_suffixes = ["Labs", "Systems", "Works", "Group", "Technologies", "Solutions", "Networks",
                      "Partners", "Digital", "Dynamics", "Industries", "Ventures"]

    today = datetime(2026, 7, 11)

    rows = []
    for i in range(n):
        customer_id = f"CUST-{100000 + i}"
        company_name = f"{random.choice(name_prefixes)} {random.choice(name_suffixes)}"

        region = _weighted_choice(rng, regions, region_weights)
        country = random.choice(country_by_region[region])
        industry = _weighted_choice(rng, industries, industry_weights)
        company_size = _weighted_choice(rng, company_sizes, size_weights)
        plan = _weighted_choice(rng, plans, plan_weights)
        account_manager = random.choice(account_managers)

        # ------------------------------------------------------------
        # Subscription lifecycle dates
        # ------------------------------------------------------------
        tenure_days = int(rng.integers(30, 1460))  # up to ~4 years
        start_date = today - timedelta(days=tenure_days)
        contract_length_months = int(random.choice([1, 12, 12, 12, 24, 24, 36]))
        renewal_date = start_date + timedelta(days=30 * contract_length_months)
        # Push renewal dates forward so a meaningful share fall in the pipeline window
        if renewal_date < today:
            cycles_elapsed = max(1, int((today - start_date).days // (30 * contract_length_months)) + 1)
            renewal_date = start_date + timedelta(days=30 * contract_length_months * cycles_elapsed)

        # ------------------------------------------------------------
        # Revenue
        # ------------------------------------------------------------
        base = plan_base_mrr[plan]
        spread = plan_mrr_spread[plan]
        mrr = max(19, float(rng.normal(base, spread * 0.4)))
        arr = mrr * 12

        # ------------------------------------------------------------
        # Usage & engagement signals
        # ------------------------------------------------------------
        usage_score = float(np.clip(rng.normal(72, 17), 0, 100))
        login_frequency = float(np.clip(rng.normal(19, 8), 0, 60))  # logins per month
        feature_adoption_rate = float(np.clip(rng.normal(63, 20), 0, 100))
        active_users = max(1, int(rng.normal({"Startup (1-50)": 6, "SMB (51-200)": 18,
                                               "Mid-Market (201-1000)": 45,
                                               "Enterprise (1000+)": 140}[company_size], 12)))
        support_tickets = max(0, int(rng.poisson(2.2)))
        nps_score = int(np.clip(rng.normal(38, 32), -100, 100))

        # ------------------------------------------------------------
        # Health & risk scoring (rule-based, weighted composite)
        # ------------------------------------------------------------
        health_score = (
            usage_score * 0.30
            + feature_adoption_rate * 0.25
            + min(login_frequency / 30 * 100, 100) * 0.20
            + (nps_score + 100) / 2 * 0.15
            + max(0, 100 - support_tickets * 8) * 0.10
        )
        health_score = float(np.clip(health_score, 0, 100))

        risk_score = float(np.clip(100 - health_score + rng.normal(0, 8), 0, 100))

        # ------------------------------------------------------------
        # Renewal outcome (probability driven by health/risk)
        # Tuned so overall churn lands ~12-16%, in line with healthy
        # mid-market B2B SaaS benchmarks, while still varying by health.
        # ------------------------------------------------------------
        churn_prob = np.clip(0.14 - (health_score - 50) / 260, 0.02, 0.32)
        outcome_roll = rng.random()

        if outcome_roll < churn_prob:
            renewal_status = "Churned"
        elif outcome_roll < churn_prob + 0.08:
            renewal_status = "At Risk"
        elif outcome_roll < churn_prob + 0.08 + 0.06:
            renewal_status = "Pending"
        else:
            renewal_status = "Renewed"

        # Upgrade / downgrade / flat, correlated with health
        if renewal_status == "Renewed":
            up_prob = np.clip((health_score - 40) / 90, 0.12, 0.55)
            down_prob = np.clip((45 - health_score) / 180, 0.02, 0.2)
            move_roll = rng.random()
            if move_roll < up_prob:
                change_status = "Upgraded"
                expansion_revenue = float(mrr * rng.uniform(0.2, 0.65))
                contraction_revenue = 0.0
            elif move_roll < up_prob + down_prob:
                change_status = "Downgraded"
                expansion_revenue = 0.0
                contraction_revenue = float(mrr * rng.uniform(0.08, 0.3))
            else:
                change_status = "No Change"
                expansion_revenue = 0.0
                contraction_revenue = 0.0
        else:
            change_status = "No Change"
            expansion_revenue = 0.0
            contraction_revenue = 0.0

        churn_reasons_pool = [
            "Price sensitivity", "Budget cuts", "Lack of feature adoption",
            "Switched to competitor", "Poor onboarding experience",
            "Low product usage", "Support dissatisfaction", "Business closed/downsized",
            "Missing key integration", "Executive sponsor left",
        ]
        churn_reason = random.choice(churn_reasons_pool) if renewal_status in ("Churned", "At Risk") else "N/A"

        payment_status = _weighted_choice(
            rng,
            ["Current", "Overdue", "Failed Payment", "Trial"],
            [0.84, 0.08, 0.04, 0.04],
        )

        clv = float(mrr * rng.uniform(10, 40) * (1 if renewal_status != "Churned" else rng.uniform(0.3, 0.7)))

        rows.append({
            "customer_id": customer_id,
            "company_name": company_name,
            "company_size": company_size,
            "industry": industry,
            "region": region,
            "country": country,
            "plan": plan,
            "subscription_start_date": start_date.date(),
            "renewal_date": renewal_date.date(),
            "contract_length_months": contract_length_months,
            "mrr": round(mrr, 2),
            "arr": round(arr, 2),
            "usage_score": round(usage_score, 1),
            "login_frequency": round(login_frequency, 1),
            "feature_adoption_rate": round(feature_adoption_rate, 1),
            "active_users": active_users,
            "support_tickets": support_tickets,
            "nps_score": nps_score,
            "customer_health_score": round(health_score, 1),
            "renewal_risk_score": round(risk_score, 1),
            "renewal_status": renewal_status,
            "upgrade_downgrade_status": change_status,
            "expansion_revenue": round(expansion_revenue, 2),
            "contraction_revenue": round(contraction_revenue, 2),
            "churn_reason": churn_reason,
            "account_manager": account_manager,
            "customer_lifetime_value": round(clv, 2),
            "payment_status": payment_status,
        })

    df = pd.DataFrame(rows)

    # Basic cleaning guarantees: correct dtypes, no negative revenue, no dupes
    df["subscription_start_date"] = pd.to_datetime(df["subscription_start_date"])
    df["renewal_date"] = pd.to_datetime(df["renewal_date"])
    df = df.drop_duplicates(subset="customer_id").reset_index(drop=True)
    numeric_cols = ["mrr", "arr", "expansion_revenue", "contraction_revenue", "customer_lifetime_value"]
    for c in numeric_cols:
        df[c] = df[c].clip(lower=0)

    return df


if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    df = generate_subscription_data(4200)
    df.to_csv("data/subscriptions.csv", index=False)
    print(f"Generated {len(df)} records -> data/subscriptions.csv")
    print(df.head())