from retrievers.vector_store_factory import get_vector_store
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_community.tools.google_serper.tool import GoogleSerperAPIWrapper
from config import Config
import json
import uuid
from typing import Optional


class SearchInput(BaseModel):
    query: str = Field(description="query to search for English grammar, vocabulary, comprehension passages, and language skills for CLAT exam")
    max_results: int = Field(default=5, description="maximum number of results to return")


@tool("english_search_document", args_schema=SearchInput, description="Use this tool for any learning related to English grammar, vocabulary, comprehension passages, and language skills for CLAT exam and not for practising questions")
# description of method with args is important for agent to understand this tool
def english_document_search(query: str, max_results: int = 5):
       """Search English language study materials for CLAT exam preparation.
       
       Use this tool ONLY for:
       - English grammar questions (tenses, parts of speech, sentence structure)
       - Vocabulary and word meanings
       - Reading comprehension passages and techniques
       - English language skills and rules
       
       DO NOT use for current events, general knowledge, or factual questions about people/places.
    
    Args:
        query: English language topic to search for (grammar, vocabulary, comprehension)
        max_results: the number of similar documents to return (default: 5)
    """

       try:
            vector_store = get_vector_store(provider_name=Config.VECTOR_STORE_PROVIDER,
                                                 embedding_provider=Config.EMBEDDING_PROVIDER,
                                                 embedding_model=Config.DEFAULT_EMBEDDING_MODEL,
                                                 collection_name=Config.ENGLISH_COLLECTION)
            # Pass max_results to the retriever instead of filtering afterwards
            results = vector_store.get_chroma_retriever(top_k=max_results).invoke(query)
            print(f"the length of resources is {len(results)}")
            return results
       except Exception as e:
            return str(e)

@tool("search_web", description="Search the web for current information, facts, news, and general knowledge")
def search_web(query: str) -> str:
    """Search the web for current information, facts, news, and general knowledge.
    
    Use this tool for:
    - Current events and news
    - Factual questions about people, places, organizations
    - General knowledge questions
    - Information not related to English language skills
    
    Input should be a search query string."""
    try:
        # Configure serper to get more focused results
        Config.validate()  # Ensure API key is available
        serper = GoogleSerperAPIWrapper(
            serper_api_key=Config.GOOGLE_SERPER_API_KEY,
            k=Config.SEARCH_RESULTS_LIMIT,  # Use config value
        )
        
        # Get the parsed response (this uses _parse_snippets internally)
        # serper.results(query) to see full response
        response = serper.run(query)
        print("Serper response:", response)
        print("\n")
        return response
        
    except Exception as e:
        return f"Error searching web: {str(e)}"


# ===== LEARNING TOOLS =====
# These tools enable autonomous learning functionality

# Global state for learning sessions
active_learning_sessions = {}

class PracticeSessionInput(BaseModel):
    user_id: str = Field(description="Unique identifier for the user")
    topic: Optional[str] = Field(default=None, description="Optional topic to focus on (e.g., Grammar, Legal Principles)")
    target_questions: int = Field(default=10, description="Number of questions in the session")


class AnswerInput(BaseModel):
    user_id: str = Field(description="Unique identifier for the user")
    answer: str = Field(description="User's answer (A, B, C, or D)")

class UserInput(BaseModel):
    user_id: str = Field(description="Unique identifier for the user")


