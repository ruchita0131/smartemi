def run_analysis_agent(profile: dict) -> dict:
    """Calculates DTI ratio and a financial health score out of 100."""
    income = profile["monthly_income"]
    total_emi = profile["total_emi"]
    total_expenses = profile["total_expenses"]
    disposable = profile["disposable_income"]

    dti = (total_emi / income * 100) if income > 0 else 100
    expense_ratio = ((total_expenses + total_emi) / income * 100) if income > 0 else 100

    # Score starts at 100 and gets deducted
    score = 100
    if dti > 50: score -= 40
    elif dti > 40: score -= 25
    elif dti > 30: score -= 10

    if expense_ratio > 80: score -= 30
    elif expense_ratio > 60: score -= 15

    if disposable < 0: score -= 20

    score = max(0, min(100, score))

    if score >= 75: health_label = "Excellent"
    elif score >= 50: health_label = "Moderate"
    elif score >= 25: health_label = "Poor"
    else: health_label = "Critical"

    return {
        "dti_ratio": round(dti, 1),
        "expense_ratio": round(expense_ratio, 1),
        "health_score": score,
        "health_label": health_label,
        "monthly_surplus": disposable
    }