import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.models import UserCreate, DBUser, UserResponse, Message
from src.database import get_db
from src.utils import hash_password, verify_password
from src.auth import create_access_token
from src.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["authentication"],
)

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    logger.info(f"Registration attempt for username: {user.username}, email: {user.email}")

    if db.query(DBUser).filter(DBUser.username == user.username).first():
        logger.warning(f"Registration failed: Username '{user.username}' already exists")
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(DBUser).filter(DBUser.email == user.email).first():
        logger.warning(f"Registration failed: Email '{user.email}' already exists")
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = hash_password(user.password)
    db_user = DBUser(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info(f"User registered successfully: {user.username} (ID: {db_user.id})")
    return db_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    logger.info(f"Login attempt for username: {form_data.username}")

    db_user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        logger.warning(f"Login failed for username: {form_data.username} - Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": db_user.username})
    logger.info(f"User logged in successfully: {form_data.username} (ID: {db_user.id})")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: DBUser = Depends(get_current_user)):
    """Get the current logged-in user."""
    logger.info(f"User profile accessed: {current_user.username} (ID: {current_user.id})")
    return current_user

@router.delete("/me", response_model=Message)
def delete_me(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete the current user's account."""
    logger.info(f"Account deletion requested for user: {current_user.username} (ID: {current_user.id})")
    db.delete(current_user)
    db.commit()
    logger.info(f"User account deleted successfully: {current_user.username} (ID: {current_user.id})")
    return {"message": "User account deleted successfully"}
