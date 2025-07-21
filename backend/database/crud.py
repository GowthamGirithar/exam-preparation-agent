"""
CRUD operations for the Law Exam Learning System.

This module provides convenient functions for:
- User management
- Session tracking
- Performance analytics
- Learning progress monitoring
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database.models import User, Topic, LearningSession, UserAnswer, UserPerformance, WeaknessAnalysis
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid


# User Operations
def create_user(db: Session, name: str, email: str, **kwargs) -> User:
    """Create a new user."""
    user = User(name=name, email=email, **kwargs)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


# Topic Operations
def get_topics(db: Session, category: Optional[str] = None) -> List[Topic]:
    """Get all topics, optionally filtered by category."""
    query = db.query(Topic).filter(Topic.is_active == True)
    if category:
        query = query.filter(Topic.category == category)
    return query.all()


def get_topic_by_name(db: Session, name: str) -> Optional[Topic]:
    """Get topic by name."""
    return db.query(Topic).filter(Topic.name == name).first()


# Learning Session Operations
def create_learning_session(
    db: Session, 
    user_id: int, 
    session_type: str,
    target_questions: int = 10,
    difficulty_preference: Optional[str] = None,
    topic_focus: Optional[List[str]] = None
) -> LearningSession:
    """Create a new learning session."""
    session = LearningSession(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        session_type=session_type,
        target_questions=target_questions,
        difficulty_preference=difficulty_preference,
        topic_focus=topic_focus
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_active_session(db: Session, user_id: int) -> Optional[LearningSession]:
    """Get user's active (incomplete) session."""
    return db.query(LearningSession).filter(
        LearningSession.user_id == user_id,
        LearningSession.is_completed == False
    ).first()


def complete_session(db: Session, session_id: int) -> LearningSession:
    """Mark a session as completed and update metrics."""
    session = db.query(LearningSession).filter(LearningSession.id == session_id).first()
    if session:
        session.is_completed = True
        session.ended_at = datetime.utcnow()
        
        # Calculate completion percentage
        if session.target_questions > 0:
            session.completion_percentage = (session.questions_attempted / session.target_questions) * 100
        
        # Calculate average time per question
        if session.questions_attempted > 0:
            session.average_time_per_question = session.total_time_spent / session.questions_attempted
        
        db.commit()
        db.refresh(session)
    return session


# User Answer Operations
def record_user_answer(
    db: Session,
    session_id: int,
    user_id: int,
    question_id: str,
    topic_name: str,
    question_text: str,
    user_answer: str,
    correct_answer: str,
    time_taken: float,
    difficulty: str = "medium",
    **kwargs
) -> UserAnswer:
    """Record a user's answer to a question."""
    answer = UserAnswer(
        session_id=session_id,
        user_id=user_id,
        question_id=question_id,
        topic_name=topic_name,
        question_text=question_text,
        user_answer=user_answer,
        correct_answer=correct_answer,
        is_correct=(user_answer.upper() == correct_answer.upper()),
        time_taken=time_taken,
        difficulty=difficulty,
        **kwargs
    )
    
    db.add(answer)
    
    # Update session metrics
    session = db.query(LearningSession).filter(LearningSession.id == session_id).first()
    if session:
        session.questions_attempted += 1
        session.total_time_spent += time_taken
        if answer.is_correct:
            session.questions_correct += 1
    
    db.commit()
    db.refresh(answer)
    
    # Update user performance asynchronously
    update_user_performance(db, user_id, topic_name, answer.is_correct, time_taken)
    
    return answer


# Performance Analytics
def get_user_performance(db: Session, user_id: int, topic_name: Optional[str] = None) -> List[UserPerformance]:
    """Get user performance data, optionally filtered by topic."""
    query = db.query(UserPerformance).filter(UserPerformance.user_id == user_id)
    
    if topic_name:
        topic = get_topic_by_name(db, topic_name)
        if topic:
            query = query.filter(UserPerformance.topic_id == topic.id)
    
    return query.all()


def update_user_performance(db: Session, user_id: int, topic_name: str, is_correct: bool, time_taken: float):
    """Update user performance metrics for a topic."""
    topic = get_topic_by_name(db, topic_name)
    if not topic:
        return
    
    # Get or create performance record
    performance = db.query(UserPerformance).filter(
        UserPerformance.user_id == user_id,
        UserPerformance.topic_id == topic.id
    ).first()
    
    if not performance:
        performance = UserPerformance(
            user_id=user_id,
            topic_id=topic.id,
            total_questions=0,
            correct_answers=0,
            total_time_spent=0.0
        )
        db.add(performance)
    
    # Update metrics
    performance.total_questions += 1
    performance.total_time_spent += time_taken
    performance.last_practiced = datetime.utcnow()
    
    if is_correct:
        performance.correct_answers += 1
    
    # Calculate derived metrics
    performance.accuracy_percentage = (performance.correct_answers / performance.total_questions) * 100
    performance.average_time_per_question = performance.total_time_spent / performance.total_questions
    
    # Calculate weakness score (higher = weaker)
    performance.weakness_score = 1.0 - (performance.accuracy_percentage / 100.0)
    
    # Calculate mastery level (0-1 scale)
    performance.mastery_level = min(performance.accuracy_percentage / 100.0, 1.0)
    
    db.commit()


