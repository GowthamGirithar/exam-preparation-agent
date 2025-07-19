"""
Question Management System for the Law Exam Learning System.

This module provides:
- Question retrieval from Vector DB (ChromaDB) populated via PDF ingestion
- Question metadata management and parsing from PDF content
- Adaptive question selection based on user performance
- Question difficulty assessment and categorization
- Integration with existing PDF ingestion pipeline

WORKFLOW:
1. PDFs with CLAT questions → DataIngestor → ChromaDB (Vector DB)
2. Student requests question → QuestionManager → Retrieves from ChromaDB
3. Raw text → QuestionParser → Structured Question object
4. User performance analysis → Adaptive selection → Personalized questions
"""

import json
import random
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from retrievers.vector_store_factory import get_vector_store
from config import Config
from database.database import SessionLocal
from database.crud import get_user_weaknesses, get_user_performance, get_topics


@dataclass
class Question:
    """
    Structured question data with metadata.
    
    This represents a parsed question from PDF content stored in Vector DB.
    """
    id: str                    # Unique identifier
    text: str                  # Question text
    options: List[str]         # Answer options (A, B, C, D)
    correct_answer: str        # Correct answer letter
    explanation: str           # Detailed explanation
    topic: str                 # CLAT topic (Grammar, Legal Principles, etc.)
    category: str              # CLAT category (English, Legal Reasoning, etc.)
    difficulty: str            # easy, medium, hard
    source: str                # vector_db, fallback, etc.
    metadata: Dict[str, Any]   # Additional metadata


