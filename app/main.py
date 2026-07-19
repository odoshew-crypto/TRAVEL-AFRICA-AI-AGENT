from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.cleaner import clean_hotels
from app.rag import ask_question, create_embeddings
from app.scraper import scrape_hotels


app = FastAPI(title="Travel Africa RAG API")


# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

HOTELS_CSV = DATA_DIR / "hotels.csv"


# Load HTML templates
templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


class QuestionRequest(BaseModel):
    question: str


# Homepage
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={
            "request": request
        },
    )


# Health Check
@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# Scrape Hotels
@app.post("/scrape")
def scrape():
    try:
        result = scrape_hotels()

        if isinstance(result, dict):
            return {
                "message": "Scraping completed",
                **result,
            }

        if isinstance(result, pd.DataFrame):
            return {
                "message": "Scraping completed",
                "records": len(result),
            }

        return {
            "message": "Scraping completed",
            "result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {exc}",
        ) from exc


# Clean Data
@app.post("/clean-data")
def clean_data():
    try:
        result = clean_hotels()

        if isinstance(result, pd.DataFrame):
            return {
                "message": "Cleaning completed",
                "records": len(result),
            }

        if isinstance(result, dict):
            return {
                "message": "Cleaning completed",
                **result,
            }

        return {
            "message": "Cleaning completed",
            "result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Cleaning failed: {exc}",
        ) from exc


# Create Embeddings
@app.post("/create-embeddings")
def embeddings():
    try:
        return create_embeddings()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Embedding creation failed: {exc}",
        ) from exc


# Ask RAG
@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        return ask_question(
            request.question
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Question processing failed: {exc}",
        ) from exc


# Get All Hotels
@app.get("/hotels")
def get_hotels():
    if not HOTELS_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "hotels.csv was not found. "
                "Run POST /clean-data first."
            ),
        )

    try:
        df = pd.read_csv(HOTELS_CSV)
        df = df.fillna("")

        return df.to_dict(
            orient="records"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read hotels: {exc}",
        ) from exc


# Hotels by Location
@app.get("/hotels/{location}")
def get_hotels_by_location(location: str):
    if not HOTELS_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "hotels.csv was not found. "
                "Run POST /clean-data first."
            ),
        )

    try:
        df = pd.read_csv(HOTELS_CSV)
        df = df.fillna("")

        if "location" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail=(
                    "The hotels dataset does not "
                    "contain a location column."
                ),
            )

        filtered = df[
            df["location"]
            .astype(str)
            .str.strip()
            .str.casefold()
            == location.strip().casefold()
        ]

        return filtered.to_dict(
            orient="records"
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not filter hotels: {exc}",
        ) from exc


# Trip Planner
@app.post("/plan-trip")
def plan_trip(request: QuestionRequest):
    try:
        return ask_question(
            request.question
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Trip planning failed: {exc}",
        ) from exc