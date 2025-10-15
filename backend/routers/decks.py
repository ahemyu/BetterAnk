import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.models import Deck, DBDeck, UpdateDeck, Flashcard, DBFlashcard, DBUser, Message
from src.database import get_db
from src.dependencies import get_current_user

logger = logging.getLogger(__name__)

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
    Create a new deck for the current user. Can optionally specify a parent_deck_id to create a subdeck.
    """
    logger.info(f"Creating deck '{deck.name}' for user {current_user.username} (ID: {current_user.id})")

    # If parent_deck_id is specified, validate it
    if deck.parent_deck_id:
        parent_deck = db.query(DBDeck).filter(
            DBDeck.id == deck.parent_deck_id,
            DBDeck.user_id == current_user.id
        ).first()
        if parent_deck is None:
            logger.warning(f"Parent deck {deck.parent_deck_id} not found for user {current_user.username}")
            raise HTTPException(status_code=404, detail="Parent deck not found")

        # Ensure the parent deck is not itself a subdeck (only one level of nesting allowed)
        if parent_deck.parent_deck_id is not None:
            logger.warning(f"Attempted to create subdeck under subdeck {deck.parent_deck_id}")
            raise HTTPException(status_code=400, detail="Cannot create subdeck under a subdeck. Only one level of nesting is allowed.")

        logger.info(f"Creating subdeck '{deck.name}' under parent deck '{parent_deck.name}' (ID: {deck.parent_deck_id})")

    db_deck = DBDeck(
        name=deck.name,
        description=deck.description,
        created_at=datetime.now(),
        user_id=current_user.id,
        parent_deck_id=deck.parent_deck_id
    )

    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)

    logger.info(f"Deck created successfully: '{deck.name}' (ID: {db_deck.id})")
    return db_deck

@router.get("/{deck_id}", response_model=Deck)
def get_deck(
    deck_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific deck by ID."""
    logger.info(f"Fetching deck {deck_id} for user {current_user.username} (ID: {current_user.id})")

    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        logger.warning(f"Deck {deck_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Deck not found")

    logger.debug(f"Deck retrieved: '{db_deck.name}' (ID: {db_deck.id})")
    return db_deck

@router.get("/{deck_id}/subdecks", response_model=List[Deck])
def get_subdecks(
    deck_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all subdecks for a specific deck."""
    logger.info(f"Fetching subdecks for deck {deck_id}, user {current_user.username} (ID: {current_user.id})")

    # Verify the parent deck exists and belongs to the user
    parent_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if parent_deck is None:
        logger.warning(f"Deck {deck_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Deck not found")

    # Get all subdecks for this deck
    subdecks = db.query(DBDeck).filter(
        DBDeck.parent_deck_id == deck_id,
        DBDeck.user_id == current_user.id
    ).all()

    logger.info(f"Retrieved {len(subdecks)} subdecks for deck {deck_id}")
    return subdecks

@router.get("", response_model=List[Deck])
def get_decks(
    limit: int = 100,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all top-level decks (not subdecks) for the current user with pagination.
    """
    logger.info(f"Fetching top-level decks for user {current_user.username} (ID: {current_user.id}), limit: {limit}")

    # Only return decks without a parent_deck_id (top-level decks)
    decks = db.query(DBDeck).filter(
        DBDeck.user_id == current_user.id,
        DBDeck.parent_deck_id == None
    ).limit(limit).all()

    logger.info(f"Retrieved {len(decks)} top-level decks for user {current_user.username}")
    return decks

@router.get("/{deck_id}/flashcards", response_model=List[Flashcard])
def get_deck_flashcards(
    deck_id: int,
    due: bool = False,
    limit: int = 100,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get flashcards in a deck. If the deck has subdecks, includes cards from all subdecks as well.
    """
    logger.info(f"Fetching flashcards for deck {deck_id}, user {current_user.username}, due: {due}, limit: {limit}")

    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        logger.warning(f"Deck {deck_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Deck not found")

    # Get all subdeck IDs for this deck
    subdeck_ids = [subdeck.id for subdeck in db.query(DBDeck).filter(
        DBDeck.parent_deck_id == deck_id,
        DBDeck.user_id == current_user.id
    ).all()]

    # Create list of deck IDs to query (parent deck + all subdecks)
    deck_ids_to_query = [deck_id] + subdeck_ids

    # Query flashcards from the deck and all its subdecks
    query = db.query(DBFlashcard).filter(
        DBFlashcard.deck_id.in_(deck_ids_to_query),
        DBFlashcard.user_id == current_user.id
    )

    if due:
        now = datetime.now()
        query = query.filter(DBFlashcard.next_review_at <= now)

    flashcards = query.limit(limit).all()

    if subdeck_ids:
        logger.info(f"Retrieved {len(flashcards)} flashcards from deck {deck_id} and {len(subdeck_ids)} subdecks")
    else:
        logger.info(f"Retrieved {len(flashcards)} flashcards from deck {deck_id}")

    return flashcards

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
    logger.info(f"Updating deck {deck_id} for user {current_user.username} (ID: {current_user.id})")

    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        logger.warning(f"Deck {deck_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Deck not found")

    if deck.name:
        logger.debug(f"Updating deck name from '{db_deck.name}' to '{deck.name}'")
        db_deck.name = deck.name
    if deck.description:
        logger.debug(f"Updating deck description")
        db_deck.description = deck.description

    db.commit()
    db.refresh(db_deck)

    logger.info(f"Deck {deck_id} updated successfully")
    return db_deck

@router.delete("/{deck_id}", response_model=Message)
def delete_deck(
    deck_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific deck. If it's a parent deck, all subdecks will be deleted by CASCADE."""
    logger.info(f"Deleting deck {deck_id} for user {current_user.username} (ID: {current_user.id})")

    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        logger.warning(f"Deck {deck_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Deck not found")

    deck_name = db_deck.name
    is_parent = db_deck.parent_deck_id is None

    # Count subdecks if this is a parent deck
    subdeck_count = 0
    if is_parent:
        subdeck_count = db.query(DBDeck).filter(DBDeck.parent_deck_id == deck_id).count()
        if subdeck_count > 0:
            logger.info(f"Deleting parent deck '{deck_name}' will also delete {subdeck_count} subdeck(s)")

    db.delete(db_deck)
    db.commit()

    if is_parent and subdeck_count > 0:
        logger.info(f"Parent deck '{deck_name}' (ID: {deck_id}) and {subdeck_count} subdeck(s) deleted successfully")
    else:
        logger.info(f"Deck '{deck_name}' (ID: {deck_id}) deleted successfully")

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
    logger.info(f"Adding flashcard {flashcard_id} to deck {deck_id} for user {current_user.username}")

    flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if flashcard is None:
        logger.warning(f"Flashcard {flashcard_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Flashcard not found")

    deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if deck is None:
        logger.warning(f"Deck {deck_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Deck not found")

    flashcard.deck_id = deck_id
    db.commit()
    db.refresh(deck)

    logger.info(f"Flashcard {flashcard_id} successfully added to deck {deck_id}")
    return deck
