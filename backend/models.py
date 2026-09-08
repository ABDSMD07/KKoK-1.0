from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)

from database import Base


class Document(Base):

    __tablename__ = "documents"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    document_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )


    original_filename = Column(
        String,
        nullable=False
    )


    stored_filename = Column(
        String,
        nullable=False
    )


    original_path = Column(
        String,
        nullable=False
    )


    concise_path = Column(
        String,
        nullable=True
    )


    detailed_path = Column(
        String,
        nullable=True
    )


    status = Column(
        String,
        default="Uploaded",
        nullable=False
    )


    confidence = Column(
        String,
        default="—",
        nullable=False
    )


    # IMPORTANT:
    #
    # For now we deliberately store UTC as a naive datetime.
    # This keeps compatibility with your existing database.
    #
    # main.py will explicitly serialize this as UTC with "Z",
    # so JavaScript cannot mistake it for local time.

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )