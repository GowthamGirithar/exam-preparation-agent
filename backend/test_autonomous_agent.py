"""
Test script for the Autonomous LangGraph Agent.
Tests the complete learning flow: question -> answer -> verification -> explanation.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from agents.autonomous_langgraph_agent import AutonomousLangGraphAgent

def test_complete_learning_flow():
    """Test the complete learning flow with autonomous agent."""
    print("Testing Complete Learning Flow with Autonomous Agent")
    
    # Create autonomous agent
    print("🔧 Creating autonomous agent...")
    autonomous_agent = AutonomousLangGraphAgent(
        llm_provider=Config.LLM_PROVIDER,
        llm_model=Config.LLM_MODEL,
        llm_host=Config.LLM_HOST,
        tools=[
            "english_search_document", 
            "search_web",
            "start_practice_session",
            "get_practice_question", 
            "submit_practice_answer",
            "get_learning_progress",
            "get_adaptive_question"
        ]
    )
    print("Agent created successfully!")
    print()
    
    user_id = "test_student"
    session_id = "learning_session"
    
    
    # Step 1: Ask agent to provide a grammar question
    print("Step 1: Requesting a grammar question")
    
    question_request = "Please give me a grammar question to practice for the user with id test_student"
    print(f"User: {question_request}")
    
    try:
        response1 = autonomous_agent.answer_questions(question_request, user_id, session_id)
        
        # Show what the agent decided to do
        plan1 = response1.get('plan', {})
        print(f"Agent's Plan: {plan1.get('reasoning', 'No reasoning')}")
        
        tool_results1 = response1.get('tool_results', [])
        if tool_results1:
            print(f" Tools Used: {[tr['tool_name'] for tr in tool_results1 if tr['success']]}")
        
        print()
        print("Agent's Response:")
        print(response1['output'])
        print()
        
    except Exception as e:
        print(f"❌ Error in Step 1: {e}")
        return

    
    # Step 2: Simulate user providing an answer
    print("Step 2: User provides an answer")
    
    # Simulate user answering (let's say they choose option B)
    user_answer = "user with id test_student answered that my answer is B"
    print(f"User: {user_answer}")
    
    try:
        response2 = autonomous_agent.answer_questions(user_answer, user_id, session_id)
        
        # Show what the agent decided to do
        plan2 = response2.get('plan', {})
        print(f"Agent's Plan: {plan2.get('reasoning', 'No reasoning')}")
        
        tool_results2 = response2.get('tool_results', [])
        if tool_results2:
            print(f"Tools Used: {[tr['tool_name'] for tr in tool_results2 if tr['success']]}")
        
        print()
        print("Agent's Response:")
        print(response2['output'])
        print()
        print("=" * 60)
        print()
        
    except Exception as e:
        print(f"❌ Error in Step 2: {e}")
        return
    
    '''
    
    # Step 3: Ask for explanation
    print("💡 Step 3: Requesting explanation")
    print("-" * 40)
    
    explanation_request = "Can you explain why that's the correct answer?"
    print(f"👤 User: {explanation_request}")
    
    try:
        response3 = autonomous_agent.answer_questions(explanation_request, user_id, session_id)
        
        # Show what the agent decided to do
        plan3 = response3.get('plan', {})
        print(f"🧠 Agent's Plan: {plan3.get('reasoning', 'No reasoning')}")
        
        tool_results3 = response3.get('tool_results', [])
        if tool_results3:
            print(f"🔧 Tools Used: {[tr['tool_name'] for tr in tool_results3 if tr['success']]}")
        
        print()
        print("🤖 Agent's Response:")
        print(response3['output'])
        print()
        print("=" * 60)
        print()
        
    except Exception as e:
        print(f"❌ Error in Step 3: {e}")
        return
    
    # Step 4: Check learning progress
    print("📊 Step 4: Checking learning progress")
    print("-" * 40)
    
    progress_request = "Show me my learning progress"
    print(f"👤 User: {progress_request}")
    
    try:
        response4 = autonomous_agent.answer_questions(progress_request, user_id, session_id)
        
        # Show what the agent decided to do
        plan4 = response4.get('plan', {})
        print(f"🧠 Agent's Plan: {plan4.get('reasoning', 'No reasoning')}")
        
        tool_results4 = response4.get('tool_results', [])
        if tool_results4:
            print(f"🔧 Tools Used: {[tr['tool_name'] for tr in tool_results4 if tr['success']]}")
        
        print()
        print("🤖 Agent's Response:")
        print(response4['output'])
        print()
        
    except Exception as e:
        print(f"❌ Error in Step 4: {e}")
        return
    
    print("🎉 Complete Learning Flow Test Completed!")
    print()
    print("📝 What We Tested:")
    print("   ✅ Agent autonomously provided a practice question")
    print("   ✅ Agent processed user's answer")
    print("   ✅ Agent verified and explained the answer")
    print("   ✅ Agent tracked learning progress")
    print("   ✅ All decisions were made autonomously by the LLM")
    print("   ✅ Each step was debuggable with clear reasoning")
    '''

def test_simple_interaction():
    """Test a simple interaction to verify basic functionality."""
    print("\n🔍 Testing Simple Interaction")
    print("=" * 40)
    
    autonomous_agent = AutonomousLangGraphAgent(
        llm_provider=Config.LLM_PROVIDER,
        llm_model=Config.LLM_MODEL,
        llm_host=Config.LLM_HOST,
        tools=["get_practice_question", "submit_practice_answer"]
    )
    
    simple_question = "Give me a practice question"
    print(f"👤 User: {simple_question}")
    
    try:
        response = autonomous_agent.answer_questions(simple_question, "simple_test", "simple_session")
        
        print(f"🧠 Agent's Reasoning: {response.get('plan', {}).get('reasoning', 'No reasoning')}")
        print(f"🔧 Tools Used: {len(response.get('tool_results', []))} tools")
        print()
        print("🤖 Agent's Response:")
        print(response['output'])
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run the complete test suite."""
    
    # Test configuration
    print(f"📋 Configuration:")
    print(f"   - LLM Provider: {Config.LLM_PROVIDER}")
    print(f"   - LLM Model: {Config.LLM_MODEL}")
    print(f"   - Tool Schema Validation: {Config.TOOL_SCHEMA_VALIDATION}")
    print()
    
    # Run simple test first
    # test_simple_interaction()
    
    print("\n" + "="*60 + "\n")
    
    # Run complete learning flow test
    test_complete_learning_flow()

if __name__ == "__main__":
    main()