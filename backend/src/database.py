from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection string
# Format: postgresql://username:password@host:port/database_name
SQLALCHEMY_DATABASE_URL = "postgresql://ahemyu:lol@localhost:5432/betterankdb"

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class
Base = declarative_base()

# FastAPI dependency
def get_db():
    """Provides a database session for endpoints.
    
    This function creates a new database session for each request and
    ensures the session is closed when the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()