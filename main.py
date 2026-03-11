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