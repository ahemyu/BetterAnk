from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.models import Deck, DBDeck, UpdateDeck, Flashcard, DBFlashcard, DBUser, Message
from src.database import get_db
from src.dependencies import get_current_user

router = APIRouter(
    prefix="/decks",
    tags=["decks"],
)

@router.post("", response_model=Deck)
def create_deck(
    deck: Deck, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new deck for the current user.
    """
    db_deck = DBDeck(
        name=deck.name,
        description=deck.description,
        created_at=datetime.now(),
        user_id=current_user.id
    )
    
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    
    return db_deck

@router.get("/{deck_id}", response_model=Deck)
def get_deck(
    deck_id: int, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific deck by ID."""
    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return db_deck

@router.get("", response_model=List[Deck])
def get_decks(
    limit: int = 100, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all decks for the current user with pagination.
    """
    decks = db.query(DBDeck).filter(DBDeck.user_id == current_user.id).limit(limit).all()
    return decks

@router.get("/{deck_id}/flashcards", response_model=List[Flashcard])
def get_deck_flashcards(
    deck_id: int, 
    due: bool = False, 
    limit: int = 100, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get flashcards in a deck."""
    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    query = db.query(DBFlashcard).filter(
        DBFlashcard.deck_id == deck_id,
        DBFlashcard.user_id == current_user.id
    )
    
    if due:
        now = datetime.now()
        query = query.filter(DBFlashcard.next_review_at <= now)
    
    return query.limit(limit).all()

@router.put("/{deck_id}", response_model=Deck)
def update_deck(
    deck_id: int, 
    deck: UpdateDeck, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific deck.
    """
    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    if deck.name:
        db_deck.name = deck.name
    if deck.description:
        db_deck.description = deck.description
    
    db.commit()
    db.refresh(db_deck)
    
    return db_deck

@router.delete("/{deck_id}", response_model=Message)
def delete_deck(
    deck_id: int, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific deck."""
    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    db.delete(db_deck)
    db.commit()
    
    return {"message": "Deck deleted successfully"}

@router.put("/{deck_id}/flashcard/{flashcard_id}", response_model=Deck)
def add_flashcard_to_deck(
    deck_id: int, 
    flashcard_id: int, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a flashcard to a deck (both must belong to current user).
    """
    flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    flashcard.deck_id = deck_id
    db.commit()
    db.refresh(deck)
    
    return deck
