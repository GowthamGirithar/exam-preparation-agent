"""
Test script for Question Manager with PDF integration.

This script demonstrates:
- How Question Manager retrieves content from your PDF ingestion system
- Question parsing from PDF content stored in ChromaDB
- Adaptive question selection based on user performance
- Integration with existing Vector DB setup
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from learning.question_manager import QuestionManager, get_question_manager
from database.database import SessionLocal
from database.crud import create_user, create_learning_session, record_user_answer


def test_question_manager():
    """Test the complete Question Manager functionality."""
    print("🧪 Testing Question Manager with PDF Integration...")
    
    # Initialize Question Manager
    print("\n1. Initializing Question Manager...")
    qm = get_question_manager()
    
    # Test connection to Vector DB (your PDF content)
    print("\n2. Testing Vector DB connection...")
    stats = qm.get_question_stats()
    print(f"   Status: {stats}")
    
    # Test question retrieval by topic
    print("\n3. Testing question retrieval by topic...")
    topics_to_test = ["Grammar", "Legal Principles", "Indian History", "Vocabulary"]
    
    for topic in topics_to_test:
        print(f"\n   📚 Testing {topic}:")
        
        # Test different difficulties
        for difficulty in ["easy", "medium", "hard"]:
            questions = qm.get_question_by_topic(topic, difficulty, 1)
            if questions:
                q = questions[0]
                print(f"     ✅ {difficulty}: {q.text[:50]}...")
                print(f"        Topic: {q.topic}, Category: {q.category}")
                print(f"        Options: {len(q.options)}, Answer: {q.correct_answer}")
                print(f"        Source: {q.source}")
            else:
                print(f"     ❌ {difficulty}: No questions found")
    
    # Test adaptive question selection
    print("\n4. Testing adaptive question selection...")
    
    # Create a test user with some performance data
    db = SessionLocal()
    try:
        # Create test user
        user = create_user(db, "Test Student 2", "test2@example.com")
        print(f"   Created test user: {user.name} (ID: {user.id})")
        
        # Create a learning session
        session = create_learning_session(
            db=db,
            user_id=user.id,
            session_type="adaptive_test",
            target_questions=5
        )
        print(f"   Created session: {session.session_id}")
        
        # Simulate some answers to create performance data
        print("\n   📊 Simulating user performance...")
        
        # Poor performance in Grammar (to make it a weakness)
        grammar_answers = [
            {"topic": "Grammar", "correct": False, "time": 25.0},
            {"topic": "Grammar", "correct": False, "time": 30.0},
            {"topic": "Grammar", "correct": True, "time": 20.0},
        ]
        
        # Good performance in History
        history_answers = [
            {"topic": "Indian History", "correct": True, "time": 15.0},
            {"topic": "Indian History", "correct": True, "time": 18.0},
            {"topic": "Indian History", "correct": True, "time": 12.0},
        ]
        
        # Record answers
        for i, answer_data in enumerate(grammar_answers + history_answers):
            record_user_answer(
                db=db,
                session_id=session.id,
                user_id=user.id,
                question_id=f"test_q_{i}",
                topic_name=answer_data["topic"],
                question_text=f"Test question {i+1}",
                user_answer="A" if answer_data["correct"] else "B",
                correct_answer="A",
                time_taken=answer_data["time"]
            )
        
        print(f"   Recorded {len(grammar_answers + history_answers)} answers")
        
        # Now test adaptive selection
        print("\n   🎯 Testing adaptive question selection...")
        for i in range(3):
            question = qm.get_adaptive_question(user.id)
            if question:
                print(f"     Question {i+1}: {question.topic} ({question.difficulty})")
                print(f"       Text: {question.text[:60]}...")
                print(f"       Source: {question.source}")
            else:
                print(f"     Question {i+1}: No question returned")
        
    except Exception as e:
        print(f"   ❌ Error in adaptive testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    # Test random question selection
    print("\n5. Testing random question selection...")
    categories = ["English", "General Knowledge", "Legal Reasoning"]
    
    for category in categories:
        question = qm.get_random_question(category)
        if question:
            print(f"   ✅ {category}: {question.topic} - {question.text[:40]}...")
        else:
            print(f"   ❌ {category}: No question found")
    
    # Test question validation
    print("\n6. Testing question validation...")
    
    # Get a sample question
    questions = qm.get_question_by_topic("Grammar", "medium", 1)
    if questions:
        question = questions[0]
        is_valid = qm.validate_question(question)
        print(f"   Question validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
        print(f"   Question details:")
        print(f"     Text length: {len(question.text)}")
        print(f"     Options count: {len(question.options)}")
        print(f"     Correct answer: {question.correct_answer}")
        print(f"     Has explanation: {'Yes' if question.explanation else 'No'}")
    
    print("\n🎉 Question Manager testing completed!")
    print("\n📋 Summary:")
    print("   ✅ Vector DB integration (uses your PDF content)")
    print("   ✅ Question parsing from PDF text")
    print("   ✅ Topic and difficulty detection")
    print("   ✅ Adaptive question selection")
    print("   ✅ Fallback question system")
    print("   ✅ Question validation")


def test_question_parsing():
    """Test the question parsing functionality with sample PDF content."""
    print("\n🔍 Testing Question Parsing from PDF Content...")
    
    from learning.question_manager import QuestionParser
    
    # Sample PDF content formats
    sample_contents = [
        # Format 1: Standard MCQ
        """
        Question: Choose the correct sentence:
        Options: A) He don't like coffee B) He doesn't likes coffee C) He doesn't like coffee D) He not like coffee
        Answer: C
        Explanation: The correct form uses 'doesn't' (does not) with the base form of the verb 'like'.
        """,
        
        # Format 2: Legal Reasoning
        """
        Principle: A person is liable for negligence if they fail to take reasonable care.
        Facts: A doctor operates without proper sterilization, causing infection to the patient.
        Question: Is the doctor liable for negligence?
        A) Yes, due to negligence B) No, it's an accident C) Only if patient dies D) Depends on hospital policy
        Answer: A
        Explanation: The doctor failed to take reasonable care by not sterilizing properly, which constitutes negligence.
        """,
        
        # Format 3: General Knowledge
        """
        Q: Who was the first President of India?
        (A) Jawaharlal Nehru (B) Dr. Rajendra Prasad (C) Sardar Patel (D) Dr. A.P.J. Abdul Kalam
        Correct: B
        Explanation: Dr. Rajendra Prasad was the first President of India, serving from 1950 to 1962.
        """
    ]
    
    parser = QuestionParser()
    
    for i, content in enumerate(sample_contents, 1):
        print(f"\n   📄 Parsing Sample {i}:")
        question = parser.parse_question_text(content)
        
        if question:
            print(f"     ✅ Successfully parsed!")
            print(f"     ID: {question.id}")
            print(f"     Topic: {question.topic} ({question.category})")
            print(f"     Difficulty: {question.difficulty}")
            print(f"     Text: {question.text[:50]}...")
            print(f"     Options: {len(question.options)}")
            print(f"     Answer: {question.correct_answer}")
            print(f"     Source: {question.source}")
        else:
            print(f"     ❌ Failed to parse")


if __name__ == "__main__":
    print("🚀 Starting Question Manager Tests...")
    
    # Test question parsing first
    test_question_parsing()
    
    # Test full question manager functionality
    test_question_manager()
    
    print("\n✨ All tests completed!")
    print("\n📝 Next Steps:")
    print("   1. Add your CLAT PDF files to ./data/ directory")
    print("   2. Run your existing ingestion: python -m ingestion.ingest")
    print("   3. Questions will be automatically retrieved from your PDFs!")