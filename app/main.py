from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.cleaner import clean_hotels
from app.rag import ask_question, create_embeddings
from app.scraper import scrape_hotels

app = FastAPI(title="Travel Africa RAG API")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
HOTELS_CSV = DATA_DIR / "hotels.csv"

# Serve static files (CSS & JavaScript)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load HTML templates
templates = Jinja2Templates(directory="templates")


class QuestionRequest(BaseModel):
    question: str


# Homepage
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html"
    )


# Health Check
@app.get("/health")
def health():
    return {"status": "ok"}


# Scrape Hotels
@app.post("/scrape")
def scrape():
    df = scrape_hotels()
    return {
        "message": "Scraping completed",
        "records": len(df)
    }


# Clean Data
@app.post("/clean-data")
def clean_data():
    df = clean_hotels()
    return {
        "message": "Cleaning completed",
        "records": len(df)
    }


# Create Embeddings
@app.post("/create-embeddings")
def embeddings():
    return create_embeddings()


# Ask RAG
@app.post("/ask")
def ask(request: QuestionRequest):
    return ask_question(request.question)


# Get All Hotels
@app.get("/hotels")
def get_hotels():
    df = pd.read_csv(HOTELS_CSV)
    df = df.fillna("")
    return df.to_dict(orient="records")


# Hotels by Location
@app.get("/hotels/{location}")
def get_hotels_by_location(location: str):
    df = pd.read_csv(HOTELS_CSV)
    df = df.fillna("")

    filtered = df[
        df["location"].astype(str).str.lower() == location.lower()
    ]

    return filtered.to_dict(orient="records")


# Trip Planner
@app.post("/plan-trip")
def plan_trip(request: QuestionRequest):
    return ask_question(request.question)