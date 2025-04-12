from datetime import datetime
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum

### Enums ###
class ReviewFeedback(str, Enum):
    GOOD = "good"
    MID = "mid"
    BAD = "bad"

### Database models ###
class DBFlashcard(Base):
    """SQLAlchemy model for flashcards table in the database."""
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    front = Column(String, nullable=False)
    back = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, default=datetime.now)
    review_count = Column(Integer, default=0)
    reviews = relationship("DBReview", back_populates="flashcard", cascade="all, delete-orphan") # cascade means that if a flashcard is deleted, all its reviews will also be deleted

    # Adding deck relationship
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=True)  # Nullable because a card might not belong to a deck initially
    deck = relationship("DBDeck", back_populates="flashcards")

class DBReview(Base):
    """SQLAlchemy model for reviews table in the database."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    flashcard_id = Column(Integer, ForeignKey("flashcards.id"), nullable=False)
    review_at = Column(DateTime, default=datetime.now, nullable=False)
    feedback = Column(SQLAlchemyEnum(ReviewFeedback), nullable=False)

    flashcard = relationship("DBFlashcard", back_populates="reviews")

class DBDeck(Base):
    """SQLAlchemy model for decks table in the database."""
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship with flashcards
    flashcards = relationship("DBFlashcard", back_populates="deck", cascade="all, delete-orphan")  # cascade means that if a deck is deleted, all its flashcards will also be deleted


### Pydantic models ###

class Deck(BaseModel):
    """Represents a deck of flashcards."""
    model_config = ConfigDict(from_attributes=True) # to allow conversion from SQLAlchemy model
    id: int | None = None  # Optional because it will be assigned by the database
    name: str
    description: str | None = None
    created_at: datetime | None = None

class UpdateDeck(BaseModel):
    """Update the name and/or description of a Deck."""
    name: str | None = None
    description: str | None = None

class Review(BaseModel):
    """Represents a review of a flashcard."""
    model_config = ConfigDict(from_attributes=True) # to allow conversion from SQLAlchemy model
    id: int | None = None  # Optional because it will be assigned by the database
    flashcard_id: int
    review_at: datetime = datetime.now()# what does this do? 
    feedback: ReviewFeedback

class Flashcard(BaseModel):
    """Represents a flashcard."""
    model_config = ConfigDict(from_attributes=True) # to allow conversion from SQLAlchemy model
    id: int | None = None  # Optional because it will be assigned by the database
    front: str                # The question or prompt
    back: str                 # The answer
    created_at: datetime | None = None
    last_reviewed_at: datetime | None = None
    next_review_at: datetime = datetime.now()  # Initially due  immediately
    # difficulty_factor: float = 2.5  # Default value in the SM-2 algorithm
    review_count: int = 0  # Number of times the flashcard has been reviewed
    deck_id: int | None = None  