from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
import models

app = FastAPI(title="SmartEMI Planner API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request Models ───────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class IncomeRequest(BaseModel):
    amount: float

class ExpenseRequest(BaseModel):
    category: str
    amount: float

class LoanRequest(BaseModel):
    loan_type: str
    principal: float
    interest_rate: float
    tenure_months: int
    emi: float

# ─── Basic Routes ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "SmartEMI Planner API is running", "version": "2.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ─── Auth Routes ──────────────────────────────────────────────

@app.post("/auth/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter_by(email=data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(name=data.name, email=data.email)
    user.set_password(data.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Account created", "user_id": user.id}

@app.post("/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email=data.email).first()
    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful", "user_id": user.id, "access_token": f"user-{user.id}"}

# ─── Summary Route ────────────────────────────────────────────

@app.get("/api/users/{user_id}/summary")
def get_summary(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    income_row = db.query(models.Expense).filter_by(
        user_id=user_id, category='income'
    ).first()

    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == user_id,
        models.Expense.category != 'income'
    ).all()

    loans = db.query(models.Loan).filter_by(user_id=user_id).all()

    total_expenses = sum(e.amount for e in expenses)
    total_emi = sum(l.emi for l in loans)
    income = income_row.amount if income_row else 0.0

    return {
        "monthly_income": income,
        "total_expenses": total_expenses,
        "total_emi": total_emi,
        "disposable_income": income - total_expenses - total_emi,
        "loans": [
            {
                "id": l.id,
                "loan_type": l.loan_type,
                "principal": l.principal,
                "interest_rate": l.interest_rate,
                "tenure_months": l.tenure_months,
                "emi": l.emi
            } for l in loans
        ],
        "expenses": [
            {
                "id": e.id,
                "category": e.category,
                "amount": e.amount
            } for e in expenses
        ]
    }

# ─── Income Route ─────────────────────────────────────────────

@app.post("/api/users/{user_id}/income")
def update_income(user_id: int, data: IncomeRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    inc = db.query(models.Expense).filter_by(
        user_id=user_id, category='income'
    ).first()

    if inc:
        inc.amount = data.amount
    else:
        inc = models.Expense(user_id=user_id, category='income', amount=data.amount)
        db.add(inc)

    db.commit()
    return {"status": "ok", "amount": data.amount}

# ─── Expense Routes ───────────────────────────────────────────

@app.post("/api/users/{user_id}/expenses")
def add_expense(user_id: int, data: ExpenseRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    exp = models.Expense(
        user_id=user_id,
        category=data.category,
        amount=data.amount
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return {"status": "ok", "id": exp.id}

@app.delete("/api/users/{user_id}/expenses/{expense_id}")
def delete_expense(user_id: int, expense_id: int, db: Session = Depends(get_db)):
    exp = db.query(models.Expense).filter_by(
        id=expense_id, user_id=user_id
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(exp)
    db.commit()
    return {"status": "ok"}

# ─── Loan Routes ──────────────────────────────────────────────

@app.post("/api/users/{user_id}/loans")
def add_loan(user_id: int, data: LoanRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    loan = models.Loan(
        user_id=user_id,
        loan_type=data.loan_type,
        principal=data.principal,
        interest_rate=data.interest_rate,
        tenure_months=data.tenure_months,
        emi=data.emi
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return {"status": "ok", "id": loan.id}

@app.delete("/api/users/{user_id}/loans/{loan_id}")
def delete_loan(user_id: int, loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(models.Loan).filter_by(
        id=loan_id, user_id=user_id
    ).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    db.delete(loan)
    db.commit()
    return {"status": "ok"}

@app.get("/debug/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"id": u.id, "name": u.name, "email": u.email} for u in users]




from agents.graph import run_financial_graph

@app.get("/api/users/{user_id}/analyze")
def analyze(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build raw summary
    income_row = db.query(models.Expense).filter_by(
        user_id=user_id, category='income'
    ).first()
    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == user_id,
        models.Expense.category != 'income'
    ).all()
    loans = db.query(models.Loan).filter_by(user_id=user_id).all()

    raw_summary = {
        "monthly_income": income_row.amount if income_row else 0,
        "loans": [
            {
                "loan_type": l.loan_type,
                "principal": l.principal,
                "interest_rate": l.interest_rate,
                "tenure_months": l.tenure_months,
                "emi": l.emi
            } for l in loans
        ],
        "expenses": [
            {"category": e.category, "amount": e.amount}
            for e in expenses
        ]
    }

    # Run LangGraph pipeline
    result = run_financial_graph(raw_summary)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "profile":  result["profile"],
        "analysis": result["analysis"],
        "strategy": result["strategy"],
        "forecast": result["forecast"],
        "advice":   result["advice"]
    }



class SimulateRequest(BaseModel):
    loan_id: int
    extra_monthly_payment: float

@app.post("/api/users/{user_id}/simulate")
def simulate(user_id: int, data: SimulateRequest, db: Session = Depends(get_db)):
    loan = db.query(models.Loan).filter_by(id=data.loan_id, user_id=user_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    def calculate_payoff(principal, annual_rate, emi, extra=0):
        monthly_rate = annual_rate / 100 / 12
        balance = principal
        months = 0
        total_interest = 0

        while balance > 0 and months < 360:
            interest = balance * monthly_rate
            total_interest += interest
            payment = emi + extra
            principal_paid = payment - interest
            if principal_paid <= 0:
                break
            balance -= principal_paid
            if balance < 0:
                balance = 0
            months += 1

        return months, round(total_interest, 2)

    # Without extra payment
    original_months, original_interest = calculate_payoff(
        loan.principal, loan.interest_rate, loan.emi, 0
    )

    # With extra payment
    new_months, new_interest = calculate_payoff(
        loan.principal, loan.interest_rate, loan.emi, data.extra_monthly_payment
    )

    months_saved = original_months - new_months
    interest_saved = original_interest - new_interest

    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    today = datetime.today()

    return {
        "loan_type": loan.loan_type,
        "principal": loan.principal,
        "interest_rate": loan.interest_rate,
        "emi": loan.emi,
        "extra_payment": data.extra_monthly_payment,
        "original_months": original_months,
        "new_months": new_months,
        "months_saved": months_saved,
        "original_interest": original_interest,
        "new_interest": new_interest,
        "interest_saved": round(interest_saved, 2),
        "original_closure": (today + relativedelta(months=original_months)).strftime("%B %Y"),
        "new_closure": (today + relativedelta(months=new_months)).strftime("%B %Y"),
    }


class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/api/users/{user_id}/chat")
def chat(user_id: int, data: ChatRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's financial context
    income_row = db.query(models.Expense).filter_by(
        user_id=user_id, category='income'
    ).first()
    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == user_id,
        models.Expense.category != 'income'
    ).all()
    loans = db.query(models.Loan).filter_by(user_id=user_id).all()

    income = income_row.amount if income_row else 0
    total_emi = sum(l.emi for l in loans)
    total_expenses = sum(e.amount for e in expenses)

    loans_text = "\n".join([
        f"- {l.loan_type.title()} Loan: ₹{l.principal:,.0f} @ {l.interest_rate}% | EMI: ₹{l.emi:,.0f}"
        for l in loans
    ]) or "No loans"

    # Build context-aware system prompt
    system_context = f"""You are SmartEMI, a friendly AI financial advisor.
You have full access to this user's financial data:

Monthly Income: ₹{income:,.0f}
Total EMI: ₹{total_emi:,.0f}
Total Expenses: ₹{total_expenses:,.0f}
Disposable Income: ₹{income - total_emi - total_expenses:,.0f}

Loans:
{loans_text}

Answer questions about their finances clearly and specifically.
Use their actual numbers. Be concise — max 3 sentences per response.
If asked something unrelated to finance, politely redirect."""

    # Build conversation
    from google import genai as google_genai
    import os

    client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Format history + new message
    conversation = ""
    for msg in data.history[-6:]:  # last 6 messages for context
        role = "User" if msg["role"] == "user" else "SmartEMI"
        conversation += f"{role}: {msg['content']}\n"
    conversation += f"User: {data.message}\nSmartEMI:"

    full_prompt = system_context + "\n\n" + conversation

    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=full_prompt
    )

    return {"reply": response.text.strip()}


@app.get("/api/users/{user_id}/profile")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.name, "email": user.email}


