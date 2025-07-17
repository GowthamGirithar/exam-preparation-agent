"""
Database initialization script for the Law Exam Learning System.

This script:
- Creates all database tables
- Populates CLAT topics for performance tracking
- Sets up default configurations

Note: Questions are stored in Vector DB (ChromaDB), not here.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .database import engine, create_tables, SessionLocal
from .models import Topic, User
from sqlalchemy.orm import Session


def init_database():
    """Initialize the database with tables and initial data."""
    print("Initializing database... and populating master data")
    create_tables()
    # populate initial data
    db = SessionLocal()
    try:
        populate_topics(db) # populate the topics master data
        print("Database initialization completed successfully!")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.rollback()
    finally:
        db.close()


def populate_topics(db: Session):
    """Populate the database with CLAT exam topics for performance tracking."""
    
    # Check if topics already exist
    if db.query(Topic).first():
        print("Topics already exist, skipping...")
        return
    
    clat_topics = [
        # English Language
        {"name": "Reading Comprehension", "category": "English", "description": "Passages with questions on understanding, inference, and analysis"},
        {"name": "Grammar", "category": "English", "description": "Parts of speech, tenses, sentence structure, and language rules"},
        {"name": "Vocabulary", "category": "English", "description": "Word meanings, synonyms, antonyms, and usage"},
        {"name": "Sentence Correction", "category": "English", "description": "Identifying and correcting grammatical errors"},
        
        # General Knowledge & Current Affairs
        {"name": "Indian History", "category": "General Knowledge", "description": "Ancient, medieval, and modern Indian history"},
        {"name": "Indian Geography", "category": "General Knowledge", "description": "Physical and political geography of India"},
        {"name": "Indian Polity", "category": "General Knowledge", "description": "Constitution, governance, and political system"},
        {"name": "Economics", "category": "General Knowledge", "description": "Basic economic concepts and Indian economy"},
        {"name": "Current Affairs", "category": "General Knowledge", "description": "Recent national and international events"},
        {"name": "Science & Technology", "category": "General Knowledge", "description": "Basic science concepts and technological developments"},
        
        # Legal Reasoning
        {"name": "Legal Principles", "category": "Legal Reasoning", "description": "Basic legal concepts and principles"},
        {"name": "Case Studies", "category": "Legal Reasoning", "description": "Application of legal principles to given scenarios"},
        {"name": "Constitutional Law", "category": "Legal Reasoning", "description": "Fundamental rights, duties, and constitutional provisions"},
        {"name": "Contract Law", "category": "Legal Reasoning", "description": "Basic principles of contracts and agreements"},
        
        # Logical Reasoning
        {"name": "Analytical Reasoning", "category": "Logical Reasoning", "description": "Pattern recognition and logical analysis"},
        {"name": "Critical Reasoning", "category": "Logical Reasoning", "description": "Argument evaluation and logical deduction"},
        {"name": "Puzzles", "category": "Logical Reasoning", "description": "Logical puzzles and problem-solving"},
        
        # Quantitative Techniques
        {"name": "Basic Mathematics", "category": "Quantitative Techniques", "description": "Arithmetic, algebra, and geometry"},
        {"name": "Data Interpretation", "category": "Quantitative Techniques", "description": "Charts, graphs, and statistical data analysis"},
        {"name": "Percentages", "category": "Quantitative Techniques", "description": "Percentage calculations and applications"},
    ]
    
    for topic_data in clat_topics:
        topic = Topic(**topic_data)
        db.add(topic)
    
    db.commit()
    print(f"Added {len(clat_topics)} topics to the database.")

