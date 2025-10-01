import sys
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# This allows running the app with `python src/main.py`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from routers import authentication, decks, flashcards, llm

app = FastAPI(title="BetterAnk API")

app.include_router(authentication.router)
app.include_router(decks.router)
app.include_router(flashcards.router)
app.include_router(llm.router)

# we serve frontend as static files from the same server 
frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend/src")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
