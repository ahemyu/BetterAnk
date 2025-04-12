from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Flashcard, DBFlashcard
from database import engine, get_db, Base
from datetime import datetime

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BetterAnk API")

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Hello from BetterAnk API"}

@app.post("/flashcards", response_model=Flashcard)
def create_flashcard(flashcard: Flashcard, db: Session = Depends(get_db)):
    """
    Create a new flashcard.
    
    This endpoint accepts flashcard data and saves it to the database.
    """
    # Create a new DBFlashcard instance
    db_flashcard = DBFlashcard(
        front=flashcard.front,
        back=flashcard.back,
        created_at=datetime.now(),
        next_review_at=datetime.now()
    )
    
    # Add to the database session and commit
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)
    
    return db_flashcard

@app.get("/flashcards", response_model=List[Flashcard])
def get_flashcards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all flashcards with pagination.
    
    This endpoint returns all flashcards from the database with optional pagination.
    """
    return db.query(DBFlashcard).offset(skip).limit(limit).all()

@app.get("/flashcards/{flashcard_id}", response_model=Flashcard)
def get_flashcard(flashcard_id: int, db: Session = Depends(get_db)):
    """
    Get a specific flashcard by ID.
    
    This endpoint retrieves a single flashcard by its ID from the database.
    """
    db_flashcard = db.query(DBFlashcard).filter(DBFlashcard.id == flashcard_id).first()
    if db_flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return db_flashcard

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)