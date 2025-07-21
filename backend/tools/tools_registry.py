from retrievers.vector_store_factory import get_vector_store
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_community.tools.google_serper.tool import GoogleSerperAPIWrapper
from config import Config
import json
import uuid
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_tool_input(raw_input: Any, tool_name: str = "") -> Dict[str, Any]:
    """
    Simple helper to parse tool input for Ollama models.
    Handles the case where LangChain passes entire JSON as first parameter.
    """
    
    if isinstance(raw_input, str) and raw_input.strip().startswith('{'):
            try:
                parsed = json.loads(raw_input.strip())
                logger.info(f"[{tool_name}] Parsed JSON: {parsed}")
                return parsed
            except json.JSONDecodeError:
                logger.warning(f"[{tool_name}] JSON parsing failed, using as string")
                return {"query": raw_input}
    else :
            return raw_input




class SearchInput(BaseModel):
    query: str = Field(description="query to search for English grammar, vocabulary, comprehension passages, and language skills for CLAT exam")
    max_results: int = Field(default=5, description="maximum number of results to return")


@tool("english_search_document", 
      args_schema=SearchInput if Config.TOOL_SCHEMA_VALIDATION else None,
      description="Use this tool for any learning related to English grammar, vocabulary, comprehension passages, and language skills for CLAT exam and not for practising questions")
def english_document_search(query_or_json, max_results: int = 5):
    """Search English language study materials for CLAT exam preparation."""
    
    # Parse input only for Ollama mode (when validation is off)
    if not Config.TOOL_SCHEMA_VALIDATION:
        params = parse_tool_input(query_or_json, "english_search_document")
        query_or_json = params.get("query", str(query_or_json))
        max_results = params.get("max_results", max_results)
    
    try:
        vector_store = get_vector_store(
            provider_name=Config.VECTOR_STORE_PROVIDER,
            embedding_provider=Config.EMBEDDING_PROVIDER,
            embedding_model=Config.DEFAULT_EMBEDDING_MODEL,
            collection_name=Config.ENGLISH_COLLECTION
        )
        results = vector_store.get_chroma_retriever(top_k=max_results).invoke(query_or_json)
        logger.info(f"English search returned {len(results)} results for query: {query_or_json}")
        return results
    except Exception as e:
        logger.error(f"English search error: {e}")
        return str(e)


@tool("search_web", description="Search the web for current information, facts, news, and general knowledge")
def search_web(query_or_json: str) -> str:
    """Search the web for current information, facts, news, and general knowledge."""
    
    # Parse input only for Ollama mode (when validation is off)
    if not Config.TOOL_SCHEMA_VALIDATION:
        params = parse_tool_input(query_or_json, "search_web")
        query_or_json = params.get("query", str(query_or_json))
    
    try:      
        serper = GoogleSerperAPIWrapper(
            serper_api_key=Config.GOOGLE_SERPER_API_KEY,
            k=Config.SEARCH_RESULTS_LIMIT,
        )
        response = serper.run(query_or_json)
        logger.info(f"Web search completed for query: {query}")
        return response
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"Error searching web: {str(e)}"


# ===== LEARNING TOOLS =====
# These tools enable autonomous learning functionality

# Global state for learning sessions
active_learning_sessions = {}

class PracticeSessionInput(BaseModel):
    user_id: str = Field(description="Unique identifier for the user")
    topic: Optional[str] = Field(default=None, description="Optional topic to focus on (e.g., Grammar, Legal Principles)")
    target_questions: int = Field(default=10, description="Number of questions in the session")

class PractiseQuestionInput(BaseModel):
    user_id: str = Field(description="Unique identifier for the user")
    topic: str = Field(default="Grammar", description="Topic for the question")
    difficulty: str = Field(default="medium", description="Question difficulty (easy, medium, hard)")


class AnswerInput(BaseModel):
    user_id: str = Field(description="Unique identifier for the user")
    answer: str = Field(description="User's answer (A, B, C, or D)")

class UserInput(BaseModel):
    user_id: str = Field(description="Unique identifier for the user")

class LearningProgressInput(BaseModel):
    user_id: str = Field(description="Unique identifier for the user")






@tool("start_practice_session", 
      args_schema=PracticeSessionInput if Config.TOOL_SCHEMA_VALIDATION else None,
      description="Provide number of questions user asked to practice for CLAT on specific topics")
