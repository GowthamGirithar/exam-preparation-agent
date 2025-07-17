"""
Test script to verify database operations work correctly.

This script tests:
- Database connection
- CRUD operations
- Performance tracking
- Session management
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import SessionLocal
from database.crud import *
from database.models import *


def test_database_operations():
    """Test all database operations."""
    print("🧪 Testing Database Operations...")
    
    db = SessionLocal()
    try:
        # Test 1: Get existing user
        print("\n1. Testing user operations...")
        user = get_user(db, 1)
        if user:
            print(f"✅ Found user: {user.name} ({user.email})")
        else:
            print("❌ No user found")
            return
        
        # Test 2: Get topics
        print("\n2. Testing topic operations...")
        topics = get_topics(db)
        print(f"✅ Found {len(topics)} topics")
        
        english_topics = get_topics(db, category="English")
        print(f"✅ Found {len(english_topics)} English topics")
        
        # Test 3: Create learning session
        print("\n3. Testing session creation...")
        session = create_learning_session(
            db=db,
            user_id=user.id,
            session_type="practice",
            target_questions=5,
            difficulty_preference="medium",
            topic_focus=["Grammar", "Vocabulary"]
        )
        print(f"✅ Created session: {session.session_id}")
        
        # Test 4: Record some answers
        print("\n4. Testing answer recording...")
        sample_answers = [
            {
                "question_id": "q1",
                "topic_name": "Grammar",
                "question_text": "Choose the correct sentence:",
                "user_answer": "C",
                "correct_answer": "C",
                "time_taken": 15.5,
                "difficulty": "easy"
            },
            {
                "question_id": "q2", 
                "topic_name": "Vocabulary",
                "question_text": "What is the synonym of 'happy'?",
                "user_answer": "B",
                "correct_answer": "A",
                "time_taken": 22.3,
                "difficulty": "medium"
            },
            {
                "question_id": "q3",
                "topic_name": "Grammar",
                "question_text": "Identify the error:",
                "user_answer": "A",
                "correct_answer": "A",
                "time_taken": 18.7,
                "difficulty": "medium"
            }
        ]
        
        for answer_data in sample_answers:
            answer = record_user_answer(
                db=db,
                session_id=session.id,
                user_id=user.id,
                **answer_data
            )
            status = "✅ Correct" if answer.is_correct else "❌ Wrong"
            print(f"  {status} - {answer.topic_name}: {answer.time_taken}s")
        
        # Test 5: Complete session
        print("\n5. Testing session completion...")
        completed_session = complete_session(db, session.id)
        print(f"✅ Session completed: {completed_session.completion_percentage:.1f}% complete")
        print(f"   Accuracy: {completed_session.questions_correct}/{completed_session.questions_attempted}")
        
        # Test 6: Get performance data
        print("\n6. Testing performance analytics...")
        performance = get_user_performance(db, user.id)
        print(f"✅ Found performance data for {len(performance)} topics:")
        for perf in performance:
            topic = db.query(Topic).filter(Topic.id == perf.topic_id).first()
            print(f"   {topic.name}: {perf.accuracy_percentage:.1f}% accuracy ({perf.total_questions} questions)")
        
        # Test 7: Get weaknesses
        print("\n7. Testing weakness analysis...")
        weaknesses = get_user_weaknesses(db, user.id)
        if weaknesses:
            print(f"✅ Found {len(weaknesses)} weak areas:")
            for weakness in weaknesses:
                print(f"   {weakness['topic_name']}: {weakness['accuracy']:.1f}% accuracy")
        else:
            print("ℹ️  No weaknesses found (need more data)")
        
        # Test 8: Get session summary
        print("\n8. Testing session summary...")
        summary = get_session_summary(db, session.id)
        print(f"✅ Session summary generated:")
        print(f"   Questions: {summary['performance']['questions_attempted']}")
        print(f"   Accuracy: {summary['performance']['accuracy']:.1f}%")
        print(f"   Topics covered: {len(summary['topic_breakdown'])}")
        
        # Test 9: Get user stats
        print("\n9. Testing user statistics...")
        stats = get_user_stats(db, user.id)
        print(f"✅ User stats generated:")
        print(f"   Total sessions: {stats['overall_stats']['total_sessions']}")
        print(f"   Overall accuracy: {stats['overall_stats']['overall_accuracy']:.1f}%")
        print(f"   Categories practiced: {len(stats['category_performance'])}")
        
        print("\n🎉 All database tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_database_operations()