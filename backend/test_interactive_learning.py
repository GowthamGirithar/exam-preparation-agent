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

from dotenv import load_dotenv
load_dotenv()

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
    
    print("\n🎯 Starting Interactive 5-Question Practice Session")
    # Test user and session
    test_user_id = "1"
    test_session_id = "test_session_123"
    # Start the session
    try:
        response = agent.answer_questions("start practice Grammar with 5 questions", test_user_id, test_session_id)
        print(f"🟢 Session Started: {response.get('output', response)}")
    except Exception as e:
        print(f"❌ Failed to start practice session: {e}")
        exit(1)

    # Now go into the Q&A loop
    MAX_QUESTIONS = 5
    question_number = 0
    answers = ['A', 'B', 'C', 'D', 'A']  # Simulated choices

    while question_number < MAX_QUESTIONS:
        try:
            # Submit answer
            answer = answers[question_number]
            print(f"\n📝 Submitting Answer {question_number + 1}: {answer}")
            response = agent.answer_questions(f"answer {answer}", test_user_id, test_session_id)

            output = response.get('output', response)
            print(f"📩 Agent Response: {output}")

            # Check if session is complete (agent may say so in the response)
            if "session complete" in str(output).lower() or "you've completed" in str(output).lower():
                print("✅ Session ended by agent.")
                break

            question_number += 1

        except Exception as e:
            print(f"❌ Error during question {question_number + 1}: {e}")
            break

        # Check progress
    print("\n📊 Checking User Progress")
    try:
        response = agent.answer_questions("my progress", test_user_id, test_session_id)
        print(f"📈 Progress: {response.get('output', response)}")
    except Exception as e:
        print(f"❌ Could not retrieve progress: {e}")

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
    
