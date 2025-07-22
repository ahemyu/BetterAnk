from fastapi import Body, FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from spaced_repetition import SM2Algo
from models import DBDeck, Deck, Flashcard, DBFlashcard, Message, Review, DBReview, ReviewFeedback, UpdateDeck, UserResponse, UserCreate, DBUser, ReviewCreate
from database import engine, get_db, Base
from datetime import datetime, timedelta
from utils import hash_password, verify_password
from auth import create_access_token, verify_access_token

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BetterAnk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  #TODO: Replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=Message)
async def root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Hello from BetterAnk API"}

### login and authentication stuff ###

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DBUser:
    """Get the current user from the JWT token."""
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    db_user = db.query(DBUser).filter(DBUser.username == username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")

    return db_user

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username or email already exists
    if db.query(DBUser).filter(DBUser.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(DBUser).filter(DBUser.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash the password and create the user
    hashed_password = hash_password(user.password)
    db_user = DBUser(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    # Find the user by username
    db_user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Create a JWT token
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
def get_me(current_user: DBUser = Depends(get_current_user)):
    """Get the current logged-in user."""
    return current_user

@app.delete("/me", response_model=Message)
def delete_me(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete the current user's account."""
    db.delete(current_user)
    db.commit()
    return {"message": "User account deleted successfully"}

### flashcards ###
@app.post("/flashcards", response_model=Flashcard)
def create_flashcard(
    flashcard: Flashcard, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new flashcard for the current user.
    
    This endpoint accepts flashcard data and saves it to the database.
    If a deck_id is provided, the flashcard is associated with that deck.
    """
    # Check if a deck_id was provided and if that deck exists and belongs to user
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

@app.get("/flashcards", response_model=List[Flashcard])
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

@app.get("/flashcards/{flashcard_id}", response_model=Flashcard)
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

@app.delete("/flashcards/{flashcard_id}", response_model=Message)
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

### Review ###
@app.post("/flashcards/{flashcard_id}/review", response_model=Review)
def create_review(
    flashcard_id: int, 
    review_data: ReviewCreate, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new review for a flashcard and update its next review date based on the SM-2 algorithm.
    """
    # Check if the flashcard exists and belongs to current user
    flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    # determine next_review date and other sm2 algo related stuff
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

### Deck related ###
@app.post("/decks", response_model=Deck)
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

@app.get("/decks/{deck_id}", response_model=Deck)
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

@app.get("/decks", response_model=List[Deck])
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

@app.get("/decks/{deck_id}/flashcards", response_model=List[Flashcard])
def get_deck_flashcards(
    deck_id: int, 
    due: bool = False, 
    limit: int = 100, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get flashcards in a deck."""
    # Check if the deck exists and belongs to current user
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

@app.put("/decks/{deck_id}", response_model=Deck)
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
    
    # Update the deck's properties
    if deck.name:
        db_deck.name = deck.name
    if deck.description:
        db_deck.description = deck.description
    
    db.commit()
    db.refresh(db_deck)
    
    return db_deck

@app.delete("/decks/{deck_id}", response_model=Message)
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

@app.put("/decks/{deck_id}/flashcard/{flashcard_id}", response_model=Deck)
def add_flashcard_to_deck(
    deck_id: int, 
    flashcard_id: int, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a flashcard to a deck (both must belong to current user).
    """
    # Check if the flashcard exists and belongs to current user
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
    
    # Assign the flashcard to the deck
    flashcard.deck_id = deck_id
    
    db.commit()
    db.refresh(deck)
    
    return deck

@app.delete("/flashcards/{flashcard_id}/deck", response_model=Message)
def remove_flashcard_from_deck(
    flashcard_id: int, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a flashcard from its deck.
    """
    # Check if the flashcard exists
    flashcard = db.query(DBFlashcard).filter(
        DBFlashcard.id == flashcard_id,
        DBFlashcard.user_id == current_user.id
    ).first()
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