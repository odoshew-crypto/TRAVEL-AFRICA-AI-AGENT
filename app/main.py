from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.scraper import scrape_hotels

app = FastAPI(title="Travel Africa RAG API")


scrape_status = {
    "state": "idle",
    "message": "No scraping job has started",
    "result": None,
}


@app.get("/")
def home():
    return {"message": "Travel Africa RAG API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


def run_scrape_job():
    """
    Runs scraping after the API has already returned a response.
    """

    scrape_status["state"] = "running"
    scrape_status["message"] = "Hotel scraping is running"
    scrape_status["result"] = None

    try:
        result = scrape_hotels()

        scrape_status["state"] = "completed"
        scrape_status["message"] = "Hotel scraping completed"
        scrape_status["result"] = result

    except Exception as exc:
        print(f"Background scraping failed: {exc}")

        scrape_status["state"] = "failed"
        scrape_status["message"] = str(exc)
        scrape_status["result"] = None


@app.post("/scrape", status_code=202)
def start_scraping(background_tasks: BackgroundTasks):
    """
    Starts scraping and immediately returns HTTP 202.
    """

    if scrape_status["state"] == "running":
        raise HTTPException(
            status_code=409,
            detail="A scraping job is already running",
        )

    scrape_status["state"] = "queued"
    scrape_status["message"] = "Hotel scraping has been queued"
    scrape_status["result"] = None

    background_tasks.add_task(run_scrape_job)

    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "message": "Scraping started in the background",
            "check_status_at": "/scrape/status",
        },
    )


@app.get("/scrape/status")
def get_scrape_status():
    return scrape_status