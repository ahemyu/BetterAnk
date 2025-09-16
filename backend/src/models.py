from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Float
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum

class Message(BaseModel):
    message: str

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
    next_review_at = Column(DateTime, default=datetime.now, index=True)
    review_count = Column(Integer, default=0)
    easiness_factor = Column(Float, default=2.5, nullable=False)
    interval = Column(Integer, default=1, nullable=False)
    repetitions = Column(Integer, default=0, nullable=False)
    reviews = relationship("DBReview", back_populates="flashcard", cascade="all, delete-orphan") # cascade means that if a flashcard is deleted, all its reviews will also be deleted

    # Adding deck relationship
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=True, index=True)  # Nullable because a card might not belong to a deck initially
    deck = relationship("DBDeck", back_populates="flashcards")

    # Adding user relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("DBUser", back_populates="flashcards")

class DBReview(Base):
    """SQLAlchemy model for reviews table in the database."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    flashcard_id = Column(Integer, ForeignKey("flashcards.id"), nullable=False, index=True)
    review_at = Column(DateTime, default=datetime.now, nullable=False)
    feedback = Column(SQLAlchemyEnum(ReviewFeedback), nullable=False)

    flashcard = relationship("DBFlashcard", back_populates="reviews")

    # Adding user relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("DBUser", back_populates="reviews")

class DBDeck(Base):
    """SQLAlchemy model for decks table in the database."""
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship with flashcards
    flashcards = relationship("DBFlashcard", back_populates="deck", cascade="all, delete-orphan")  # cascade means that if a deck is deleted, all its flashcards will also be deleted

    # Adding user relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("DBUser", back_populates="decks")

class DBUser(Base):
    """SQLAlchemy model for users table in the database."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    decks = relationship("DBDeck", back_populates="user", cascade="all, delete-orphan")
    flashcards = relationship("DBFlashcard", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("DBReview", back_populates="user", cascade="all, delete-orphan") 

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

class UpdateFlashcard(BaseModel):
    """Update the front and/or back of a flashcard."""
    front: str | None = None
    back: str | None = None

class Review(BaseModel):
    """Represents a review of a flashcard."""
    model_config = ConfigDict(from_attributes=True) # to allow conversion from SQLAlchemy model
    id: int | None = None  # Optional because it will be assigned by the database
    flashcard_id: int
    review_at: datetime = datetime.now()
    feedback: ReviewFeedback

class ReviewCreate(BaseModel):
    """Request body for creating a review."""
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
    review_count: int = 0  # Number of times the flashcard has been reviewed
    easiness_factor: float = 2.5
    interval: int = 1
    repetitions: int = 0
    deck_id: int | None = None  

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