def start_practice_session(user_id="1", topic: Optional[str] = None, target_questions: int = 10) -> str:
    """Start an adaptive practice session for CLAT exam preparation."""
    
    # Parse input only for Ollama mode (when validation is off)
    if not Config.TOOL_SCHEMA_VALIDATION:
        params = parse_tool_input(user_id, "start_practice_session")
        user_id = params.get("user_id", "1")
        topic = params.get("topic", topic)
        target_questions = params.get("target_questions", target_questions)

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
# parse_docstring=True,
@tool("get_practice_question", args_schema=PractiseQuestionInput if Config.TOOL_SCHEMA_VALIDATION else None, description="Get a specific practice question by topic and difficulty for CLAT preparation")
def get_practice_question(user_id: str=1, topic: str="Grammar", difficulty: str = "medium") -> str:
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
    # due to bug on langchain we need to do json parse 
    if not Config.TOOL_SCHEMA_VALIDATION:
        params = parse_tool_input(user_id, "get_practice_question")
        user_id = params.get("user_id", "1")
        topic = params.get("topic", topic)
        difficulty = params.get('difficulty', difficulty)
    
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


@tool("submit_practice_answer",args_schema=AnswerInput if Config.TOOL_SCHEMA_VALIDATION else None,
       description= ("Use this tool to submit the user's answer to any question. Works in two modes: "
                    "1) Standalone Q&A: Validates answer and provides feedback for any question "
                    "2) Practice Session: Validates answer and provides next question based on adaptive learning"))
def submit_practice_answer(user_id: str = "1", answer: str="A") -> str:
    """Submit an answer to a question (works both in practice sessions and standalone Q&A).
    
    This tool supports two modes:
    1. Standalone Q&A: If there's a current question but no active practice session,
       it validates the answer and provides feedback without continuing to next question.
    2. Practice Session: If in an active practice session, it validates the answer
       and provides the next question based on adaptive learning.
    
    Args:
        user_id: Unique identifier for the user
        answer: User's answer (A, B, C, or D)
    
    Returns:
        JSON string with answer feedback and optionally next question
    """
    if not Config.TOOL_SCHEMA_VALIDATION:
        params = parse_tool_input(user_id, "submit_practice_answer")
        user_id = params.get('user_id', '1')
        answer = params.get('answer', 'A')
       
    
    try:
        # Check if there's any current question
        if user_id not in active_learning_sessions or not active_learning_sessions[user_id].get("current_question"):
            return json.dumps({
                "success": False,
                "message": "No active question found. Please ask for a question first using get_practice_question or start a practice session."
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
        
        # Determine if this is a practice session or standalone Q&A
        is_practice_session = (session_info.get("target_questions", 0) > 1 and 
                              session_info.get("db_session_id") is not None)
        
        # Record answer in database
        db_session_id = session_info.get("db_session_id", 1)
        record_user_answer(
            db, db_session_id, user.id,
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
            "question_info": {
                "topic": question.topic,
                "difficulty": question.difficulty
            }
        }
        
        if is_practice_session:
            # Practice session mode - provide next question if session not complete
            result["mode"] = "practice_session"
            result["progress"] = {
                "questions_asked": session_info['questions_asked'],
                "target_questions": session_info['target_questions']
            }
            
            # Check if session should continue
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
                    _cleanup_learning_session(user_id)
            else:
                result["session_complete"] = True
                result["message"] = "Practice session complete!"
                _cleanup_learning_session(user_id)
        else:
            # Standalone Q&A mode - just validate and provide feedback
            result["mode"] = "standalone_qa"
            result["message"] = "Answer validated. Ask for another question or start a practice session for continuous learning."
            
            # Clear the current question for standalone mode
            session_info["current_question"] = None
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error submitting answer: {str(e)}"
        })


@tool("get_learning_progress",args_schema=LearningProgressInput if Config.TOOL_SCHEMA_VALIDATION else None,
      description="Get user's learning progress and performance analytics")
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
    if not Config.TOOL_SCHEMA_VALIDATION:
        params = parse_tool_input(user_id, "get_learning_progress")
        user_id = params.get('user_id', '1')
    
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


@tool("get_adaptive_question",  description="Get an adaptive question based on user's performance and weaknesses")
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
    if not Config.TOOL_SCHEMA_VALIDATION:
        params = parse_tool_input(user_id, "get_adaptive_question")
        user_id = params.get('user_id', '1')    

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
