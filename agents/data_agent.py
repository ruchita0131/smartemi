def run_data_agent(summary: dict) -> dict:
    """Cleans and structures raw summary data into a financial profile."""
    loans = summary.get("loans", [])
    expenses = summary.get("expenses", [])

    total_emi = sum(l["emi"] for l in loans)
    total_expenses = sum(e["amount"] for e in expenses)
    income = summary.get("monthly_income", 0)

    return {
        "monthly_income": income,
        "total_emi": total_emi,
        "total_expenses": total_expenses,
        "disposable_income": income - total_emi - total_expenses,
        "loan_count": len(loans),
        "loans": loans,
        "expenses": expenses,
        "is_valid": income > 0 and len(loans) > 0
    }