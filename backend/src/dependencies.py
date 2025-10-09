import logging
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.models import DBUser
from src.database import get_db
from src.auth import verify_access_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> DBUser:
    """Get the current user from the JWT token in HttpOnly cookie."""
    # Try to get token from cookie first
    token = request.cookies.get("access_token")

    # Fallback to Authorization header for backward compatibility
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        logger.warning("Authentication failed: No token provided")
        raise HTTPException(status_code=401, detail="Not authenticated")

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
