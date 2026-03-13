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


from agents.data_agent import run_data_agent
from agents.analysis_agent import run_analysis_agent
from agents.optimizer_agent import run_optimizer_agent
from agents.forecast_agent import run_forecast_agent
from agents.advisor_agent import run_advisor_agent

@app.get("/api/users/{user_id}/analyze")
def analyze(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get raw summary
    income_row = db.query(models.Expense).filter_by(user_id=user_id, category='income').first()
    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == user_id,
        models.Expense.category != 'income'
    ).all()
    loans = db.query(models.Loan).filter_by(user_id=user_id).all()

    summary = {
        "monthly_income": income_row.amount if income_row else 0,
        "loans": [{"loan_type": l.loan_type, "principal": l.principal,
                   "interest_rate": l.interest_rate, "tenure_months": l.tenure_months,
                   "emi": l.emi} for l in loans],
        "expenses": [{"category": e.category, "amount": e.amount} for e in expenses]
    }

    # Run the 5 agents in sequence
    profile  = run_data_agent(summary)
    analysis = run_analysis_agent(profile)
    strategy = run_optimizer_agent(profile)
    forecast = run_forecast_agent(profile)
    advice   = run_advisor_agent(profile, analysis, strategy, forecast)

    return {
        "profile":  profile,
        "analysis": analysis,
        "strategy": strategy,
        "forecast": forecast,
        "advice":   advice
    }

import os

@app.get("/debug/env")
def check_env():
    key = os.getenv("ANTHROPIC_API_KEY", "NOT SET")
    return {"key_set": key != "NOT SET", "key_preview": key[:15] + "..." if key != "NOT SET" else "NOT SET"}