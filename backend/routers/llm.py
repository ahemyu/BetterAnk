"""
Router for LLM-powered flashcard generation endpoints.
"""
import base64
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models import (
    LLMGenerateRequest,
    LLMGenerateFromImageRequest,
    LLMGenerateBatchResponse,
    LLMGeneratedFlashcardResponse,
    DBDeck,
    DBUser
)
from src.database import get_db
from src.dependencies import get_current_user
from src.llm_service import get_llm_service
from datetime import datetime


router = APIRouter(
    prefix="/llm",
    tags=["llm"],
)

llm_service = get_llm_service()

@router.post("/generate-from-text", response_model=LLMGenerateBatchResponse)
async def generate_flashcards_from_text(
    request: LLMGenerateRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate flashcards from text using Gemini API.
    Does not save to database - returns generated cards for review.
    """
    # Validate deck ownership if deck_id is provided
    if request.deck_id is not None:
        deck = db.query(DBDeck).filter(
            DBDeck.id == request.deck_id,
            DBDeck.user_id == current_user.id
        ).first()
        if deck is None:
            raise HTTPException(status_code=404, detail="Deck not found or access denied")

    try:
        # Generate flashcards using LLM service
        flashcard_batch = llm_service.generate_flashcards(
            text=request.text,
            count=request.num_cards
        )

        # Convert to response format
        response_cards = [
            LLMGeneratedFlashcardResponse(front=card.front, back=card.back)
            for card in flashcard_batch.flashcards
        ]

        return LLMGenerateBatchResponse(
            flashcards=response_cards,
            message=f"Successfully generated {len(response_cards)} flashcards"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {str(e)}")


@router.post("/generate-from-image", response_model=LLMGenerateBatchResponse)
async def generate_flashcards_from_image(
    request: LLMGenerateFromImageRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate flashcards from an image using Gemini API.
    Does not save to database - returns generated cards for review.
    """
    # Validate deck ownership if deck_id is provided
    if request.deck_id is not None:
        deck = db.query(DBDeck).filter(
            DBDeck.id == request.deck_id,
            DBDeck.user_id == current_user.id
        ).first()
        if deck is None:
            raise HTTPException(status_code=404, detail="Deck not found or access denied")

    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_base64)

        # Generate flashcards using LLM service
        flashcard_batch = llm_service.generate_flashcards(
            image=image_data,
            count=request.num_cards
        )

        # Convert to response format
        response_cards = [
            LLMGeneratedFlashcardResponse(front=card.front, back=card.back)
            for card in flashcard_batch.flashcards
        ]

        return LLMGenerateBatchResponse(
            flashcards=response_cards,
            message=f"Successfully generated {len(response_cards)} flashcards from image"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {str(e)}")