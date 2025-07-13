from typing import Dict, Any
from langsmith.evaluation import run_evaluator

@run_evaluator
def correctness_evaluator(run, example) -> Dict[str, Any]:
    """
    Evaluates the correctness of the agent's answer compared to the expected answer.
    
    Args:
        run: The agent's execution run
        example: The test example with expected answer
    
    Returns:
        Dict containing score and reasoning
    """
    try:
        # Get the agent's output
        agent_output = ""
        if hasattr(run, 'outputs') and run.outputs:
            agent_output = run.outputs.get('output', '')
        
        # Get expected answer
        expected_answer = example.outputs.get("expected_answer", "")
        
        if not agent_output or not expected_answer:
            return {
                "key": "correctness",
                "score": 0,
                "reason": "Missing agent output or expected answer"
            }
        
        # Use simple string similarity for basic correctness check
        score = calculate_answer_similarity(agent_output, expected_answer)
        
        # Provide reasoning
        if score >= 0.8:
            reason = "Answer is highly accurate"
        elif score >= 0.6:
            reason = "Answer is mostly correct with minor differences"
        elif score >= 0.4:
            reason = "Answer is partially correct"
        else:
            reason = "Answer is incorrect or significantly different from expected"
        
        return {
            "key": "correctness",
            "score": score,
            "reason": reason
        }
        
    except Exception as e:
        return {
            "key": "correctness",
            "score": 0,
            "reason": f"Error evaluating correctness: {str(e)}"
        }

def calculate_answer_similarity(agent_answer: str, expected_answer: str) -> float:
    """
    Calculate similarity between agent answer and expected answer.
    
    Args:
        agent_answer: The agent's response
        expected_answer: The expected correct answer
        
    Returns:
        Similarity score between 0 and 1
    """
    # Normalize both answers
    agent_normalized = normalize_answer(agent_answer)
    expected_normalized = normalize_answer(expected_answer)
    
    # Check for exact match
    if agent_normalized == expected_normalized:
        return 1.0
    
    # Check if expected answer is contained in agent answer
    if expected_normalized in agent_normalized:
        return 0.9
    
    # Check if agent answer contains key terms from expected answer
    expected_words = set(expected_normalized.split())
    agent_words = set(agent_normalized.split())
    
    if not expected_words:
        return 0.0
    
    # Calculate word overlap
    common_words = expected_words.intersection(agent_words)
    overlap_ratio = len(common_words) / len(expected_words)
    
    # Bonus for containing most important words
    if overlap_ratio >= 0.8:
        return 0.8
    elif overlap_ratio >= 0.6:
        return 0.6
    elif overlap_ratio >= 0.4:
        return 0.4
    elif overlap_ratio >= 0.2:
        return 0.2
    else:
        return 0.0

def normalize_answer(answer: str) -> str:
    """
    Normalize answer text for comparison.
    
    Args:
        answer: Raw answer text
        
    Returns:
        Normalized answer text
    """
    import re
    
    # Convert to lowercase
    normalized = answer.lower()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Remove common punctuation
    normalized = re.sub(r'[.,!?;:]', '', normalized)
    
    # Remove articles and common words that don't affect meaning
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
    words = normalized.split()
    words = [word for word in words if word not in stop_words]
    
    return ' '.join(words)

@run_evaluator
def llm_based_correctness_evaluator(run, example) -> Dict[str, Any]:
    """
    Uses an LLM to evaluate the correctness of the answer.
    This is more sophisticated but requires an LLM call.
    
    Args:
        run: The agent's execution run
        example: The test example with expected answer
    
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
        
        # Get expected answer and question
        expected_answer = example.outputs.get("expected_answer", "")
        question = example.inputs.get("question", "")
        
        if not agent_output or not expected_answer:
            return {
                "key": "llm_correctness",
                "score": 0,
                "reason": "Missing agent output or expected answer"
            }
        
        # Create evaluation prompt
        # we can even use predefined prompt which is there in langchain 
        # we can use inbuild function also create_llm_as_judge
        eval_prompt = f"""
        Question: {question}
        Expected Answer: {expected_answer}
        Agent's Answer: {agent_output}
        
        Please evaluate if the agent's answer is correct compared to the expected answer.
        Consider semantic meaning, not just exact word matching.
        
        Respond with a score from 0 to 1 (where 1 is completely correct) and a brief reason.
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
            "key": "llm_correctness",
            "score": score,
            "reason": reason
        }
        
    except Exception as e:
        return {
            "key": "llm_correctness",
            "score": 0,
            "reason": f"Error in LLM evaluation: {str(e)}"
        }
