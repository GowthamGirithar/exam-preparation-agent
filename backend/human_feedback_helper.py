"""
Human Feedback Helper Class.
Simple helper for managing human feedback functionality in the autonomous agent.
"""

from typing import Dict, List, Optional
from config import Config
import logging

logger = logging.getLogger(__name__)

class HumanFeedbackHelper:
    """Helper class for human feedback functionality."""
    
    # Keywords that boost confidence (simple requests)
    AUTO_APPROVE_KEYWORDS = [
        "practice", "question", "progress", "simple", "basic", "help", "show"
    ]
    
    # Keywords that lower confidence (complex requests)
    COMPLEX_KEYWORDS = [
        "analyze", "complex", "detailed", "comprehensive", "intricate", 
        "elaborate", "sophisticated", "nuanced", "multifaceted", "explain"
    ]
    
    # Keywords that significantly lower confidence (ambiguous requests)
    AMBIGUOUS_KEYWORDS = [
        "something", "anything", "whatever", "i don't know", "not sure", "maybe"
    ]
    
    @classmethod
    def assess_confidence(cls, plan: Dict, user_question: str) -> float:
        """
        Assess confidence in the agent's plan and decision.
        
        Args:
            plan: The agent's planned action
            user_question: User's original question
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.8  # Start with baseline
        question_lower = user_question.lower()
        
        # Boost confidence for simple, clear requests
        if any(keyword in question_lower for keyword in cls.AUTO_APPROVE_KEYWORDS):
            confidence += 0.1
            logger.debug(f"Confidence boost for simple request: +0.1")
        
        # Lower confidence for complex questions
        if any(keyword in question_lower for keyword in cls.COMPLEX_KEYWORDS):
            confidence -= 0.3
            logger.debug(f"Confidence penalty for complex request: -0.3")
        
        # Significantly lower confidence for ambiguous requests
        if any(keyword in question_lower for keyword in cls.AMBIGUOUS_KEYWORDS):
            confidence -= 0.4
            logger.debug(f"Confidence penalty for ambiguous request: -0.4")
        
        # Length-based assessment
        if len(user_question) > 200:
            confidence -= 0.2
            logger.debug(f"Confidence penalty for long question: -0.2")
        elif len(user_question) < 20:
            confidence += 0.1
            logger.debug(f"Confidence boost for short question: +0.1")
        
        # Tool selection assessment
        tools_to_use = plan.get("tools_to_use", [])
        if not tools_to_use and any(word in question_lower for word in cls.COMPLEX_KEYWORDS):
            confidence -= 0.2
            logger.debug(f"Confidence penalty for complex question without tools: -0.2")
        
        # Ensure confidence is within bounds
        final_confidence = max(min(confidence, 1.0), 0.0)
        logger.debug(f"Final confidence score: {final_confidence:.2f}")
        
        return 0
    
    @classmethod
    def should_require_approval(cls, confidence_score: float, human_feedback_enabled: bool) -> bool:
        """
        Determine if human approval is required.
        
        Args:
            confidence_score: Calculated confidence score
            human_feedback_enabled: Whether human feedback is enabled
            
        Returns:
            True if human approval is required
        """
        if not human_feedback_enabled:
            return False
        
        return confidence_score < Config.HUMAN_FEEDBACK_CONFIDENCE_THRESHOLD
    
    @classmethod
    def create_approval_message(cls, confidence_score: float, user_question: str) -> str:
        """
        Create a human-readable approval request message.
        
        Args:
            confidence_score: Calculated confidence score
            user_question: User's original question
            
        Returns:
            Formatted approval message
        """
        reasons = []
        question_lower = user_question.lower()
        
        # Determine reasons for low confidence
        if confidence_score < 0.5:
            reasons.append("very low confidence")
        elif confidence_score < 0.7:
            reasons.append("low confidence")
        
        if len(user_question) > 200:
            reasons.append("complex question")
        
        if any(keyword in question_lower for keyword in cls.COMPLEX_KEYWORDS):
            reasons.append("complex analysis requested")
        
        if any(keyword in question_lower for keyword in cls.AMBIGUOUS_KEYWORDS):
            reasons.append("ambiguous request")
        
        reason_text = ", ".join(reasons) if reasons else "requires review"
        return f"Human approval needed: {reason_text} (confidence: {confidence_score:.2f})"

    