@tool("start_practice_session", args_schema=PracticeSessionInput, description="Provide number of questions user asked to practice for CLAT on specific topics")
def start_practice_session(user_id: str, topic: Optional[str] = None, target_questions: int = 10) -> str:
    """Start an adaptive practice session for CLAT exam preparation.
    
    Use this tool when users want to:
    - Practice questions on specific topics
    - Start learning sessions
    - Begin adaptive practice based on their weaknesses
    
    Args:
        user_id: Unique identifier for the user
        topic: Optional topic to focus on (Grammar, Legal Principles, Indian History, etc.)
        target_questions: Number of questions in the session (default: 10)
    
    Returns:
        JSON string with session info and first question
    """
    try:
        # Import here to avoid circular imports
        from learning.question_manager import QuestionManager
        from database.crud import create_user, get_user, get_user_by_email, create_learning_session
        from database.database import get_db
        
        question_manager = QuestionManager()
        db = next(get_db())
        
        # Ensure user exists
        user = _ensure_user_exists(db, user_id)
        
        # Create learning session
        learning_session_id = str(uuid.uuid4())
        learning_session = create_learning_session(
            db, user.id, "adaptive_practice",
            target_questions=target_questions, topic_focus=topic
        )
        
        # Store session info
        active_learning_sessions[user_id] = {
            "session_id": learning_session_id,
            "db_session_id": learning_session.id,
            "current_question": None,
            "questions_asked": 0,
            "target_questions": target_questions,
            "topic_focus": topic
        }
        
        # Get first question
        if topic:
            questions = question_manager.get_question_by_topic(topic, "medium", 1)
            question = questions[0] if questions else None
        else:
            question = question_manager.get_adaptive_question(user.id)
        
        if question:
            active_learning_sessions[user_id]["current_question"] = question
            active_learning_sessions[user_id]["questions_asked"] = 1
            
            return json.dumps({
                "success": True,
                "message": f"Practice session started for {topic or 'adaptive learning'}",
                "session_info": {
                    "session_id": learning_session_id,
                    "questions_asked": 1,
                    "target_questions": target_questions,
                    "topic_focus": topic
                },
                "question": {
                    "id": question.id,
                    "text": question.text,
                    "options": question.options,
                    "topic": question.topic,
                    "difficulty": question.difficulty
                }
            })
        else:
            return json.dumps({
                "success": False,
                "message": f"No questions available for topic: {topic or 'general practice'}",
                "suggestion": "Try uploading more PDF content or choose a different topic like Grammar, Legal Principles, or Indian History"
            })
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error starting practice session: {str(e)}"
        })


# parse_docstring validates the input automatically based on the function arges mentined as comment 
@tool("get_practice_question", parse_docstring=True)
def get_practice_question(user_id: str, topic: str, difficulty: str = "medium") -> str:
    """Get a specific practice question by topic and difficulty for CLAT preparation.
    
    Use this tool when users want:
    - A question on a specific topic
    - Questions of particular difficulty level
    - To practice specific areas
    
    Args:
        user_id: Unique identifier for the user
        topic: Topic for the question (Grammar, Legal Principles, Indian History, etc.)
        difficulty: Question difficulty (easy, medium, hard)
    
    Returns:
        JSON string with question details
    """
    
    # Handle the case where entire JSON is passed as topic parameter
    # TODO: due to bug on langchain as it takes overload from ollama
    if isinstance(topic, str) and topic.strip().startswith('{'):
        try:
            # Parse the JSON that was incorrectly passed as topic
            params = json.loads(topic.strip())
            actual_topic = params.get('topic', 'Grammar')
            actual_difficulty = params.get('difficulty', 'medium')
            print(f"[DEBUG] Parsed JSON - topic: {actual_topic}, difficulty: {actual_difficulty}")
            topic = actual_topic
            difficulty = actual_difficulty
        except json.JSONDecodeError:
            print(f"[DEBUG] Failed to parse JSON, using original values")
    
    try:
        from learning.question_manager import QuestionManager
        from database.database import get_db
        
        question_manager = QuestionManager()
        db = next(get_db())
        user = _ensure_user_exists(db, user_id)
        
        questions = question_manager.get_question_by_topic(topic, difficulty, 1)
        question = questions[0] if questions else None
        
        if question:
            # Store as current question
            if user_id not in active_learning_sessions:
                active_learning_sessions[user_id] = {
                    "session_id": str(uuid.uuid4()),
                    "current_question": None,
                    "questions_asked": 0,
                    "target_questions": 1,
                    "topic_focus": topic
                }
            
            active_learning_sessions[user_id]["current_question"] = question
            
            return json.dumps({
                "success": True,
                "question": {
                    "id": question.id,
                    "text": question.text,
                    "options": question.options,
                    "topic": question.topic,
                    "difficulty": question.difficulty
                }
            })
        else:
            return json.dumps({
                "success": False,
                "message": f"No {difficulty} questions found for topic: {topic}",
                "available_topics": ["Grammar", "Vocabulary", "Indian History", "Legal Principles", "Current Affairs"]
            })
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error retrieving question: {str(e)}"
        })


