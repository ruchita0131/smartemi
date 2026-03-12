import os
import anthropic

def run_advisor_agent(profile: dict, analysis: dict, strategy: dict, forecast: dict) -> str:
    """Calls Claude API with full financial context to generate personalized advice."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    loans_text = "\n".join([
        f"  - {l['loan_type'].title()} Loan: ₹{l['principal']:,.0f} @ {l['interest_rate']}% | EMI: ₹{l['emi']:,.0f}"
        for l in profile["loans"]
    ])

    forecast_text = "\n".join([
        f"  - {p['loan_type'].title()} Loan closes {p['closure_date']} (₹{p['total_interest_remaining']:,.0f} interest remaining)"
        for p in forecast.get("projections", [])
    ])

    prompt = f"""You are SmartEMI Advisor, an expert Indian personal finance AI.
Analyze this user's complete financial situation and give specific, actionable advice.
Be direct, use their actual numbers, and keep it practical.

FINANCIAL PROFILE:
- Monthly Income: ₹{profile['monthly_income']:,.0f}
- Total EMI: ₹{profile['total_emi']:,.0f}
- Total Expenses: ₹{profile['total_expenses']:,.0f}
- Disposable Income: ₹{profile['disposable_income']:,.0f}
- Debt-to-Income Ratio: {analysis['dti_ratio']}%
- Financial Health Score: {analysis['health_score']}/100 ({analysis['health_label']})

LOANS:
{loans_text}

LOAN PROJECTIONS:
{forecast_text}

OPTIMIZER RECOMMENDATION:
- Best strategy: {strategy.get('recommended_method', 'N/A').title()} method
- First loan to attack: {strategy.get('priority_loan', 'N/A').title()} Loan
- Extra monthly payment suggested: ₹{strategy.get('extra_monthly_payment', 0):,.0f}
- Interest saved vs other strategy: ₹{strategy.get('interest_saved_by_choosing_better', 0):,.0f}

Provide:
1. A clear 2-line assessment of their financial health
2. Top 3 specific actions they should take THIS month with exact rupee amounts
3. One motivating insight about their debt-free timeline

Keep response under 250 words. Use simple language."""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text