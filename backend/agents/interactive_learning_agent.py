from llm.llm_factory import get_llm
from langchain.prompts import PromptTemplate
from tools.tools_registry import get_registered_tools
from langchain.agents import AgentExecutor, create_react_agent
from config import Config
from langchain_core.runnables.history import RunnableWithMessageHistory
from memory.memory_setup import get_session_history
from langchain_core.runnables.utils import ConfigurableFieldSpec
from learning.question_manager import QuestionManager
from database.crud import (
    create_user, get_user, get_user_by_email, create_learning_session,
    record_user_answer, update_user_performance, get_user_weaknesses
)
from database.database import get_db
import uuid
import json
from typing import Dict, Any, Optional
import re


class InteractiveLearningAgent:
    """
    Interactive Learning Agent that combines your existing law exam agent 
    with adaptive learning capabilities.
    
    Features:
    - All existing agent capabilities (document search, web search, session memory)
    - Interactive question generation from your PDF content
    - Adaptive question selection based on user performance
    - Performance tracking and analytics
    - Topic explanations with examples
    - Learning session management

    Issue : 
    a. React agent is answering the question and not allowing users to ans . Even control is not returned to client code to submit ans.
    b. Tool input parameter are not passed correctly even when open ai used
    c. we need to enable skip validation for tools input schema

    """
    
    def __init__(self, llm_provider: str, llm_model: str, llm_host: str, tools: list[str]):
        # Get the specific LLM
        self.llm = get_llm(llm_provider, llm_model, llm_host)
        
        # Get modern tools using @tool decorator
        self.tools = get_registered_tools(tools)
        
        # Initialize Question Manager for adaptive learning
        self.question_manager = QuestionManager()
        
        # Learning session state
        self.active_sessions = {}  # user_id -> session_info
        
        # Create simplified prompt template that relies on tool descriptions
        self.prompt = PromptTemplate.from_template(
            """You are a helpful, reasoning-focused CLAT preparation tutor that answers user questions, guides them through MCQs, tracks their progress, and explains legal concepts clearly. Use the tools below whenever helpful.
Available tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: think about what to do and which tool is most appropriate based on the tool descriptions
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action in JSON format
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)

**Important: If you provide a practice question, do not answer it yourself. Wait for the user's response.**
When starting a practice session, provide the first question to the user and wait. Do NOT submit any answers by yourself until the user provides a valid answer.
After the user answers, call submit_practice_answer with the answer, then provide feedback and next question.
Keep this question-answer loop until all questions are done.

Thought: I now know the final answer
Final Answer: <your answer here>

Previous conversation:
{chat_history}

Question: {input}
{agent_scratchpad}"""
        )
        
        # Initialize the agent
        self.agent_executor_with_memory = self._init_agent()
    
    def _init_agent(self):
        """Create ReAct agent with learning capabilities."""
        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        agent_executor = AgentExecutor(
            name="InteractiveLearningAgent",
            agent=agent,
            tools=self.tools,
            verbose=Config.VERBOSE_MODE,
            handle_parsing_errors=True,
            max_iterations=Config.MAX_ITERATIONS,
            return_intermediate_steps=False,
        )

        # Wrap with memory
        agent_with_memory = RunnableWithMessageHistory(
            agent_executor,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="user_id",
                    annotation=str,
                    name="User ID",
                    description="Unique identifier for the user.",
                    default="",
                    is_shared=True,
                ),
                ConfigurableFieldSpec(
                    id="session_id",
                    annotation=str,
                    name="Session ID", 
                    description="Unique identifier for the session.",
                    default="",
                    is_shared=True,
                ),
            ]
        )
        
        return agent_with_memory
    
    def answer_questions(self, question: str, user_id: str, session_id: str = "default"):
        """
        Autonomous answer method that uses the agent's intelligence to decide when to use learning tools.
        
        Args:
            question: The question from the user
            user_id: User ID for conversation and performance tracking
            session_id: Session ID for conversation history
            
        Returns:
            Response from the autonomous agent
        """
        # Use the agent with memory
        response = self.agent_executor_with_memory.invoke(
            {"input": question},
            config={"configurable": {"user_id": user_id, "session_id": session_id}}
        )

        return response
    
    def get_tool_info(self):
        """Get information about available tools and learning features."""
        tool_info = []
        for tool in self.tools:
            tool_info.append({
                "name": tool.name,
                "description": tool.description,
                "args_schema": str(tool.args_schema) if hasattr(tool, 'args_schema') else "No schema"
            })
        
        # Add learning features info
        tool_info.append({
            "name": "Interactive Learning",
            "description": "Adaptive question generation, performance tracking, and personalized learning",
            "commands": [
                "start practice [topic]",
                "get question [topic] [difficulty]", 
                "answer [A/B/C/D]",
                "explain [topic]",
                "my progress",
                "end session"
            ]
        })
        
        return tool_info
