"""
SQLAlchemy models for the Law Exam Learning System.

This module defines the database schema for:
- User management and profiles  
- CLAT topics and categories (for performance tracking)
- Learning sessions and tracking
- User performance and analytics

Note: Questions are stored in Vector DB (ChromaDB), not here.
This DB is only for performance tracking and user analytics.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
from datetime import datetime
from typing import Optional, Dict, Any


class User(Base):
    """
    User model for storing student information and preferences.
    
    Tracks basic user data and learning preferences for personalized experience.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)  # Primary key user ID
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Learning preferences
    preferred_difficulty = Column(String(20), default="medium")  # easy, medium, hard
    target_exam_date = Column(DateTime(timezone=True))
    daily_question_goal = Column(Integer, default=10)
    
    # Relationships
    sessions = relationship("LearningSession", back_populates="user", cascade="all, delete-orphan")
    answers = relationship("UserAnswer", back_populates="user", cascade="all, delete-orphan")
    performance = relationship("UserPerformance", back_populates="user", cascade="all, delete-orphan")


class Topic(Base):
    """
    Topic model for CLAT exam subjects and subtopics.
    
    Used for performance tracking and analytics.
    Maps to topics in vector DB content.
    """
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # English, GK, Legal Reasoning, etc.
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    performance = relationship("UserPerformance", back_populates="topic", cascade="all, delete-orphan")


class LearningSession(Base):
    """
    Learning session model for tracking practice sessions.
    
    Records complete learning sessions with performance metrics.
    """
    __tablename__ = "learning_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session metadata
    session_type = Column(String(50), nullable=False)  # practice, weak_topics, mixed, explanation
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    
    # Session configuration
    target_questions = Column(Integer, default=10)
    difficulty_preference = Column(String(20))
    topic_focus = Column(JSON)  # List of topic names to focus on
    
    # Performance metrics
    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    total_time_spent = Column(Float, default=0.0)  # in seconds
    average_time_per_question = Column(Float, default=0.0)
    
    # Session status
    is_completed = Column(Boolean, default=False)
    completion_percentage = Column(Float, default=0.0)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    answers = relationship("UserAnswer", back_populates="session", cascade="all, delete-orphan")


class UserAnswer(Base):
    """
    User answer model for tracking individual question responses.
    
    Records detailed information about each question attempt for analytics.
    Note: question_content is stored here since questions are in Vector DB.
    """
    __tablename__ = "user_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("learning_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Question identification (from Vector DB)
    question_id = Column(String(100), nullable=False)  # Vector DB document ID
    topic_name = Column(String(100), nullable=False)  # Topic for performance tracking
    question_text = Column(Text, nullable=False)  # Store question for reference
    
    # Answer details
    user_answer = Column(String(10), nullable=False)  # A, B, C, D, etc.
    correct_answer = Column(String(10), nullable=False)  # A, B, C, D, etc.
    is_correct = Column(Boolean, nullable=False)
    time_taken = Column(Float, nullable=False)  # in seconds
    confidence_level = Column(Integer)  # 1-5 scale (optional)
    
    # Metadata
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    attempt_number = Column(Integer, default=1)  # For retry scenarios
    
    # Additional context
    hints_used = Column(Integer, default=0)
    explanation_viewed = Column(Boolean, default=False)
    difficulty = Column(String(20))  # easy, medium, hard
    
    # Relationships
    user = relationship("User", back_populates="answers")
    session = relationship("LearningSession", back_populates="answers")


class UserPerformance(Base):
    """
    User performance model for aggregated analytics by topic.
    
    Maintains running statistics for adaptive learning algorithms.
    """
    __tablename__ = "user_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    
    # Performance metrics
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    accuracy_percentage = Column(Float, default=0.0)
    
    # Time analytics
    total_time_spent = Column(Float, default=0.0)  # in seconds
    average_time_per_question = Column(Float, default=0.0)
    
    # Learning progress
    current_difficulty = Column(String(20), default="medium")
    mastery_level = Column(Float, default=0.0)  # 0-1 scale
    weakness_score = Column(Float, default=0.5)  # 0-1 scale (higher = weaker)
    
    # Session tracking
    last_practiced = Column(DateTime(timezone=True))
    practice_streak = Column(Integer, default=0)  # consecutive days
    total_sessions = Column(Integer, default=0)
    
    # Improvement tracking
    improvement_rate = Column(Float, default=0.0)  # percentage improvement over time
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="performance")
    topic = relationship("Topic", back_populates="performance")


class WeaknessAnalysis(Base):
    """
    Weakness analysis model for tracking user's weak areas.
    
    Used by adaptive algorithm to select appropriate questions.
    """
    __tablename__ = "weakness_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Analysis data
    topic_name = Column(String(100), nullable=False)
    weakness_score = Column(Float, nullable=False)  # 0-1 scale (higher = weaker)
    confidence_score = Column(Float, default=0.5)  # 0-1 scale
    
    # Contributing factors
    recent_accuracy = Column(Float, default=0.0)  # Last 10 questions accuracy
    time_efficiency = Column(Float, default=0.0)  # Compared to average
    consistency = Column(Float, default=0.0)  # Performance consistency
    
    # Recommendations
    recommended_difficulty = Column(String(20), default="medium")
    priority_level = Column(Integer, default=1)  # 1-5 scale
    
    # Metadata
    last_analyzed = Column(DateTime(timezone=True), server_default=func.now())
    analysis_version = Column(String(20), default="1.0")
    
    # Relationships
    user = relationship("User")