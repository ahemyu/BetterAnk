import logging
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os

logger = logging.getLogger(__name__)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 1

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created access token for subject: {data.get('sub')}")
    return token

def verify_access_token(token: str) -> dict | None:
    """Verify a JWT access token and return the payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Token verified successfully for subject: {payload.get('sub')}")
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        return None
