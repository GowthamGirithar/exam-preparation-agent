from config import Config
import os


def get_agent():
    if Config.AGENT_NAME == "LawExamAgent":
        from agents.law_exam_agent import LawExamAgent
        '''
        example:
        law_agent = LawExamAgent(llm_provider="ollama", llm_model="llama3", llm_host="http://localhost:11434")

        response =law_agent.answer_questions("Give me sample question from CLAT last exam in English and Comprehension with answer")
        for chunk in response:
            print(chunk, end="", flush=True) # python command to flush immediately from buffer

        '''
        return LawExamAgent(llm_provider=Config.LLM_PROVIDER, llm_model=Config.LLM_MODEL)
    elif Config.AGENT_NAME == "DynamicLawAgent":
        from agents.dynamic_law_exam_agent import DynamicLawExamAgent
        '''
        example:

        law_agent_dynamic = DynamicLawExamAgent(llm_provider="ollama", llm_model="llama3", llm_host="http://localhost:11434", tools=["search_document"])

        response =law_agent_dynamic.answer_questions("what is microservice in 2 sentence")
        for chunk in response:
            print(chunk, end="", flush=True) # python command to flush immediately from buffer

        '''
        return DynamicLawExamAgent(llm_provider=Config.LLM_PROVIDER, llm_model=Config.LLM_MODEL, llm_host=Config.LLM_HOST, tools=["search_document"])
    elif Config.AGENT_NAME == "ModernDynamicLawAgent":
        from agents.modern_dynamic_law_agent import ModernDynamicLawAgent
        '''

        example 

        law_agent_dynamic = ModernDynamicLawAgent(llm_provider="ollama", llm_model="llama3", llm_host="http://localhost:11434", tools=["english_search_document", "search_web"])

        response =law_agent_dynamic.answer_questions("current president of Germany")
        for chunk in response:
            print(chunk, end="", flush=True) # python command to flush immediately from buffer
 
        
        '''
        return ModernDynamicLawAgent(llm_provider=Config.LLM_PROVIDER, llm_model=Config.LLM_MODEL, llm_host=Config.LLM_HOST, tools=["english_search_document", "search_web"])
    elif Config.AGENT_NAME == "ModernDynamicLawAgentWithSessionMemory":
        from agents.modern_dynamic_law_agent_session_memory import ModernDynamicLawAgentWithSessionMemory

        '''
        
        law_agent_dynamic = ModernDynamicLawAgentWithSessionMemory(llm_provider="ollama", llm_model="llama3", llm_host="http://localhost:11434", tools=["english_search_document", "search_web"])

        # First question
        print("=== First Question ===")
        response = law_agent_dynamic.answer_questions("current president of Germany", 12, "user_session_123")
        print("Response:", response.get('output', response))
        print()

        # Second question - testing memory
        print("=== Second Question (Testing Memory) ===")
        response = law_agent_dynamic.answer_questions("what did I ask before", 12, "user_session_123")
        print("Response:", response.get('output', response))
        print()

        # Check chat history
        print("=== Chat History ===")
        print("Chat history:", response.get('chat_history', []))
        
        
        
        '''
        return ModernDynamicLawAgentWithSessionMemory(llm_provider=Config.LLM_PROVIDER, llm_model= Config.LLM_MODEL,llm_host=Config.LLM_HOST, tools=["english_search_document", "search_web"])
    elif Config.AGENT_NAME == "InteractiveLearningAgent":
        from agents.interactive_learning_agent import InteractiveLearningAgent
        
        '''
        Interactive Learning Agent with adaptive question generation and performance tracking.
        
        Features:
        - All existing agent capabilities (document search, web search, session memory)
        - Adaptive question generation from PDF content
        - Performance tracking and analytics
        - Learning session management
        - Topic explanations
        
        Example usage:
        
        learning_agent = InteractiveLearningAgent(
            llm_provider="ollama",
            llm_model="llama3",
            llm_host="http://localhost:11434",
            tools=["english_search_document", "search_web"]
        )
        
        # Start practice session
        response = learning_agent.answer_questions("start practice Grammar", "123", "session_1")
        print("Response:", response.get('output'))
        
        # Submit answer
        response = learning_agent.answer_questions("answer A", "123", "session_1")
        print("Response:", response.get('output'))
        
        # Check progress
        response = learning_agent.answer_questions("my progress", "123", "session_1")
        print("Response:", response.get('output'))
        
        # Regular question (uses existing tools)
        response = learning_agent.answer_questions("What is contract law?", "123", "session_1")
        print("Response:", response.get('output'))
        '''
        return InteractiveLearningAgent(
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
    elif Config.AGENT_NAME == "AutonomousLangGraphAgent":
        from agents.autonomous_langgraph_agent import AutonomousLangGraphAgent
        
        '''
        Fully autonomous LangGraph agent with debuggable architecture.
        
        Architecture:
        - Planner: LLM decides what tools to use and why (fully logged)
        - Executor: Executes planned tools with detailed logging
        - Responder: Generates final response based on results
        
        Benefits:
        - Easy to debug with explicit logging at each step
        - Clear separation of concerns
        - Full control over each phase
        - Autonomous tool selection by LLM
        - Detailed debug information in response
        
        Example usage:
        
        autonomous_agent = AutonomousLangGraphAgent(
            llm_provider="ollama",
            llm_model="llama3",
            llm_host="http://localhost:11434",
            tools=["english_search_document", "search_web"]
        )
        
        # The agent autonomously decides what to do
        response = autonomous_agent.answer_questions("start practice Grammar", "123", "session_1")
        print("Response:", response.get('output'))
        print("Plan:", response.get('plan'))  # See what the planner decided
        print("Tools used:", response.get('tool_results'))  # See execution details
        print("Debug info:", response.get('debug_info'))  # Full debug information
        '''
        return AutonomousLangGraphAgent(
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
    else:
        raise ValueError(f"Unknown agent name: {Config.AGENT_NAME}")
