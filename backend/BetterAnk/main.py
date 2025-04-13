from fastapi import Body, FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import DBDeck, Deck, Flashcard, DBFlashcard, Message, Review, DBReview, ReviewFeedback, UpdateDeck
from database import engine, get_db, Base
from datetime import datetime, timedelta

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BetterAnk API")

@app.get("/", response_model=Message)
async def root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Hello from BetterAnk API"}


@app.post("/flashcards", response_model=Flashcard)
def create_flashcard(flashcard: Flashcard, db: Session = Depends(get_db)):
    """
    Create a new flashcard.
    
    This endpoint accepts flashcard data and saves it to the database.
    If a deck_id is provided, the flashcard is associated with that deck.
    """
    # Check if a deck_id was provided and if that deck exists
    if flashcard.deck_id is not None:
        deck = db.query(DBDeck).filter(DBDeck.id == flashcard.deck_id).first()
        if deck is None:
            raise HTTPException(status_code=404, detail="Deck not found")
    
    db_flashcard = DBFlashcard(
        front=flashcard.front,
        back=flashcard.back,
        created_at=datetime.now(),
        next_review_at=datetime.now(),
        deck_id=flashcard.deck_id,  # This assigns the flashcard to the deck if deck_id is provided
        # difficulty_factor=flashcard.difficulty_factor 
    )
    
    # Add to the database session and commit
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)
    
    return db_flashcard

@app.get("/flashcards", response_model=List[Flashcard])
def get_flashcards(due: bool = False, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all flashcards with pagination.
    
    This endpoint returns all flashcards from the database with optional pagination.
    """
    query = db.query(DBFlashcard)

    if due:
        now = datetime.now()
        # Filter flashcards that are due for review
        query = query.filter(DBFlashcard.next_review_at <= now)

    return query.limit(limit).all()

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


@app.post("/flashcards/{flashcard_id}/review", response_model=Review)
def create_review(flashcard_id: int, feedback: str = Body(...), db: Session = Depends(get_db)):
    """
    Create a new review for a flashcard.
    
    This endpoint allows recording the outcome of reviewing a flashcard,
    with feedback that can be 'good', 'mid', or 'bad'.
    """
    # Check if the flashcard exists
    flashcard = db.query(DBFlashcard).filter(DBFlashcard.id == flashcard_id).first()
    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    # Create a new review instance
    now = datetime.now()
    db_review = DBReview(
        flashcard_id=flashcard_id,
        review_at=now,
        feedback=feedback
    )
    
    # Update the flashcard's review information
    flashcard.last_reviewed_at = now
    flashcard.review_count += 1

    # placeholder for review logic
    if feedback == ReviewFeedback.GOOD:
        flashcard.next_review_at = now + timedelta(days=3)
    elif feedback == ReviewFeedback.MID:
        flashcard.next_review_at = now + timedelta(days=1)
    else:  # BAD
        flashcard.next_review_at = now + timedelta(minutes=2)
    
    # Add the review to the database and commit
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    return db_review


### Deck related ###
@app.post("/decks", response_model=Deck)
def create_deck(deck: Deck, db: Session = Depends(get_db)):
    """
    Create a new deck.
    
    This endpoint accepts deck data and saves it to the database.
    """
    db_deck = DBDeck(
        name=deck.name,
        description=deck.description,
        created_at=datetime.now()
    )
    
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    
    return db_deck


@app.get("/decks", response_model=List[Deck])
def get_decks(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all decks with pagination.
    
    This endpoint returns all decks from the database with optional pagination.
    """
    decks = db.query(DBDeck).limit(limit).all()

    return decks


@app.get("/decks/{deck_id}/flashcards", response_model=List[Flashcard])
def get_deck_flashcards(deck_id: int, due: bool = False, limit: int = 100, db: Session = Depends(get_db)):
    """Either get all flashcards in a deck or only the due ones."""
    # Check if the deck exists
    db_deck = db.query(DBDeck).filter(DBDeck.id == deck_id).first()
    if db_deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    # Query flashcards that belong to this deck
    flashcards = db.query(DBFlashcard).filter(DBFlashcard.deck_id == deck_id).limit(limit).all()
    
    if due:
        now = datetime.now()
        # Filter flashcards that are due for review
        flashcards = [card for card in flashcards if card.next_review_at <= now] # This is in O(n) independent of if we do it in the database ourself
    return flashcards


@app.put("/decks/{deck_id}", response_model=Deck)
def update_deck(deck_id: int, deck: UpdateDeck, db: Session = Depends(get_db)):
    """
    Update a specific deck.
    
    This endpoint updates the name and/or description of a deck.
    """
    db_deck = db.query(DBDeck).filter(DBDeck.id == deck_id).first()
    if db_deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    # Update the deck's properties
    if deck.name:
        db_deck.name = deck.name
    if deck.description:
        db_deck.description = deck.description
    
    db.commit()
    db.refresh(db_deck)
    
    return db_deck


@app.delete("/decks/{deck_id}", response_model=Message)
def delete_deck(deck_id: int, db: Session = Depends(get_db)):
    """Delete a specific deck."""
    db_deck = db.query(DBDeck).filter(DBDeck.id == deck_id).first()
    if db_deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    db.delete(db_deck)
    db.commit()
    
    return {"message": "Deck deleted successfully"}


@app.put("/decks/{deck_id}/flashcard/{flashcard_id}", response_model=Deck)
def add_flashcard_to_deck(deck_id: int, flashcard_id: int, db: Session = Depends(get_db)):
    """
    Add a flashcard to a deck.
    
    This endpoint assigns a flashcard to a specific deck.
    """
    # Check if the flashcard exists
    flashcard = db.query(DBFlashcard).filter(DBFlashcard.id == flashcard_id).first()
    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    # Check if the deck exists
    deck = db.query(DBDeck).filter(DBDeck.id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    # Assign the flashcard to the deck
    flashcard.deck_id = deck_id
    
    db.commit()
    db.refresh(deck) # we need to refresh as we are actually modifying the flashcards and not the deck itself
    
    return deck


@app.delete("/flashcards/{flashcard_id}/deck", response_model=Message)
def remove_flashcard_from_deck(flashcard_id: int, db: Session = Depends(get_db)):
    """
    Remove a flashcard from its deck.
    
    This endpoint removes a flashcard's association with any deck.
    """
    # Check if the flashcard exists
    flashcard = db.query(DBFlashcard).filter(DBFlashcard.id == flashcard_id).first()
    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    # Check if the flashcard is assigned to a deck
    if flashcard.deck_id is None:
        raise HTTPException(status_code=400, detail="Flashcard is not assigned to any deck")
    
    # Remove the flashcard from the deck
    flashcard.deck_id = None
    
    db.commit()
    
    return {"message": "Flashcard removed from deck successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)