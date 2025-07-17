"""
Database configuration and connection setup for the Law Exam Learning System.

This module provides:
- SQLAlchemy engine and session configuration
- Database URL construction
- Session factory for dependency injection
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./law_exam_learning.db")

# Create SQLAlchemy engine
# For SQLite, we need to enable foreign key constraints
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    # Log SQL queries in verbose mode disabled now
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
# our models are SQLAlchemy ORM model, not a regular Python class or a Pydantic BaseModel
Base = declarative_base()

# commonly used in FastAPI to manage SQLAlchemy database sessions safely and efficiently
def get_db():
    """
    Dependency function to get database session.
    
    This function is used with FastAPI's dependency injection system
    to provide database sessions to API endpoints.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all database tables.
    
    This function creates all tables defined in the models.
    Should be called during application startup.
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Drop all database tables.
    
    WARNING: This will delete all data!
    Use only for testing or complete reset.
    """
    Base.metadata.drop_all(bind=engine)