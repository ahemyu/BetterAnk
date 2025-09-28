from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.spaced_repetition import SM2Algo
from src.models import Flashcard, DBFlashcard, Message, Review, DBReview, ReviewCreate, UpdateFlashcard, DBDeck, DBUser
from src.database import get_db
from src.dependencies import get_current_user

router = APIRouter(
    prefix="/flashcards",
    tags=["flashcards"],
)

@router.post("", response_model=Flashcard)
def create_flashcard(
    flashcard: Flashcard, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new flashcard for the current user.
    """
    if flashcard.deck_id is not None:
        deck = db.query(DBDeck).filter(
            DBDeck.id == flashcard.deck_id,
            DBDeck.user_id == current_user.id
        ).first()
        if deck is None:
            raise HTTPException(status_code=404, detail="Deck not found or access denied")
    
    db_flashcard = DBFlashcard(
        front=flashcard.front,
        back=flashcard.back,
        created_at=datetime.now(),
        next_review_at=datetime.now(),
        deck_id=flashcard.deck_id,
        user_id=current_user.id 
    )
    
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)
    
    return db_flashcard

@router.get("", response_model=List[Flashcard])
def get_flashcards(
    due: bool = False, 
    limit: int = 100, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all flashcards for the current user with pagination.
    """
    query = db.query(DBFlashcard).filter(DBFlashcard.user_id == current_user.id)

    if due:
        now = datetime.now()
        query = query.filter(DBFlashcard.next_review_at <= now)

    return query.limit(limit).all()

@router.get("/{flashcard_id}", response_model=Flashcard)
def get_flashcard(
    flashcard_id: int, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific flashcard by ID.
    """
    db_flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if db_flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return db_flashcard

@router.put("/{flashcard_id}", response_model=Flashcard)
def update_flashcard(
    flashcard_id: int,
    flashcard: UpdateFlashcard,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific flashcard.
    """
    db_flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if db_flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    if flashcard.front:
        db_flashcard.front = flashcard.front
    if flashcard.back:
        db_flashcard.back = flashcard.back

    db.commit()
    db.refresh(db_flashcard)

    return db_flashcard

@router.delete("/{flashcard_id}", response_model=Message)
def delete_flashcard(
    flashcard_id: int, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific flashcard."""
    db_flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if db_flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    db.delete(db_flashcard)
    db.commit()
    
    return {"message": "Flashcard deleted successfully"}

@router.post("/{flashcard_id}/review", response_model=Review)
def create_review(
    flashcard_id: int, 
    review_data: ReviewCreate, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new review for a flashcard and update its next review date based on the SM-2 algorithm.
    """
    flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    SM2Algo.update_flashcard(feedback=review_data.feedback, flashcard=flashcard)
    db_review = DBReview(
        flashcard_id=flashcard_id,
        review_at=datetime.now(),
        feedback=review_data.feedback,
        user_id=current_user.id
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    return db_review

@router.delete("/{flashcard_id}/deck", response_model=Message)
def remove_flashcard_from_deck(
    flashcard_id: int, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a flashcard from its deck.
    """
    flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    if flashcard.deck_id is None:
        raise HTTPException(status_code=400, detail="Flashcard is not assigned to any deck")
    
    flashcard.deck_id = None
    db.commit()
    
    return {"message": "Flashcard removed from deck successfully"}
