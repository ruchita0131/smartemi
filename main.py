from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models  # triggers table creation on startup

app = FastAPI(title="SmartEMI Planner API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this after frontend is deployed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "SmartEMI Planner API is running", "version": "2.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

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

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/")
def root():
    return {"message": "SmartEMI Planner API is running", "version": "2.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

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

@app.get("/api/users/{user_id}/summary")
def get_summary(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    income_row = db.query(models.Expense).filter_by(user_id=user_id, category='income').first()
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
        "loans": [{"id": l.id, "loan_type": l.loan_type, "principal": l.principal,
                   "interest_rate": l.interest_rate, "tenure_months": l.tenure_months,
                   "emi": l.emi} for l in loans],
        "expenses": [{"id": e.id, "category": e.category, "amount": e.amount} for e in expenses]
    }