@tool("submit_practice_answer", args_schema=AnswerInput, description="Submit an answer to the current practice question")
def submit_practice_answer(user_id: str, answer: str) -> str:
    """Submit an answer to the current practice question.
    
    Use this tool when users provide their answer to a practice question.
    
    Args:
        user_id: Unique identifier for the user
        answer: User's answer (A, B, C, or D)
    
    Returns:
        JSON string with answer feedback and next question (if available)
    """
    try:
        if user_id not in active_learning_sessions or not active_learning_sessions[user_id].get("current_question"):
            return json.dumps({
                "success": False,
                "message": "No active question. Please start a practice session first."
            })
        
        user_answer = answer.upper()
        if user_answer not in ['A', 'B', 'C', 'D']:
            return json.dumps({
                "success": False,
                "message": "Please provide a valid answer: A, B, C, or D"
            })
        
        from database.crud import record_user_answer, update_user_performance
        from database.database import get_db
        from learning.question_manager import QuestionManager
        
        question_manager = QuestionManager()
        db = next(get_db())
        user = _ensure_user_exists(db, user_id)
        
        session_info = active_learning_sessions[user_id]
        question = session_info["current_question"]
        correct_answer = question.correct_answer.upper()
        is_correct = user_answer == correct_answer
        
        # Record answer in database
        record_user_answer(
            db, session_info.get("db_session_id", 1), user.id,
            question.id, question.topic, question.text,
            user_answer, correct_answer, 30.0, question.difficulty
        )
        
        # Update performance
        update_user_performance(db, user.id, question.topic, is_correct, 30.0)
        
        result = {
            "success": True,
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "explanation": question.explanation,
            "progress": {
                "questions_asked": session_info['questions_asked'],
                "target_questions": session_info['target_questions']
            }
        }
        
        # Get next question if in practice session
        if session_info["questions_asked"] < session_info["target_questions"]:
            if session_info.get("topic_focus"):
                questions = question_manager.get_question_by_topic(
                    session_info.get("topic_focus"), "medium", 1
                )
                next_question = questions[0] if questions else None
            else:
                next_question = question_manager.get_adaptive_question(user.id)
            
            if next_question:
                session_info["current_question"] = next_question
                session_info["questions_asked"] += 1
                
                result["next_question"] = {
                    "id": next_question.id,
                    "text": next_question.text,
                    "options": next_question.options,
                    "topic": next_question.topic,
                    "difficulty": next_question.difficulty
                }
            else:
                result["session_complete"] = True
                result["message"] = "No more questions available"
        else:
            result["session_complete"] = True
            result["message"] = "Practice session complete!"
            _cleanup_learning_session(user_id)
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error submitting answer: {str(e)}"
        })


