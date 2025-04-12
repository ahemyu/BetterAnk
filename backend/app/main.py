from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Flashcard, DBFlashcard, Review, DBReview, ReviewFeedback
from database import engine, get_db, Base
from datetime import datetime, timedelta

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
# this needs to be above get /flashcards/{flashcard_id} bc otherwise FastAPI tries to convert 'due' to an int 
@app.get("/flashcards/due", response_model=List[Flashcard])
def get_due_flashcards(db: Session = Depends(get_db)):
    """
    Get all flashcards that are due for review.
    
    This endpoint returns flashcards where the next_review_at date
    is in the past, meaning they are ready to be reviewed.
    """
    now = datetime.now()
    due_cards = db.query(DBFlashcard).filter(DBFlashcard.next_review_at <= now).all()
    return due_cards

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


@app.post("/reviews", response_model=Review)#TODO:  this endpoint name is not nice
def create_review(review: Review, db: Session = Depends(get_db)):
    """
    Create a new review for a flashcard.
    
    This endpoint allows recording the outcome of reviewing a flashcard,
    with feedback that can be 'good', 'mid', or 'bad'.
    """
    # Check if the flashcard exists
    flashcard = db.query(DBFlashcard).filter(DBFlashcard.id == review.flashcard_id).first()
    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    # Create a new review instance
    now = datetime.now()
    db_review = DBReview(
        flashcard_id=review.flashcard_id,
        review_at=now,
        feedback=review.feedback
    )
    
    # Update the flashcard's review information
    flashcard.last_reviewed_at = now
    flashcard.review_count += 1

    # Simple scheduling logic based on feedback
    if review.feedback == ReviewFeedback.GOOD:
        flashcard.next_review_at = now + timedelta(days=3)
    elif review.feedback == ReviewFeedback.MID:
        flashcard.next_review_at = now + timedelta(days=1)
    else:  # BAD
        flashcard.next_review_at = now + timedelta(minutes=2)
    
    # Add the review to the database and commit
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    return db_review


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)