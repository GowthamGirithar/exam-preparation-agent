from typing import Dict, Any
from langsmith.evaluation import run_evaluator

@run_evaluator
def memory_retention_evaluator(run, example) -> Dict[str, Any]:
    """
    Evaluates whether the agent correctly recalls information from previous conversation.
    
    Args:
        run: The agent's execution run
        example: The test example with expected memory recall
    
    Returns:
        Dict containing score and reasoning
    """
    try:
        # Get the agent's output
        agent_output = ""
        if hasattr(run, 'outputs') and run.outputs:
            agent_output = run.outputs.get('output', '')
        
        # Get expected memory recall
        expected_recall = example.outputs.get("expected_memory_recall", "")
        
        if not agent_output or not expected_recall:
            return {
                "key": "memory_retention",
                "score": 0,
                "reason": "Missing agent output or expected memory recall"
            }
        
        # Calculate memory recall score
        score = calculate_memory_recall_score(agent_output, expected_recall)
        
        # Provide reasoning based on score
        if score >= 0.8:
            reason = "Agent correctly recalled previous conversation"
        elif score >= 0.6:
            reason = "Agent partially recalled previous conversation"
        elif score >= 0.4:
            reason = "Agent showed some memory but with inaccuracies"
        else:
            reason = "Agent failed to recall previous conversation"
        
        return {
            "key": "memory_retention",
            "score": score,
            "reason": reason
        }
        
    except Exception as e:
        return {
            "key": "memory_retention",
            "score": 0,
            "reason": f"Error evaluating memory retention: {str(e)}"
        }

def calculate_memory_recall_score(agent_output: str, expected_recall: str) -> float:
    """
    Calculate how well the agent recalled previous conversation.
    
    Args:
        agent_output: The agent's response to memory question
        expected_recall: What the agent should have recalled
        
    Returns:
        Memory recall score between 0 and 1
    """
    agent_lower = agent_output.lower()
    expected_lower = expected_recall.lower()
    
    # Check if the agent explicitly mentions it doesn't remember
    no_memory_indicators = [
        "don't remember", "can't recall", "no previous", "no conversation",
        "don't have access", "can't access", "no history", "no record"
    ]
    
    if any(indicator in agent_lower for indicator in no_memory_indicators):
        return 0.0
    
    # Check for exact recall
    if expected_lower in agent_lower:
        return 1.0
    
    # Check for partial recall using keyword matching
    expected_keywords = extract_memory_keywords(expected_recall)
    agent_keywords = extract_memory_keywords(agent_output)
    
    if not expected_keywords:
        return 0.5  # Neutral if no keywords to match
    
    # Calculate keyword overlap
    common_keywords = expected_keywords.intersection(agent_keywords)
    overlap_ratio = len(common_keywords) / len(expected_keywords)
    
    # Check if agent mentions "previous question" or similar
    memory_indicators = [
        "previous question", "last question", "earlier", "before", "asked about",
        "you asked", "your question", "conversation", "chat history"
    ]
    
    has_memory_indicator = any(indicator in agent_lower for indicator in memory_indicators)
    
    # Combine scores
    if has_memory_indicator and overlap_ratio >= 0.7:
        return 0.9
    elif has_memory_indicator and overlap_ratio >= 0.5:
        return 0.7
    elif has_memory_indicator and overlap_ratio >= 0.3:
        return 0.5
    elif overlap_ratio >= 0.7:
        return 0.6
    elif overlap_ratio >= 0.5:
        return 0.4
    elif has_memory_indicator:
        return 0.3
    else:
        return 0.1

def extract_memory_keywords(text: str) -> set:
    """
    Extract keywords relevant for memory evaluation.
    
    Args:
        text: Input text
        
    Returns:
        Set of relevant keywords
    """
    import re
    
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words
    words = text.split()
    
    # Memory-specific stop words (less aggressive filtering for memory tasks)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can'
    }
    
    # Keep question words and important terms for memory evaluation
    keywords = {word for word in words if len(word) > 2 and word not in stop_words}
    
    return keywords

@run_evaluator
def conversation_context_evaluator(run, example) -> Dict[str, Any]:
    """
    Evaluates whether the agent maintains proper conversation context.
    
    Args:
        run: The agent's execution run
        example: The test example
    
    Returns:
        Dict containing score and reasoning
    """
    try:
        # Get the agent's output
        agent_output = ""
        if hasattr(run, 'outputs') and run.outputs:
            agent_output = run.outputs.get('output', '')
        
        if not agent_output:
            return {
                "key": "conversation_context",
                "score": 0,
                "reason": "Missing agent output"
            }
        
        # Check for conversation context indicators
        score = evaluate_conversation_context(agent_output)
        
        # Provide reasoning based on score
        if score >= 0.8:
            reason = "Agent demonstrates good conversation context awareness"
        elif score >= 0.6:
            reason = "Agent shows some conversation context awareness"
        elif score >= 0.4:
            reason = "Agent has limited conversation context awareness"
        else:
            reason = "Agent lacks conversation context awareness"
        
        return {
            "key": "conversation_context",
            "score": score,
            "reason": reason
        }
        
    except Exception as e:
        return {
            "key": "conversation_context",
            "score": 0,
            "reason": f"Error evaluating conversation context: {str(e)}"
        }

def evaluate_conversation_context(agent_output: str) -> float:
    """
    Evaluate how well the agent maintains conversation context.
    
    Args:
        agent_output: The agent's response
        
    Returns:
        Context awareness score between 0 and 1
    """
    output_lower = agent_output.lower()
    
    # Positive context indicators
    positive_indicators = [
        "you asked", "your question", "previously", "earlier", "before",
        "in our conversation", "you mentioned", "as we discussed",
        "following up", "continuing", "based on your previous"
    ]
    
    # Negative context indicators
    negative_indicators = [
        "i don't have access", "no previous conversation", "can't recall",
        "no conversation history", "don't remember", "no context"
    ]
    
    # Count positive and negative indicators
    positive_count = sum(1 for indicator in positive_indicators if indicator in output_lower)
    negative_count = sum(1 for indicator in negative_indicators if indicator in output_lower)
    
    # Calculate base score
    if negative_count > 0:
        base_score = 0.2
    elif positive_count >= 2:
        base_score = 0.9
    elif positive_count == 1:
        base_score = 0.7
    else:
        base_score = 0.5
    
    # Adjust based on response length and coherence
    if len(agent_output) > 50 and positive_count > 0:
        base_score += 0.1
    
    return min(1.0, base_score)