@tool("get_learning_progress", args_schema=UserInput, description="Get user's learning progress and performance analytics")
def get_learning_progress(user_id: str) -> str:
    """Get user's learning progress and performance analytics.
    
    Use this tool when users want to:
    - See their performance statistics
    - Check their weak areas
    - Get learning recommendations
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        JSON string with performance analytics
    """
    try:
        from database.crud import get_user_weaknesses
        from database.database import get_db
        
        db = next(get_db())
        user = _ensure_user_exists(db, user_id)
        
        weaknesses = get_user_weaknesses(db, user.id)
        
        if not weaknesses:
            return json.dumps({
                "success": True,
                "message": "No performance data yet. Start practicing to see your progress!",
                "analytics": None
            })
        
        analytics = {
            "topics": [],
            "recommendations": [],
            "overall_stats": {
                "total_topics": len(weaknesses),
                "topics_practiced": len([w for w in weaknesses if w["total_questions"] > 0])
            }
        }
        
        for weakness in weaknesses[:10]:  # Top 10 topics
            accuracy = weakness["accuracy"]
            status = "needs_improvement" if accuracy < 50 else "good" if accuracy < 75 else "excellent"
            
            topic_data = {
                "topic": weakness['topic_name'],
                "accuracy": accuracy,
                "total_questions": weakness['total_questions'],
                "status": status,
                "category": weakness.get('category', 'General')
            }
            analytics["topics"].append(topic_data)
        
        # Generate recommendations
        if weaknesses:
            weakest = weaknesses[0]
            analytics["recommendations"] = [
                f"Focus on {weakest['topic_name']} (lowest accuracy: {weakest['accuracy']:.1f}%)",
                f"Practice more {weakest.get('category', 'related')} questions",
                "Consider reviewing fundamental concepts before attempting harder questions"
            ]
        
        return json.dumps({
            "success": True,
            "analytics": analytics
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error retrieving progress: {str(e)}"
        })


@tool("get_adaptive_question", args_schema=UserInput, description="Get an adaptive question based on user's performance and weaknesses")
def get_adaptive_question(user_id: str) -> str:
    """Get an adaptive question based on user's performance and weaknesses.
    
    Use this tool when users want:
    - Questions tailored to their weak areas
    - Adaptive difficulty based on performance
    - Personalized learning experience
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        JSON string with adaptive question
    """
    try:
        from learning.question_manager import QuestionManager
        from database.database import get_db
        
        question_manager = QuestionManager()
        db = next(get_db())
        user = _ensure_user_exists(db, user_id)
        
        question = question_manager.get_adaptive_question(user.id)
        
        if question:
            # Store as current question
            if user_id not in active_learning_sessions:
                active_learning_sessions[user_id] = {
                    "session_id": str(uuid.uuid4()),
                    "current_question": None,
                    "questions_asked": 0,
                    "target_questions": 1,
                    "topic_focus": None
                }
            
            active_learning_sessions[user_id]["current_question"] = question
            
            return json.dumps({
                "success": True,
                "question": {
                    "id": question.id,
                    "text": question.text,
                    "options": question.options,
                    "topic": question.topic,
                    "difficulty": question.difficulty
                },
                "adaptive_info": {
                    "reason": "Selected based on your performance history",
                    "focus_area": question.topic
                }
            })
        else:
            return json.dumps({
                "success": False,
                "message": "No adaptive question available. Try starting with a specific topic."
            })
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error getting adaptive question: {str(e)}"
        })


# Helper functions for learning tools
def _ensure_user_exists(db, user_id: str):
    """Ensure user exists in database, create if not."""
    from database.crud import create_user, get_user, get_user_by_email
    
    user = get_user(db, int(user_id)) if user_id.isdigit() else None
    if not user:
        # Try to find by email first to avoid duplicates
        existing_user = get_user_by_email(db, f"student_{user_id}@example.com")
        if existing_user:
            return existing_user
        else:
            return create_user(db, f"Student_{user_id}", f"student_{user_id}@example.com")
    return user


def _cleanup_learning_session(user_id: str):
    """Clean up learning session data."""
    if user_id in active_learning_sessions:
        del active_learning_sessions[user_id]


# Modern tools for new agent (using @tool decorator)
TOOLS_AVAILABLE = {
      "english_search_document": english_document_search,
      "search_web": search_web,
      "start_practice_session": start_practice_session,
      "get_practice_question": get_practice_question,
      "submit_practice_answer": submit_practice_answer,
      "get_learning_progress": get_learning_progress,
      "get_adaptive_question": get_adaptive_question
}


def get_registered_tools(tools_names: list[str]) -> list:
        """Get tools - returns modern @tool functions for new agent"""
        registered_tools = []
        for name in tools_names:
                if name in TOOLS_AVAILABLE:
                        registered_tools.append(TOOLS_AVAILABLE[name])
        return registered_tools


def get_all_tool_names() -> list[str]:
        """Get all available tool names"""
        return list(TOOLS_AVAILABLE.keys())
