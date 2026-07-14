# Apex Renewal — SaaS Subscription Renewal & Expansion Analytics

A fintech-grade internal analytics dashboard for subscription revenue teams — renewals, churn, customer health, expansion revenue, and executive reporting, built end-to-end in Python.

---

## Overview

Subscription businesses live and die by retention. Apex Renewal is a full-stack analytics platform that answers the questions a CRO, VP of Customer Success, or RevOps lead asks every week:

- What's our MRR/ARR, and is it actually growing — or just churning and refilling?
- Are we retaining revenue (NRR/GRR), or leaking it to churn and downgrades?
- Which accounts are healthy vs. at risk, and *why*?
- Which high-value accounts should Customer Success prioritize this week?
- If we improve renewal rates or reduce churn by X points, what happens to revenue next quarter?

Rather than a single chart-on-a-CSV demo, this project covers the full analytics stack: synthetic data generation → cleaning/EDA → rule-based scoring → business KPI logic → interactive visualization → AI-generated narrative insights → downloadable executive reporting.

## Live Demo

*[Add your Streamlit Community Cloud link here once deployed]*

## Key Features

**Business KPIs**
MRR · ARR · Net Revenue Retention (NRR) · Gross Revenue Retention (GRR) · Renewal Rate · Churn Rate · Expansion Revenue · Contraction Revenue · Customer Lifetime Value (CLV) · Average Revenue per Account (ARPA) · Average Contract Value (ACV) · Revenue Leakage

**Advanced Analytics**
- Rule-based Customer Health Score (0–100) — weighted composite of usage, feature adoption, login frequency, NPS, and support ticket volume
- Renewal Risk Score (0–100) for proactive account triage
- Cohort retention heatmap — monthly signup cohorts tracked across their full lifecycle
- Renewal Pipeline (30/60/90-day view) with risk flags
- High-Risk Customer Detection and Retention Opportunity Finder
- Customer search by Customer ID
- What-If Revenue Simulator — model churn/renewal/upgrade scenarios and see the projected MRR/ARR impact instantly
- Customer segmentation by revenue tier × health band

**Reporting & AI**
- AI-generated executive summary via Groq (`llama-3.3-70b-versatile`), with an automatic rule-based fallback so the app never breaks without an API key
- Downloadable executive report (Markdown) summarizing KPIs, insights, and top at-risk accounts
- CSV export of any filtered view

**Design**
- 16+ interactive Plotly visualizations — area, waterfall bridge, donut, treemap, heatmap, funnel, bubble scatter, box plot, gauge, and more
- Custom navy / emerald / gold fintech theme with glassmorphism KPI cards, gradient header, and light/dark mode toggle
- Fully responsive filter sidebar (date range, region, industry, plan, company size)

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.10+ |
| App Framework | Streamlit |
| Data | Pandas, NumPy |
| Visualization | Plotly |
| AI Narrative | Groq API (`llama-3.3-70b-versatile`) |
| Styling | Custom CSS (glassmorphism, gradients) |

## Project Structure

```
saas-renewal-analytics/
├── app.py                  # Main Streamlit app — layout, filters, tabs
├── data_generator.py         # Synthetic subscription dataset generator
├── eda.py                     # Cleaning, cohorts, segmentation, auto-insights
├── metrics.py                  # Business KPI calculations + what-if simulator
├── visualization.py              # Themed Plotly chart library
├── utils.py                        # Formatting & filtering helpers
├── ai_insights.py                    # Groq-powered executive summary + fallback
├── report_generator.py                 # Markdown executive report builder
├── style.css                             # Navy/emerald/gold custom theme
├── requirements.txt
├── .gitignore
├── README.md
├── assets/
│   └── logo.svg                            # Apex Renewal logo
└── data/
    └── subscriptions.csv                       # Generated dataset (4,200 accounts)
```

Each module is independently testable and reusable — not a single monolithic script. `metrics.py`, `eda.py`, and `visualization.py` have zero Streamlit-specific code, so the underlying analytics logic could be reused in a notebook, a different frontend, or a scheduled report job without modification.

## How the Data Works

The dataset is synthetically generated (4,200 accounts) with realistic firmographics (industry, region, company size), usage signals (login frequency, feature adoption, NPS, support tickets), and revenue fields.

Critically, outcomes aren't randomly assigned — they're derived from a weighted rule-based health formula:

```
health_score = usage_score × 0.30
             + feature_adoption_rate × 0.25
             + login_frequency_normalized × 0.20
             + nps_normalized × 0.15
             + support_ticket_penalty × 0.10
```

Renewal outcome, churn probability, upgrade/downgrade movement, and expansion/contraction revenue are all probabilistically driven by this score. That means the relationships you'll see in the dashboard — "low health → higher churn probability", "high health → more likely to upgrade" — are internally consistent, the way a real book of business would behave, rather than independently randomized columns that happen to share a table.

Current baseline: ~68/100 average health score, ~92% renewal rate, ~8% churn rate, ~103% NRR.

## How to Run Locally

```bash
git clone https://github.com/mehak2710/saas-renewal-analytics.git
cd saas-renewal-analytics

# (recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# install dependencies
pip install -r requirements.txt

# generate the dataset (skip if data/subscriptions.csv already exists)
python data_generator.py

# run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Future Enhancements

- Persist filtered views and simulator scenarios per user session for return visits
- PDF export of the executive report (currently Markdown only, to keep Streamlit Cloud deployment lightweight)
- Cohort analysis broken out by plan tier and industry, not just signup month
- Configurable alerting (e.g. Slack/email digest) when an account crosses into the "Critical" health band
- Swap synthetic data for a real or anonymized production dataset via a pluggable data-source layer
- User authentication and role-based views (e.g. Account Manager sees only their own book)
- A/B comparison mode in the What-If Simulator to test two scenarios side by side
