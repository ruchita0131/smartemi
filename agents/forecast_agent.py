def run_forecast_agent(profile: dict) -> dict:
    """Projects closure date and total interest for each loan."""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    projections = []
    today = datetime.today()

    for loan in profile["loans"]:
        principal = loan["principal"]
        monthly_rate = loan["interest_rate"] / 100 / 12
        emi = loan["emi"]

        if emi <= 0 or principal <= 0:
            continue

        months = 0
        total_interest = 0
        balance = principal

        while balance > 0 and months < 360:
            interest = balance * monthly_rate
            total_interest += interest
            principal_paid = emi - interest
            if principal_paid <= 0:
                break
            balance -= principal_paid
            months += 1

        closure_date = today + relativedelta(months=months)

        projections.append({
            "loan_type": loan["loan_type"],
            "months_remaining": months,
            "closure_date": closure_date.strftime("%B %Y"),
            "total_interest_remaining": round(total_interest, 2),
            "total_amount_remaining": round(principal + total_interest, 2)
        })

    return {"projections": projections}