"""
Database configuration and SQLAlchemy ORM models.
Supports PostgreSQL (production) with automatic fallback to SQLite (local/dev).
"""

import os
import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session

Base = declarative_base()

# Default storage directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
STORAGE_DIR = os.environ.get("STORAGE_DIR", os.path.join(PROJECT_ROOT, "storage"))
os.makedirs(STORAGE_DIR, exist_ok=True)


class User(Base):
    """
    Users table:
    Stores registered user accounts (optional for guests).
    """
    __tablename__ = 'users'

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    images = relationship("ImageRecord", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ImageRecord(Base):
    """
    Images table:
    Stores metadata and persistent file storage references for uploaded and cut images.
    Raw image binary data is NEVER stored directly in the database.
    """
    __tablename__ = 'images'

    image_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True, index=True)
    guest_session_id = Column(String(64), nullable=True, index=True)

    original_filename = Column(String(255), nullable=False)
    original_image_path = Column(String(512), nullable=False)
    processed_image_path = Column(String(512), nullable=False)

    original_format = Column(String(32), default='png', nullable=False)
    output_format = Column(String(32), default='png', nullable=False)

    file_size = Column(Integer, default=0, nullable=False)  # bytes
    image_width = Column(Integer, default=0, nullable=False)
    image_height = Column(Integer, default=0, nullable=False)

    processing_status = Column(String(32), default='completed', nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="images")
    history_entries = relationship("ProcessingHistoryRecord", back_populates="image", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "image_id": self.image_id,
            "user_id": self.user_id,
            "guest_session_id": self.guest_session_id,
            "original_filename": self.original_filename,
            "original_image_path": self.original_image_path,
            "processed_image_path": self.processed_image_path,
            "original_format": self.original_format,
            "output_format": self.output_format,
            "file_size": self.file_size,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "processing_status": self.processing_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "history_count": len(self.history_entries) if self.history_entries else 0
        }


class ProcessingHistoryRecord(Base):
    """
    Processing History table:
    Audits every background removal or export event associated with an image.
    """
    __tablename__ = 'processing_history'

    history_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id = Column(String(36), ForeignKey('images.image_id', ondelete='CASCADE'), nullable=False, index=True)

    processing_time = Column(Float, default=0.0, nullable=False)  # seconds
    selected_output_format = Column(String(32), default='png', nullable=False)
    background_type = Column(String(32), default='transparent', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    image = relationship("ImageRecord", back_populates="history_entries")

    def to_dict(self):
        return {
            "history_id": self.history_id,
            "image_id": self.image_id,
            "processing_time": self.processing_time,
            "processing_time_ms": int(self.processing_time * 1000),
            "selected_output_format": self.selected_output_format,
            "background_type": self.background_type,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# Composite Indexes for optimal querying, sorting, and pagination
Index('idx_images_session_created', ImageRecord.guest_session_id, ImageRecord.created_at.desc())
Index('idx_images_user_created', ImageRecord.user_id, ImageRecord.created_at.desc())


# Engine & Session Management
_engine = None
_session_factory = None
db_session = None


def get_database_url() -> str:
    """Retrieves DATABASE_URL from environment or builds SQLite fallback URL."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        # Normalize postgres:// prefix if used by legacy cloud providers
        if env_url.startswith("postgres://"):
            env_url = env_url.replace("postgres://", "postgresql://", 1)
        return env_url

    sqlite_path = os.path.join(STORAGE_DIR, "lumina_studio.db")
    # Normalized forward slashes for SQLite URI
    norm_path = sqlite_path.replace("\\", "/")
    return f"sqlite:///{norm_path}"


def init_db(database_url: str = None):
    """
    Initializes the database engine, creates tables if absent,
    and configures thread-safe scoped sessions.
    """
    global _engine, _session_factory, db_session
    url = database_url or get_database_url()

    is_sqlite = url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}

    # Pool configs for production PostgreSQL
    engine_kwargs = {
        "connect_args": connect_args,
        "pool_pre_ping": True,
        "echo": False
    }

    if not is_sqlite:
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20

    _engine = create_engine(url, **engine_kwargs)
    _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    db_session = scoped_session(_session_factory)

    # Automatically create missing tables
    Base.metadata.create_all(bind=_engine)
    return _engine


def get_db():
    """Context-friendly or route-friendly session provider."""
    global db_session
    if db_session is None:
        init_db()
    return db_session