def get_user_weaknesses(db: Session, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """Get user's weakest topics for adaptive learning."""
    performances = db.query(UserPerformance).filter(
        UserPerformance.user_id == user_id,
        UserPerformance.total_questions >= 1  # Minimum questions for reliable data
    ).order_by(desc(UserPerformance.weakness_score)).limit(limit).all()
    
    weaknesses = []
    for perf in performances:
        topic = db.query(Topic).filter(Topic.id == perf.topic_id).first()
        if topic:
            weaknesses.append({
                "topic_name": topic.name,
                "category": topic.category,
                "weakness_score": perf.weakness_score,
                "accuracy": perf.accuracy_percentage,
                "total_questions": perf.total_questions,
                "last_practiced": perf.last_practiced
            })
    
    return weaknesses


def get_session_summary(db: Session, session_id: int) -> Dict[str, Any]:
    """Get comprehensive session summary."""
    session = db.query(LearningSession).filter(LearningSession.id == session_id).first()
    if not session:
        return {}
    
    # Get all answers for this session
    answers = db.query(UserAnswer).filter(UserAnswer.session_id == session_id).all()
    
    # Calculate topic-wise performance
    topic_performance = {}
    for answer in answers:
        if answer.topic_name not in topic_performance:
            topic_performance[answer.topic_name] = {
                "total": 0,
                "correct": 0,
                "total_time": 0.0
            }
        
        topic_performance[answer.topic_name]["total"] += 1
        topic_performance[answer.topic_name]["total_time"] += answer.time_taken
        if answer.is_correct:
            topic_performance[answer.topic_name]["correct"] += 1
    
    # Calculate accuracy per topic
    for topic in topic_performance:
        perf = topic_performance[topic]
        perf["accuracy"] = (perf["correct"] / perf["total"]) * 100 if perf["total"] > 0 else 0
        perf["avg_time"] = perf["total_time"] / perf["total"] if perf["total"] > 0 else 0
    
    return {
        "session": {
            "id": session.id,
            "session_id": session.session_id,
            "type": session.session_type,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "is_completed": session.is_completed
        },
        "performance": {
            "questions_attempted": session.questions_attempted,
            "questions_correct": session.questions_correct,
            "accuracy": (session.questions_correct / session.questions_attempted * 100) if session.questions_attempted > 0 else 0,
            "total_time": session.total_time_spent,
            "avg_time_per_question": session.average_time_per_question
        },
        "topic_breakdown": topic_performance,
        "answers": [
            {
                "question_id": answer.question_id,
                "topic": answer.topic_name,
                "user_answer": answer.user_answer,
                "correct_answer": answer.correct_answer,
                "is_correct": answer.is_correct,
                "time_taken": answer.time_taken,
                "difficulty": answer.difficulty
            }
            for answer in answers
        ]
    }


def get_user_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """Get comprehensive user statistics."""
    user = get_user(db, user_id)
    if not user:
        return {}
    
    # Get all sessions
    total_sessions = db.query(LearningSession).filter(LearningSession.user_id == user_id).count()
    completed_sessions = db.query(LearningSession).filter(
        LearningSession.user_id == user_id,
        LearningSession.is_completed == True
    ).count()
    
    # Get all answers
    total_answers = db.query(UserAnswer).filter(UserAnswer.user_id == user_id).count()
    correct_answers = db.query(UserAnswer).filter(
        UserAnswer.user_id == user_id,
        UserAnswer.is_correct == True
    ).count()
    
    # Get performance by category
    category_performance = db.query(
        Topic.category,
        func.sum(UserPerformance.total_questions).label('total'),
        func.sum(UserPerformance.correct_answers).label('correct')
    ).join(UserPerformance).filter(
        UserPerformance.user_id == user_id
    ).group_by(Topic.category).all()
    
    category_stats = {}
    for cat, total, correct in category_performance:
        category_stats[cat] = {
            "total_questions": total or 0,
            "correct_answers": correct or 0,
            "accuracy": (correct / total * 100) if total and total > 0 else 0
        }
    
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
            "last_active": user.last_active
        },
        "overall_stats": {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "total_questions": total_answers,
            "correct_answers": correct_answers,
            "overall_accuracy": (correct_answers / total_answers * 100) if total_answers > 0 else 0
        },
        "category_performance": category_stats,
        "weaknesses": get_user_weaknesses(db, user_id)
    }