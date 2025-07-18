#!/usr/bin/env python3
"""
Comprehensive test suite for the Interactive Learning Agent.

This tests the complete learning workflow:
1. Agent initialization and capabilities
2. Learning session management
3. Question generation and answering
4. Performance tracking and analytics
5. Topic explanations
6. API endpoints integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.interactive_learning_agent import InteractiveLearningAgent
from database.init_db import init_database
from config import Config
import json


def test_interactive_learning_agent():
    """Test the complete Interactive Learning Agent workflow."""
    
    
    # Initialize database
    print("📊 Initializing database...")
    init_database()
    print("✅ Database initialized")
    
    # Initialize agent
    try:
        agent = InteractiveLearningAgent(
            llm_provider=Config.LLM_PROVIDER,
            llm_model=Config.LLM_MODEL,
            llm_host=Config.LLM_HOST,
            tools=["english_search_document", "search_web", "start_practice_session", "get_practice_question", "submit_practice_answer", "get_learning_progress"]
        )
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return
    
    # Test user and session
    test_user_id = "999"
    test_session_id = "test_session_123"
    
    print(f"\n👤 Testing with User ID: {test_user_id} and session id {test_session_id}")

    #  Start practice session
    print("TEST 2: Start Practice Session \n")
    
    
    '''
    try:
        response = agent.answer_questions("start practice Grammar", test_user_id, test_session_id)
        print(response.get('output', response))
    except Exception as e:
        print(f"❌ Practice session test failed: {e}")
    '''   
    
    # Test 3: Get specific question
    print("TEST 3: Get Specific Question \n")
    
    try:
        response = agent.answer_questions("get me question Grammar easy", test_user_id, test_session_id)
        print(response.get('output', response))
    except Exception as e:
        print(f"❌ Specific question test failed: {e}")
    
    # Test 4: Submit answers
    print("TEST 4: Submit Answers\n")
    
    answers = ['A', 'B', 'C', 'A']  # Mix of correct/incorrect
    for i, answer in enumerate(answers, 1):
        try:
            response = agent.answer_questions(f"answer {answer}", test_user_id, test_session_id)
            print(response.get('output', response))
        except Exception as e:
            print(f"❌ Answer {i} submission failed: {e}")
    
    # Test 5: Check progress
    print("TEST 5: User Progress Analytics\n")

    
    try:
        response = agent.answer_questions("my progress", test_user_id, test_session_id)
        print(response.get('output', response))
    except Exception as e:
        print(f"❌ Progress analytics test failed: {e}")
    
    # Test 6: Topic explanation
    print("TEST 6: Topic Explanation\n")
    
    try:
        response = agent.answer_questions("explain Grammar", test_user_id, test_session_id)
        print(response.get('output', response))
    except Exception as e:
        print(f"❌ Topic explanation test failed: {e}")
    
    # Test 7: Regular agent functionality
    print("TEST 7: Regular Agent Functionality\n")
    
    try:
        response = agent.answer_questions("What is the difference between tort and contract law?", test_user_id, test_session_id)
        print(response.get('output', response))
    except Exception as e:
        print(f"❌ Regular agent functionality test failed: {e}")
    
    # Test 8: End session
    print("TEST 8: End Learning Session\n")
    
    try:
        response = agent.answer_questions("end session", test_user_id, test_session_id)
        print(response.get('output', response))
    except Exception as e:
        print(f"❌ End session test failed: {e}")
    
    


if __name__ == "__main__":
    # Run the comprehensive test
    test_interactive_learning_agent()
    
