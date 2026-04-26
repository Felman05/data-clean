"""SQLAlchemy engine, session factory, and startup connection test."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

_DB_HOST = os.getenv("DB_HOST", "localhost")
_DB_PORT = os.getenv("DB_PORT", "3306")
_DB_USER = os.getenv("DB_USER", "root")
_DB_PASSWORD = os.getenv("DB_PASSWORD", "")
_DB_NAME = os.getenv("DB_NAME", "fedm_system")

_URL = (
    f"mysql+pymysql://{_DB_USER}:{_DB_PASSWORD}"
    f"@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}?charset=utf8mb4"
)

engine = create_engine(_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Session:
    """Return a new SQLAlchemy session. Caller is responsible for closing it."""
    return SessionLocal()


def test_connection() -> tuple[bool, str]:
    """Run SELECT 1 and return (success, message) for the sidebar status banner."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connected ✓"
    except Exception as exc:
        return False, f"Database not reachable — start MySQL in XAMPP ({exc})"
