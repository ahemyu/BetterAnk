import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import time
from routers import authentication, decks, flashcards, llm

# Load environment variables from .env file
load_dotenv()

# This allows running the app with `python src/main.py`

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
app = FastAPI(title="BetterAnk API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],  # Vite dev and preview servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and their processing time."""
    start_time = time.time()

    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.debug(f"Request headers: {dict(request.headers)}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"Completed {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.3f}s")

    return response

app.include_router(authentication.router)
app.include_router(decks.router)
app.include_router(flashcards.router)
app.include_router(llm.router)

# we serve frontend as static files from the same server
frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend/build")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
