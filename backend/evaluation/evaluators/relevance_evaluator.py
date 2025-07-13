from typing import Dict, Any
from langsmith.evaluation import run_evaluator

@run_evaluator
def relevance_evaluator(run, example) -> Dict[str, Any]:
    """
    Evaluates whether the agent's response is relevant to the question asked.
    
    Args:
        run: The agent's execution run
        example: The test example with question
    
    Returns:
        Dict containing score and reasoning
    """
    try:
        # Get the agent's output
        agent_output = ""
        if hasattr(run, 'outputs') and run.outputs:
            agent_output = run.outputs.get('output', '')
        
        # Get the question
        question = example.inputs.get("question", "")
        
        if not agent_output or not question:
            return {
                "key": "relevance",
                "score": 0,
                "reason": "Missing agent output or question"
            }
        
        # Calculate relevance score
        score = calculate_relevance_score(question, agent_output)
        
        # Provide reasoning based on score
        if score >= 0.8:
            reason = "Response is highly relevant to the question"
        elif score >= 0.6:
            reason = "Response is mostly relevant with some off-topic content"
        elif score >= 0.4:
            reason = "Response is partially relevant but contains significant off-topic content"
        else:
            reason = "Response is not relevant to the question asked"
        
        return {
            "key": "relevance",
            "score": score,
            "reason": reason
        }
        
    except Exception as e:
        return {
            "key": "relevance",
            "score": 0,
            "reason": f"Error evaluating relevance: {str(e)}"
        }

def calculate_relevance_score(question: str, response: str) -> float:
    """
    Calculate how relevant the response is to the question.
    
    Args:
        question: The original question
        response: The agent's response
        
    Returns:
        Relevance score between 0 and 1
    """
    # Extract key terms from question
    question_keywords = extract_keywords(question)
    response_keywords = extract_keywords(response)
    
    if not question_keywords:
        return 0.5  # Neutral score if no keywords found
    
    # Calculate keyword overlap
    common_keywords = question_keywords.intersection(response_keywords)
    keyword_overlap = len(common_keywords) / len(question_keywords)
    
    # Check for question type relevance
    question_type_score = check_question_type_relevance(question, response)
    
    # Combine scores
    final_score = (keyword_overlap * 0.6) + (question_type_score * 0.4)
    
    return min(1.0, final_score)

def extract_keywords(text: str) -> set:
    """
    Extract meaningful keywords from text.
    
    Args:
        text: Input text
        
    Returns:
        Set of keywords
    """
    import re
    
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words
    words = text.split()
    
    # Remove stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can',
        'what', 'who', 'where', 'when', 'why', 'how', 'which', 'that', 'this', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    # Filter out stop words and short words
    keywords = {word for word in words if len(word) > 2 and word not in stop_words}
    
    return keywords

def check_question_type_relevance(question: str, response: str) -> float:
    """
    Check if the response type matches the question type.
    
    Args:
        question: The original question
        response: The agent's response
        
    Returns:
        Score between 0 and 1 for question type relevance
    """
    question_lower = question.lower()
    response_lower = response.lower()
    
    # Define question type patterns and expected response patterns
    question_patterns = {
        'definition': ['what is', 'define', 'meaning of', 'definition'],
        'who': ['who is', 'who was', 'who are'],
        'where': ['where is', 'where was', 'capital of', 'location'],
        'when': ['when did', 'when was', 'what year'],
        'how': ['how to', 'how do', 'how does'],
        'grammar': ['past tense', 'subject', 'verb', 'noun', 'adjective', 'grammar'],
        'current_affairs': ['president', 'minister', 'current', 'latest', 'recent']
    }
    
    # Check which question type this is
    detected_type = None
    for q_type, patterns in question_patterns.items():
        if any(pattern in question_lower for pattern in patterns):
            detected_type = q_type
            break
    
    if not detected_type:
        return 0.7  # Neutral score for unrecognized question types
    
    # Check if response contains appropriate content for the question type
    if detected_type == 'definition' and any(word in response_lower for word in ['is', 'means', 'refers to', 'defined as']):
        return 1.0
    elif detected_type == 'who' and any(word in response_lower for word in ['person', 'people', 'individual', 'leader']):
        return 1.0
    elif detected_type == 'where' and any(word in response_lower for word in ['located', 'city', 'country', 'place']):
        return 1.0
    elif detected_type == 'grammar' and any(word in response_lower for word in ['grammar', 'tense', 'verb', 'noun', 'subject']):
        return 1.0
    elif detected_type == 'current_affairs' and len(response_lower) > 10:  # Assume substantial response for current affairs
        return 0.8
    else:
        return 0.5

@run_evaluator
def llm_based_relevance_evaluator(run, example) -> Dict[str, Any]:
    """
    Uses an LLM to evaluate the relevance of the response to the question.
    
    Args:
        run: The agent's execution run
        example: The test example with question
    
    Returns:
        Dict containing score and reasoning
    """
    try:
        from llm.llm_factory import get_llm
        from config import Config
        
        # Get the agent's output
        agent_output = ""
        if hasattr(run, 'outputs') and run.outputs:
            agent_output = run.outputs.get('output', '')
        
        # Get the question
        question = example.inputs.get("question", "")
        
        if not agent_output or not question:
            return {
                "key": "llm_relevance",
                "score": 0,
                "reason": "Missing agent output or question"
            }
        
        # Create evaluation prompt
        eval_prompt = f"""
        Question: {question}
        Agent's Response: {agent_output}
        
        Please evaluate how relevant the agent's response is to the question asked.
        Consider whether the response directly addresses what was asked.
        
        Respond with a score from 0 to 1 (where 1 is completely relevant) and a brief reason.
        Format: SCORE: 0.X REASON: your explanation
        """
        
        # Get LLM for evaluation
        llm = get_llm(Config.LLM_PROVIDER, Config.LLM_MODEL, Config.LLM_HOST)
        
        # Get evaluation
        evaluation = llm.invoke(eval_prompt)
        
        # Parse score and reason
        import re
        score_match = re.search(r'SCORE:\s*([\d.]+)', evaluation)
        reason_match = re.search(r'REASON:\s*(.+)', evaluation)
        
        score = float(score_match.group(1)) if score_match else 0.0
        reason = reason_match.group(1).strip() if reason_match else "Could not parse evaluation"
        
        return {
            "key": "llm_relevance",
            "score": score,
            "reason": reason
        }
        
    except Exception as e:
        return {
            "key": "llm_relevance",
            "score": 0,
            "reason": f"Error in LLM evaluation: {str(e)}"
        }
