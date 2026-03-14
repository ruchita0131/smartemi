# SmartEMI Planner — Backend API

An agentic AI system for personal loan optimization, built with FastAPI and LangGraph.

## Live Links

- API: https://smartemi-api.onrender.com
- API Documentation: https://smartemi-api.onrender.com/docs
- Frontend: https://smartemi-frontend.vercel.app

## Demo Account

| Field    | Value             |
|----------|-------------------|
| Email    | demo@smartemi.in  |
| Password | demo1234          |

---

## Agent Architecture

This project uses LangGraph to orchestrate a 5-node StateGraph. Each agent has a single responsibility, and typed state flows between them via a FinancialState TypedDict.
```
START
  |
  v
[Data Agent]
Validates and structures raw financial input.
Calculates total EMI, expenses, and disposable income.
  |
  v  (conditional edge — pipeline stops if data is invalid)
[Analysis Agent]
Calculates Debt-to-Income ratio and a financial health score (0-100).
Labels: Excellent / Moderate / Poor / Critical
  |
  v
[Optimizer Agent]
Simulates two repayment strategies in parallel.
Avalanche: highest interest rate first (mathematically optimal).
Snowball: lowest balance first (psychologically motivating).
Returns the better strategy for this user's specific numbers.
  |
  v
[Forecast Agent]
Runs month-by-month amortization for each loan.
Projects exact closure date and total interest remaining.
  |
  v
[Advisor Agent]
Calls Google Gemini with the complete financial profile.
Generates personalized advice with exact rupee amounts.
  |
  v
END
```

### Why LangGraph

- Typed state via FinancialState TypedDict ensures data integrity between agents
- Conditional edge after the Data Agent stops the pipeline early if input is invalid
- Each agent is a pure function — independently testable and replaceable
- The graph is compiled once on startup and reused across requests

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| API        | FastAPI with auto-generated docs  |
| Agent Pipeline | LangGraph StateGraph          |
| AI         | Google Gemini (gemini-2.5-flash)  |
| Database   | SQLAlchemy + SQLite               |
| Auth       | bcrypt password hashing           |
| Deployment | Render.com                        |

---

## API Endpoints

| Method | Endpoint                          | Description                        |
|--------|-----------------------------------|------------------------------------|
| POST   | /auth/signup                      | Create a new account               |
| POST   | /auth/login                       | Login and receive access token     |
| GET    | /api/users/{id}/summary           | Full financial summary             |
| GET    | /api/users/{id}/analyze           | Run the 5-agent LangGraph pipeline |
| POST   | /api/users/{id}/simulate          | Scenario simulator                 |
| POST   | /api/users/{id}/chat              | AI chat with financial context     |
| GET    | /api/users/{id}/profile           | User profile details               |
| POST   | /api/users/{id}/income            | Set monthly income                 |
| POST   | /api/users/{id}/expenses          | Add an expense                     |
| DELETE | /api/users/{id}/expenses/{exp_id} | Delete an expense                  |
| POST   | /api/users/{id}/loans             | Add a loan                         |
| DELETE | /api/users/{id}/loans/{loan_id}   | Delete a loan                      |

---

## Running Locally
```bash
git clone https://github.com/ruchita0131/smartemi
cd smartemi
pip install -r requirements.txt
cp .env.example .env
# Fill in GEMINI_API_KEY and SECRET_KEY in .env
uvicorn main:app --reload
```

Visit http://localhost:8000/docs for the interactive API documentation.

## Environment Variables
```
DATABASE_URL=sqlite:///./smartemi.db
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
```

---

## Project Structure
```
smartemi/
├── main.py                  # FastAPI app, all route definitions
├── models.py                # SQLAlchemy models (User, Loan, Expense, Goal)
├── database.py              # DB engine and session setup
├── schemas.py               # Pydantic request/response models
├── agents/
│   ├── graph.py             # LangGraph StateGraph definition
│   ├── data_agent.py        # Input validation and structuring
│   ├── analysis_agent.py    # DTI ratio and health score
│   ├── optimizer_agent.py   # Avalanche and Snowball simulation
│   ├── forecast_agent.py    # Amortization projections
│   └── advisor_agent.py     # Gemini AI reasoning
├── requirements.txt
└── Procfile                 # Render deployment config
```

---

## Deployment

Backend is deployed on Render.com using:
```
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

The SQLite database persists between restarts on Render's free tier.