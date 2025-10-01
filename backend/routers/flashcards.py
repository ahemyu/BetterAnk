import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.spaced_repetition import SM2Algo
from src.models import Flashcard, DBFlashcard, Message, Review, DBReview, ReviewCreate, UpdateFlashcard, DBDeck, DBUser
from src.database import get_db
from src.dependencies import get_current_user

logger = logging.getLogger(__name__)

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
    logger.info(f"Creating flashcard for user {current_user.username} (ID: {current_user.id}), deck_id: {flashcard.deck_id}")

    if flashcard.deck_id is not None:
        deck = db.query(DBDeck).filter(
            DBDeck.id == flashcard.deck_id,
            DBDeck.user_id == current_user.id
        ).first()
        if deck is None:
            logger.warning(f"Deck {flashcard.deck_id} not found or access denied for user {current_user.username}")
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

    logger.info(f"Flashcard created successfully (ID: {db_flashcard.id})")
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
    logger.info(f"Fetching flashcards for user {current_user.username}, due: {due}, limit: {limit}")

    query = db.query(DBFlashcard).filter(DBFlashcard.user_id == current_user.id)

    if due:
        now = datetime.now()
        query = query.filter(DBFlashcard.next_review_at <= now)

    flashcards = query.limit(limit).all()
    logger.info(f"Retrieved {len(flashcards)} flashcards for user {current_user.username}")
    return flashcards

@router.get("/{flashcard_id}", response_model=Flashcard)
def get_flashcard(
    flashcard_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific flashcard by ID.
    """
    logger.info(f"Fetching flashcard {flashcard_id} for user {current_user.username}")

    db_flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if db_flashcard is None:
        logger.warning(f"Flashcard {flashcard_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Flashcard not found")

    logger.debug(f"Flashcard {flashcard_id} retrieved successfully")
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
    logger.info(f"Updating flashcard {flashcard_id} for user {current_user.username}")

    db_flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if db_flashcard is None:
        logger.warning(f"Flashcard {flashcard_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Flashcard not found")

    if flashcard.front:
        logger.debug(f"Updating flashcard {flashcard_id} front content")
        db_flashcard.front = flashcard.front
    if flashcard.back:
        logger.debug(f"Updating flashcard {flashcard_id} back content")
        db_flashcard.back = flashcard.back

    db.commit()
    db.refresh(db_flashcard)

    logger.info(f"Flashcard {flashcard_id} updated successfully")
    return db_flashcard

@router.delete("/{flashcard_id}", response_model=Message)
def delete_flashcard(
    flashcard_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific flashcard."""
    logger.info(f"Deleting flashcard {flashcard_id} for user {current_user.username}")

    db_flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if db_flashcard is None:
        logger.warning(f"Flashcard {flashcard_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Flashcard not found")

    db.delete(db_flashcard)
    db.commit()

    logger.info(f"Flashcard {flashcard_id} deleted successfully")
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
    logger.info(f"Creating review for flashcard {flashcard_id}, user {current_user.username}, feedback: {review_data.feedback}")

    flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if flashcard is None:
        logger.warning(f"Flashcard {flashcard_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Flashcard not found")

    logger.debug(f"Applying SM-2 algorithm to flashcard {flashcard_id}")
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

    logger.info(f"Review created for flashcard {flashcard_id}, next review at: {flashcard.next_review_at}")
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
    logger.info(f"Removing flashcard {flashcard_id} from its deck for user {current_user.username}")

    flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if flashcard is None:
        logger.warning(f"Flashcard {flashcard_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Flashcard not found")

    if flashcard.deck_id is None:
        logger.warning(f"Flashcard {flashcard_id} is not assigned to any deck")
        raise HTTPException(status_code=400, detail="Flashcard is not assigned to any deck")

    old_deck_id = flashcard.deck_id
    flashcard.deck_id = None
    db.commit()

    logger.info(f"Flashcard {flashcard_id} removed from deck {old_deck_id} successfully")
    return {"message": "Flashcard removed from deck successfully"}
