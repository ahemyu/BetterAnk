import logging
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.models import DBUser
from src.database import get_db
from src.auth import verify_access_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DBUser:
    """Get the current user from the JWT token."""
    payload = verify_access_token(token)
    if not payload:
        logger.warning("Authentication failed: Invalid or expired token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = payload.get("sub")
    if not username:
        logger.warning("Authentication failed: Invalid token - no username in payload")
        raise HTTPException(status_code=401, detail="Invalid token")

    db_user = db.query(DBUser).filter(DBUser.username == username).first()
    if not db_user:
        logger.warning(f"Authentication failed: User '{username}' not found in database")
        raise HTTPException(status_code=401, detail="User not found")

    logger.debug(f"User authenticated: {username} (ID: {db_user.id})")
    return db_user
