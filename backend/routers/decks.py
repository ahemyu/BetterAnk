import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.models import Deck, DBDeck, UpdateDeck, Flashcard, DBFlashcard, DBUser, Message, DeckTree
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
    Create a new deck for the current user.
    Can optionally be a subdeck by providing parent_deck_id.
    """
    logger.info(f"Creating deck '{deck.name}' for user {current_user.username} (ID: {current_user.id})")

    # Validate parent deck if provided
    if deck.parent_deck_id is not None:
        parent_deck = db.query(DBDeck).filter(
            DBDeck.id == deck.parent_deck_id,
            DBDeck.user_id == current_user.id
        ).first()
        if parent_deck is None:
            logger.warning(f"Parent deck {deck.parent_deck_id} not found for user {current_user.username}")
            raise HTTPException(status_code=404, detail="Parent deck not found")
        logger.info(f"Creating subdeck under parent deck '{parent_deck.name}' (ID: {deck.parent_deck_id})")

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

@router.get("", response_model=List[Deck])
def get_decks(
    limit: int = 100,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all decks for the current user with pagination.
    """
    logger.info(f"Fetching decks for user {current_user.username} (ID: {current_user.id}), limit: {limit}")

    decks = db.query(DBDeck).filter(DBDeck.user_id == current_user.id).limit(limit).all()

    logger.info(f"Retrieved {len(decks)} decks for user {current_user.username}")
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
    logger.info(f"Fetching flashcards for deck {deck_id}, user {current_user.username}, due: {due}, limit: {limit}")

    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        logger.warning(f"Deck {deck_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Deck not found")

    query = db.query(DBFlashcard).filter(
        DBFlashcard.deck_id == deck_id,
        DBFlashcard.user_id == current_user.id
    )

    if due:
        now = datetime.now()
        query = query.filter(DBFlashcard.next_review_at <= now)

    flashcards = query.limit(limit).all()
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

@router.get("/{deck_id}/subdecks", response_model=List[Deck])
def get_subdecks(
    deck_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all direct subdecks of a specific deck."""
    logger.info(f"Fetching subdecks for deck {deck_id}, user {current_user.username}")

    # Verify the parent deck exists and belongs to user
    parent_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if parent_deck is None:
        logger.warning(f"Parent deck {deck_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Deck not found")

    # Get all subdecks
    subdecks = db.query(DBDeck).filter(
        DBDeck.parent_deck_id == deck_id,
        DBDeck.user_id == current_user.id
    ).all()

    logger.info(f"Retrieved {len(subdecks)} subdecks for deck {deck_id}")
    return subdecks

@router.get("/tree/all", response_model=List[DeckTree])
def get_deck_tree(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the full deck hierarchy tree for the current user.
    Returns only top-level decks with nested children.
    """
    logger.info(f"Fetching deck tree for user {current_user.username}")

    def build_tree(deck: DBDeck) -> DeckTree:
        """Recursively build deck tree with children."""
        children = db.query(DBDeck).filter(
            DBDeck.parent_deck_id == deck.id,
            DBDeck.user_id == current_user.id
        ).all()

        return DeckTree(
            id=deck.id,
            name=deck.name,
            description=deck.description,
            created_at=deck.created_at,
            parent_deck_id=deck.parent_deck_id,
            children=[build_tree(child) for child in children]
        )

    # Get only top-level decks (no parent)
    top_level_decks = db.query(DBDeck).filter(
        DBDeck.parent_deck_id.is_(None),
        DBDeck.user_id == current_user.id
    ).all()

    tree = [build_tree(deck) for deck in top_level_decks]
    logger.info(f"Built deck tree with {len(tree)} top-level decks")
    return tree

@router.delete("/{deck_id}", response_model=Message)
def delete_deck(
    deck_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific deck."""
    logger.info(f"Deleting deck {deck_id} for user {current_user.username} (ID: {current_user.id})")

    db_deck = db.query(DBDeck).filter(
        DBDeck.id == deck_id,
        DBDeck.user_id == current_user.id
    ).first()
    if db_deck is None:
        logger.warning(f"Deck {deck_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Deck not found")

    deck_name = db_deck.name
    db.delete(db_deck)
    db.commit()

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
