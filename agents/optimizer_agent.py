def simulate_strategy(loans: list, extra_payment: float, sort_key) -> dict:
    """Simulates a repayment strategy and returns total interest paid."""
    import copy
    loans = copy.deepcopy(loans)
    loans.sort(key=sort_key)

    total_interest = 0
    months = 0
    max_months = 360

    while any(l["principal"] > 0 for l in loans) and months < max_months:
        months += 1
        extra = extra_payment

        for loan in loans:
            if loan["principal"] <= 0:
                continue
            monthly_rate = loan["interest_rate"] / 100 / 12
            interest = loan["principal"] * monthly_rate
            total_interest += interest
            principal_paid = loan["emi"] - interest
            loan["principal"] -= principal_paid

        # Apply extra payment to first active loan
        for loan in loans:
            if loan["principal"] > 0:
                loan["principal"] -= extra
                if loan["principal"] < 0:
                    loan["principal"] = 0
                break

    return {
        "total_interest": round(total_interest, 2),
        "months_to_payoff": months,
        "first_loan_to_close": loans[0]["loan_type"] if loans else "N/A"
    }


def run_optimizer_agent(profile: dict) -> dict:
    """Compares Avalanche and Snowball strategies."""
    loans = profile["loans"]
    if not loans:
        return {"recommended_method": "N/A", "avalanche": {}, "snowball": {}}

    disposable = profile["disposable_income"]
    extra = max(0, disposable * 0.3)  # use 30% of disposable as extra payment

    avalanche = simulate_strategy(
        loans, extra,
        sort_key=lambda l: -l["interest_rate"]
    )
    snowball = simulate_strategy(
        loans, extra,
        sort_key=lambda l: l["principal"]
    )

    better = "avalanche" if avalanche["total_interest"] <= snowball["total_interest"] else "snowball"
    interest_saved = abs(avalanche["total_interest"] - snowball["total_interest"])

    return {
        "recommended_method": better,
        "priority_loan": (avalanche if better == "avalanche" else snowball)["first_loan_to_close"],
        "avalanche": avalanche,
        "snowball": snowball,
        "interest_saved_by_choosing_better": round(interest_saved, 2),
        "extra_monthly_payment": round(extra, 2)
    }