class QuestionParser:
    """
    Parse questions from PDF content stored in Vector DB.
    
    Supports multiple question formats commonly found in CLAT preparation materials:
    - Standard MCQ format with options A, B, C, D
    - Legal reasoning principle-fact format
    - Reading comprehension passages
    """
    
    @staticmethod
    def parse_question_text(content: str) -> Optional[Question]:
        """
        Parse question from PDF text content retrieved from Vector DB.
        
        Supported formats:
        1. "Question: ... Options: A) ... B) ... Answer: A Explanation: ..."
        2. "Q: ... (A) ... (B) ... Correct: A Explanation: ..."
        3. "Principle: ... Facts: ... Question: ... A) ... Answer: A"
        4. "Passage: ... Question: ... A) ... B) ... Answer: B"
        
        Args:
            content: Raw text from PDF stored in ChromaDB
            
        Returns:
            Question object or None if parsing fails
        """
        try:
            # Generate unique ID based on content hash
            question_id = f"q_{abs(hash(content[:200])) % 100000}"
            
            # Extract question text (handles multiple formats)
            question_text = QuestionParser._extract_question_text(content)
            if not question_text:
                return None
            
            # Extract options
            options = QuestionParser._extract_options(content)
            if len(options) < 2:
                return None
            
            # Extract correct answer
            correct_answer = QuestionParser._extract_correct_answer(content)
            if not correct_answer:
                return None
            
            # Extract explanation
            explanation = QuestionParser._extract_explanation(content)
            
            # Determine topic and category from content
            topic, category = QuestionParser._determine_topic_category(content)
            
            # Assess difficulty
            difficulty = QuestionParser._assess_difficulty(question_text, options, content)
            
            return Question(
                id=question_id,
                text=question_text,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
                topic=topic,
                category=category,
                difficulty=difficulty,
                source="vector_db",
                metadata={
                    "parsed_at": datetime.utcnow().isoformat(),
                    "content_length": len(content),
                    "source_type": "pdf_ingestion"
                }
            )
            
        except Exception as e:
            print(f"Error parsing question: {e}")
            return None
    
    @staticmethod
    def _extract_question_text(content: str) -> Optional[str]:
        """Extract question text from various formats."""
        patterns = [
            # Standard format: "Question: ..."
            r'(?:Question|Q):\s*(.+?)(?:Options?|Choices?|\(A\)|A\))',
            # Legal reasoning: "Facts: ... Question: ..."
            r'Facts?:\s*.+?Question:\s*(.+?)(?:Options?|\(A\)|A\))',
            # After principle: "Principle: ... Facts: ... (.+?)(?:Options?|\(A\)|A\))"
            r'Principle:\s*.+?Facts?:\s*.+?(?:Question:\s*)?(.+?)(?:Options?|\(A\)|A\))',
            # Passage format: "Passage: ... Question: ..."
            r'Passage:\s*.+?Question:\s*(.+?)(?:Options?|\(A\)|A\))',
            # Simple format: Just text before options
            r'^(.+?)(?:Options?|Choices?|\(A\)|A\))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                question_text = match.group(1).strip()
                # Clean up the text
                question_text = re.sub(r'\s+', ' ', question_text)
                if len(question_text) > 10:  # Minimum length check
                    return question_text
        
        return None
    
    @staticmethod
    def _extract_options(content: str) -> List[str]:
        """Extract answer options from content."""
        option_patterns = [
            # Format: (A) option text (B) option text
            r'\(([A-D])\)\s*([^(]+?)(?=\([A-D]\)|Answer|Correct|Explanation|$)',
            # Format: A) option text B) option text
            r'([A-D])\)\s*([^A-D)]+?)(?=[A-D]\)|Answer|Correct|Explanation|$)',
            # Format: A. option text B. option text
            r'([A-D])\.?\s*([^A-D.]+?)(?=[A-D]\.?|Answer|Correct|Explanation|$)'
        ]
        
        for pattern in option_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            if matches and len(matches) >= 2:
                options = []
                for letter, text in matches:
                    clean_text = re.sub(r'\s+', ' ', text.strip())
                    if clean_text:
                        options.append(f"{letter.upper()}) {clean_text}")
                
                if len(options) >= 2:
                    return options
        
        return []
    
    @staticmethod
    def _extract_correct_answer(content: str) -> Optional[str]:
        """Extract correct answer from content."""
        patterns = [
            r'(?:Answer|Correct|Solution):\s*([A-D])',
            r'(?:Answer|Correct|Solution)\s*(?:is|=)?\s*([A-D])',
            r'Correct\s+option\s*(?:is|=)?\s*([A-D])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    @staticmethod
    def _extract_explanation(content: str) -> str:
        """Extract explanation from content."""
        patterns = [
            r'Explanation:\s*(.+?)(?:\n\n|Question:|$)',
            r'Solution:\s*(.+?)(?:\n\n|Question:|$)',
            r'Reason:\s*(.+?)(?:\n\n|Question:|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                explanation = match.group(1).strip()
                explanation = re.sub(r'\s+', ' ', explanation)
                if len(explanation) > 10:
                    return explanation
        
        return "No explanation provided."
    
    @staticmethod
    def _determine_topic_category(content: str) -> Tuple[str, str]:
        """
        Determine topic and category from question content using keyword analysis.
        
        This is crucial for adaptive learning - questions must be properly categorized
        to track user performance by topic.
        """
        content_lower = content.lower()
        
        # Enhanced topic mapping with more keywords
        topic_keywords = {
            # English Language
            "Grammar": [
                "grammar", "tense", "verb", "noun", "adjective", "sentence", "correct",
                "subject", "predicate", "clause", "phrase", "syntax", "error", "mistake"
            ],
            "Vocabulary": [
                "synonym", "antonym", "meaning", "word", "vocabulary", "definition",
                "lexical", "semantic", "idiom", "phrase"
            ],
            "Reading Comprehension": [
                "passage", "comprehension", "paragraph", "reading", "inference",
                "author", "tone", "theme", "main idea", "conclude"
            ],
            "Sentence Correction": [
                "error", "mistake", "correction", "incorrect", "wrong", "identify",
                "spot the error", "find the mistake"
            ],
            
            # General Knowledge
            "Indian History": [
                "history", "ancient", "medieval", "modern", "dynasty", "empire",
                "mughal", "british", "independence", "freedom", "revolt", "war"
            ],
            "Indian Geography": [
                "geography", "river", "mountain", "state", "capital", "climate",
                "monsoon", "plateau", "desert", "coast", "peninsula"
            ],
            "Indian Polity": [
                "constitution", "government", "parliament", "president", "minister",
                "democracy", "federal", "fundamental rights", "directive principles"
            ],
            "Economics": [
                "economy", "gdp", "inflation", "budget", "economic", "finance",
                "monetary", "fiscal", "trade", "commerce", "market"
            ],
            "Current Affairs": [
                "current", "recent", "news", "event", "2023", "2024", "latest",
                "contemporary", "today", "modern"
            ],
            "Science & Technology": [
                "science", "technology", "invention", "discovery", "research",
                "innovation", "digital", "computer", "space", "medical"
            ],
            
            # Legal Reasoning
            "Legal Principles": [
                "law", "legal", "principle", "rule", "statute", "act", "section",
                "provision", "legislation", "jurisprudence"
            ],
            "Case Studies": [
                "case", "court", "judgment", "verdict", "litigation", "trial",
                "plaintiff", "defendant", "appeal", "supreme court"
            ],
            "Constitutional Law": [
                "constitutional", "fundamental", "rights", "duties", "amendment",
                "article", "schedule", "preamble"
            ],
            "Contract Law": [
                "contract", "agreement", "breach", "obligation", "consideration",
                "offer", "acceptance", "damages"
            ],
            
            # Logical Reasoning
            "Analytical Reasoning": [
                "pattern", "sequence", "logic", "analysis", "arrangement",
                "order", "systematic", "logical"
            ],
            "Critical Reasoning": [
                "argument", "conclusion", "premise", "reasoning", "assumption",
                "strengthen", "weaken", "evaluate"
            ],
            "Puzzles": [
                "puzzle", "arrangement", "order", "position", "seating",
                "ranking", "direction", "blood relation"
            ],
            
            # Quantitative Techniques
            "Basic Mathematics": [
                "calculate", "mathematics", "number", "arithmetic", "algebra",
                "geometry", "trigonometry", "equation"
            ],
            "Data Interpretation": [
                "chart", "graph", "table", "data", "statistics", "bar chart",
                "pie chart", "line graph", "interpret"
            ],
            "Percentages": [
                "percent", "percentage", "ratio", "proportion", "increase",
                "decrease", "profit", "loss"
            ]
        }
        
        # Category mapping
        category_map = {
            "Grammar": "English", "Vocabulary": "English", 
            "Reading Comprehension": "English", "Sentence Correction": "English",
            
            "Indian History": "General Knowledge", "Indian Geography": "General Knowledge",
            "Indian Polity": "General Knowledge", "Economics": "General Knowledge",
            "Current Affairs": "General Knowledge", "Science & Technology": "General Knowledge",
            
            "Legal Principles": "Legal Reasoning", "Case Studies": "Legal Reasoning",
            "Constitutional Law": "Legal Reasoning", "Contract Law": "Legal Reasoning",
            
            "Analytical Reasoning": "Logical Reasoning", "Critical Reasoning": "Logical Reasoning",
            "Puzzles": "Logical Reasoning",
            
            "Basic Mathematics": "Quantitative Techniques", "Data Interpretation": "Quantitative Techniques",
            "Percentages": "Quantitative Techniques"
        }
        
        # Find best matching topic using weighted scoring
        best_topic = "General Knowledge"  # Default fallback
        max_score = 0
        
        for topic, keywords in topic_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in content_lower:
                    # Weight longer keywords more heavily
                    score += len(keyword.split())
            
            if score > max_score:
                max_score = score
                best_topic = topic
        
        category = category_map.get(best_topic, "General Knowledge")
        return best_topic, category
    
    @staticmethod
    def _assess_difficulty(question_text: str, options: List[str], full_content: str) -> str:
        """
        Assess question difficulty using multiple factors.
        
        This helps in adaptive learning by providing appropriate difficulty levels.
        """
        text = question_text.lower()
        content = full_content.lower()
        
        # Difficulty indicators
        easy_indicators = [
            "what", "who", "when", "where", "is", "are", "basic", "simple",
            "identify", "name", "list", "define"
        ]
        medium_indicators = [
            "how", "why", "which", "analyze", "compare", "explain", "describe",
            "discuss", "examine", "evaluate"
        ]
        hard_indicators = [
            "synthesize", "complex", "intricate", "comprehensive", "critically",
            "justify", "assess", "elaborate", "deduce", "infer"
        ]
        
        # Calculate scores
        easy_score = sum(2 for indicator in easy_indicators if indicator in text)
        medium_score = sum(2 for indicator in medium_indicators if indicator in text)
        hard_score = sum(2 for indicator in hard_indicators if indicator in text)
        
        # Length-based assessment
        if len(question_text) > 300:
            hard_score += 3
        elif len(question_text) > 150:
            medium_score += 2
        elif len(question_text) < 50:
            easy_score += 2
        
        # Option complexity
        avg_option_length = sum(len(opt) for opt in options) / len(options) if options else 0
        if avg_option_length > 80:
            hard_score += 2
        elif avg_option_length > 40:
            medium_score += 1
        elif avg_option_length < 20:
            easy_score += 1
        
        # Legal reasoning complexity
        if "principle" in content and "facts" in content:
            medium_score += 2
        
        # Passage-based questions
        if "passage" in content and len(full_content) > 500:
            hard_score += 2
        
        # Determine final difficulty
        if hard_score > max(easy_score, medium_score):
            return "hard"
        elif medium_score > easy_score:
            return "medium"
        else:
            return "easy"


class QuestionManager:
    """
    Main question management system integrating with PDF ingestion pipeline.
    
    WORKFLOW:
    1. PDFs → DataIngestor → ChromaDB (your existing system)
    2. Student request → QuestionManager → Query ChromaDB
    3. Raw content → QuestionParser → Structured Question
    4. Performance analysis → Adaptive selection
    """
    
    def __init__(self):
        self.vector_store = None
        self.parser = QuestionParser()
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialize connection to Vector DB (ChromaDB with PDF content)."""
        try:
            # Use LAW_COLLECTION for CLAT questions from PDFs
            self.vector_store = get_vector_store(
                provider_name=Config.VECTOR_STORE_PROVIDER,
                embedding_provider=Config.EMBEDDING_PROVIDER,
                embedding_model=Config.DEFAULT_EMBEDDING_MODEL,
                collection_name=Config.LAW_COLLECTION
            )
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize vector store: {e}")
            print("📝 Will use fallback questions instead")
    
    def get_question_by_topic(self, topic: str, difficulty: str = "medium", limit: int = 1) -> List[Question]:
        """
        Get questions filtered by topic and difficulty from PDF content.
        
        Args:
            topic: CLAT topic (e.g., "Grammar", "Legal Principles")
            difficulty: "easy", "medium", "hard", or "any"
            limit: Number of questions to return
            
        Returns:
            List of structured Question objects
        """
        # if not self.vector_store:
        return self._get_fallback_questions(topic, difficulty, limit)
        
        '''
        # TODO uncomment after vector db is injested with data
        try:
            # Create semantic search query for the topic
            search_queries = [
                f"{topic} CLAT question practice {difficulty}",
                f"{topic} multiple choice question MCQ",
                f"CLAT {topic} exam question answer explanation"
            ]
            
            questions = []
            
            # Try multiple search queries to get diverse results
            for query in search_queries:
                if len(questions) >= limit:
                    break
                
                # Retrieve from vector store (PDF content)
                results = self.vector_store.get_chroma_retriever(top_k=limit * 2).invoke(query)
                
                for result in results:
                    if len(questions) >= limit:
                        break
                    
                    # Extract content from result
                    content = result.page_content if hasattr(result, 'page_content') else str(result)
                    
                    # Parse the PDF content into structured question
                    question = self.parser.parse_question_text(content)
                    
                    if question and self._is_topic_match(question.topic, topic):
                        if difficulty == "any" or question.difficulty == difficulty:
                            # Avoid duplicates
                            if not any(q.id == question.id for q in questions):
                                questions.append(question)
            
            # If not enough questions found, supplement with fallback
            if len(questions) < limit:
                fallback_needed = limit - len(questions)
                fallback = self._get_fallback_questions(topic, difficulty, fallback_needed)
                questions.extend(fallback)
            
            return questions[:limit]
            
        except Exception as e:
            print(f"❌ Error retrieving questions from Vector DB: {e}")
            return self._get_fallback_questions(topic, difficulty, limit)
            '''
    
    def get_adaptive_question(self, user_id: int) -> Optional[Question]:
        """
        Get next question based on user's performance and weaknesses.
        
        This is the core of adaptive learning:
        1. Analyze user's weak topics from performance data
        2. Select appropriate difficulty based on accuracy
        3. Return personalized question
        """
        db = SessionLocal()
        try:
            # Get user's weak areas
            weaknesses = get_user_weaknesses(db, user_id, limit=3)
            
            if weaknesses:
                # Focus on weakest topics (adaptive learning)
                weak_topic = random.choice(weaknesses[:2])  # Top 2 weakest
                topic_name = weak_topic["topic_name"]
                
                # Adjust difficulty based on performance
                accuracy = weak_topic["accuracy"]
                if accuracy < 30:
                    difficulty = "easy"    # Build confidence
                elif accuracy < 70:
                    difficulty = "medium"  # Standard practice
                else:
                    difficulty = "hard"    # Challenge the user
                
                print(f"🎯 Adaptive selection: {topic_name} ({difficulty}) - {accuracy:.1f}% accuracy")
                
                questions = self.get_question_by_topic(topic_name, difficulty, 1)
                return questions[0] if questions else None
            
            else:
                # New user - start with common topics at medium difficulty
                common_topics = ["Grammar", "Vocabulary", "Indian History", "Legal Principles"]
                topic = random.choice(common_topics)
                
                print(f"🆕 New user: Starting with {topic} (medium)")
                
                questions = self.get_question_by_topic(topic, "medium", 1)
                return questions[0] if questions else None
                
        except Exception as e:
            print(f"❌ Error in adaptive question selection: {e}")
            return None
        finally:
            db.close()
    
    def get_random_question(self, category: Optional[str] = None) -> Optional[Question]:
        """Get a random question, optionally from a specific category."""
        db = SessionLocal()
        try:
            topics = get_topics(db, category)
            if not topics:
                return None
            
            topic = random.choice(topics)
            questions = self.get_question_by_topic(topic.name, "medium", 1)
            return questions[0] if questions else None
            
        except Exception as e:
            print(f"❌ Error getting random question: {e}")
            return None
        finally:
            db.close()
    
    def _is_topic_match(self, detected_topic: str, requested_topic: str) -> bool:
        """Check if detected topic matches requested topic (with some flexibility)."""
        if detected_topic.lower() == requested_topic.lower():
            return True
        
        # Allow some flexibility in topic matching
        topic_aliases = {
            "Grammar": ["English Grammar", "Language", "Sentence"],
            "Legal Principles": ["Law", "Legal", "Jurisprudence"],
            "Indian History": ["History", "Ancient India", "Medieval India"],
            "Current Affairs": ["News", "Recent Events", "Contemporary"]
        }
        
        for main_topic, aliases in topic_aliases.items():
            if main_topic.lower() == requested_topic.lower():
                return any(alias.lower() in detected_topic.lower() for alias in aliases)
        
        return False
    
    def _get_fallback_questions(self, topic: str, difficulty: str, limit: int) -> List[Question]:
        """
        Generate fallback questions when Vector DB is unavailable or insufficient.
        
        These are high-quality sample questions for each CLAT topic.
        """
        fallback_questions = {
            "Grammar": [
                {
                    "text": "Choose the correct sentence:",
                    "options": ["A) He don't like coffee", "B) He doesn't likes coffee", "C) He doesn't like coffee", "D) He not like coffee"],
                    "correct_answer": "C",
                    "explanation": "The correct form uses 'doesn't' (does not) with the base form of the verb 'like'.",
                    "difficulty": "easy"
                },
                {
                    "text": "Identify the error in: 'The team are playing well today.'",
                    "options": ["A) The team", "B) are playing", "C) well today", "D) No error"],
                    "correct_answer": "B",
                    "explanation": "'Team' is a collective noun and takes singular verb 'is playing'.",
                    "difficulty": "medium"
                }
            ],
            "Vocabulary": [
                {
                    "text": "What is the synonym of 'happy'?",
                    "options": ["A) Joyful", "B) Sad", "C) Angry", "D) Tired"],
                    "correct_answer": "A",
                    "explanation": "Joyful means feeling or expressing happiness, making it a synonym of happy.",
                    "difficulty": "easy"
                },
                {
                    "text": "Choose the word that best completes: 'His _____ remarks offended everyone.'",
                    "options": ["A) Tactful", "B) Diplomatic", "C) Caustic", "D) Gentle"],
                    "correct_answer": "C",
                    "explanation": "Caustic means harsh or severe, which would offend people.",
                    "difficulty": "medium"
                }
            ],
            "Indian History": [
                {
                    "text": "Who was the first President of India?",
                    "options": ["A) Jawaharlal Nehru", "B) Dr. Rajendra Prasad", "C) Sardar Patel", "D) Dr. A.P.J. Abdul Kalam"],
                    "correct_answer": "B",
                    "explanation": "Dr. Rajendra Prasad was the first President of India, serving from 1950 to 1962.",
                    "difficulty": "easy"
                },
                {
                    "text": "The Sepoy Mutiny of 1857 began in:",
                    "options": ["A) Delhi", "B) Meerut", "C) Lucknow", "D) Kanpur"],
                    "correct_answer": "B",
                    "explanation": "The Sepoy Mutiny of 1857 began in Meerut on May 10, 1857.",
                    "difficulty": "medium"
                }
            ],
            "Legal Principles": [
                {
                    "text": "Principle: A person is liable for negligence if they fail to take reasonable care. Facts: A doctor operates without proper sterilization. Is the doctor liable?",
                    "options": ["A) Yes, due to negligence", "B) No, it's an accident", "C) Only if patient dies", "D) Depends on hospital policy"],
                    "correct_answer": "A",
                    "explanation": "The doctor failed to take reasonable care (proper sterilization), which constitutes negligence.",
                    "difficulty": "medium"
                },
                {
                    "text": "Which Article of the Indian Constitution deals with Right to Equality?",
                    "options": ["A) Article 12", "B) Article 14", "C) Article 19", "D) Article 21"],
                    "correct_answer": "B",
                    "explanation": "Article 14 of the Indian Constitution guarantees equality before law and equal protection of laws.",
                    "difficulty": "easy"
                }
            ]
        }
        
        questions = []
        topic_questions = fallback_questions.get(topic, [])
        
        for i, q_data in enumerate(topic_questions):
            if difficulty != "any" and q_data.get("difficulty", "medium") != difficulty:
                continue
                
            question = Question(
                id=f"fallback_{topic}_{i}_{int(datetime.utcnow().timestamp())}",
                text=q_data["text"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
                explanation=q_data["explanation"],
                topic=topic,
                category=self._get_category_for_topic(topic),
                difficulty=q_data.get("difficulty", "medium"),
                source="fallback",
                metadata={
                    "generated_at": datetime.utcnow().isoformat(),
                    "type": "fallback_question"
                }
            )
            questions.append(question)
            if len(questions) >= limit:
                break
        
        return questions
    
    def _get_category_for_topic(self, topic: str) -> str:
        """Get CLAT category for a given topic."""
        category_map = {
            "Grammar": "English", "Vocabulary": "English",
            "Reading Comprehension": "English", "Sentence Correction": "English",
            "Indian History": "General Knowledge", "Indian Geography": "General Knowledge",
            "Indian Polity": "General Knowledge", "Economics": "General Knowledge",
            "Current Affairs": "General Knowledge", "Science & Technology": "General Knowledge",
            "Legal Principles": "Legal Reasoning", "Case Studies": "Legal Reasoning",
            "Constitutional Law": "Legal Reasoning", "Contract Law": "Legal Reasoning",
            "Analytical Reasoning": "Logical Reasoning", "Critical Reasoning": "Logical Reasoning",
            "Puzzles": "Logical Reasoning",
            "Basic Mathematics": "Quantitative Techniques", "Data Interpretation": "Quantitative Techniques",
            "Percentages": "Quantitative Techniques"
        }
        return category_map.get(topic, "General Knowledge")
    
    def validate_question(self, question: Question) -> bool:
        """Validate question structure and content."""
        if not question.text or len(question.text.strip()) < 10:
            return False
        
        if not question.options or len(question.options) < 2:
            return False
        
        if not question.correct_answer or question.correct_answer not in ['A', 'B', 'C', 'D']:
            return False
        
        return True
    
    def get_question_stats(self) -> Dict[str, Any]:
        """Get statistics about available questions."""
        try:
            if not self.vector_store:
                return {"status": "Vector DB not available", "fallback_topics": 4}
            
            # This would require implementing a count method in your vector store
            return {
                "status": "Connected to Vector DB",
                "source": "PDF ingestion via ChromaDB",
                "fallback_available": True
            }
        except Exception as e:
            return {"status": f"Error: {e}"}


# Convenience function for easy import
def get_question_manager() -> QuestionManager:
    """Get a configured QuestionManager instance."""
    return QuestionManager()