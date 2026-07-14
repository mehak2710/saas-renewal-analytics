"""
ai_insights.py
--------------
Generates an executive narrative summary using the Groq API when a key
is available (via .env or Streamlit secrets), and falls back to a
clean rule-based summary otherwise so the app never breaks in a demo
or when deployed without a key configured.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GROQ_MODEL = "llama-3.3-70b-versatile"


def _get_groq_key() -> str | None:
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key

    # Only touch st.secrets if a secrets.toml actually exists. Streamlit
    # renders its own "No secrets found" warning banner the moment
    # st.secrets is accessed at all when no file is present -- even inside
    # a try/except -- so for local .env-based setups we skip it entirely.
    secrets_paths = [
        os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml"),
        os.path.join(os.getcwd(), ".streamlit", "secrets.toml"),
    ]
    if not any(os.path.exists(p) for p in secrets_paths):
        return None

    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY")
    except Exception:
        return None


def _rule_based_summary(kpis: dict, insights: list) -> str:
    """Deterministic fallback narrative built from KPI dict + insight bullets."""
    lines = []
    lines.append(
        f"The business currently manages ${kpis['mrr']:,.0f} in MRR (${kpis['arr']:,.0f} ARR) "
        f"across {kpis['customer_count']:,} accounts."
    )
    if kpis["nrr"] >= 100:
        lines.append(
            f"Net Revenue Retention stands at {kpis['nrr']:.1f}%, meaning the existing customer "
            f"base is expanding faster than it's shrinking — a strong signal for durable growth."
        )
    else:
        lines.append(
            f"Net Revenue Retention is {kpis['nrr']:.1f}%, below the 100% benchmark, indicating "
            f"churn and downgrades currently outweigh expansion — this warrants retention focus."
        )
    lines.append(
        f"Renewal rate is {kpis['renewal_rate']:.1f}% against a churn rate of {kpis['churn_rate']:.1f}%, "
        f"with average customer health at {kpis['customer_health']:.0f}/100."
    )
    lines.append(
        f"Expansion revenue of ${kpis['expansion_revenue']:,.0f} is being offset by ${kpis['contraction_revenue']:,.0f} "
        f"in contraction, for net revenue leakage of ${kpis['revenue_leakage']:,.0f} this period."
    )
    if insights:
        lines.append("Key observations: " + " ".join(insights[:4]))
    lines.append(
        "Recommended focus: prioritize outreach to high-MRR, at-risk accounts identified in the "
        "Retention Opportunity Finder, and review churn reasons concentrated in the weakest segments."
    )
    return "\n\n".join(lines)


def generate_executive_summary(kpis: dict, insights: list) -> str:
    """Return an executive summary string, using Groq if configured, else a
    rule-based fallback. Never raises — always returns usable text."""
    api_key = _get_groq_key()
    if not api_key:
        return _rule_based_summary(kpis, insights)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        prompt = f"""You are a SaaS revenue operations analyst. Write a concise, confident
executive summary (4-6 sentences, plain prose, no headers or bullet points) for a subscription
renewal & expansion analytics dashboard, based on this data:

KPIs: {kpis}
Key observations: {insights}

Focus on renewal health, revenue retention (NRR/GRR), expansion vs contraction, and one clear
actionable recommendation. Write for a CRO/VP of Customer Success audience."""

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=400,
        )
        text = response.choices[0].message.content.strip()
        return text if text else _rule_based_summary(kpis, insights)
    except Exception:
        # Any API/network/library issue -> silently fall back, never break the app
        return _rule_based_summary(kpis, insights)