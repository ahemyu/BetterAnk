from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from database import Base

# SQLAlchemy Models (for database tables)
class DBFlashcard(Base):
    """SQLAlchemy model for flashcards table in the database."""
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    front = Column(String, nullable=False)
    back = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, default=datetime.now)
    difficulty_factor = Column(Float, default=2.5)
    review_count = Column(Integer, default=0)


class Flashcard(BaseModel):
    """Represents a flashcard."""
    id: int | None = None  # Optional because it will be assigned by the database
    front: str                # The question or prompt
    back: str                 # The answer
    created_at: datetime | None = None
    last_reviewed: datetime | None = None
    next_review_at: datetime = datetime.now()  # Initially due immediately
    difficulty_factor: float = 2.5  # Default value in the SM-2 algorithm
    review_count: int = 0
    
