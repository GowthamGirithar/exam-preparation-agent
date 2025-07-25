from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from llm.llm_factory import get_llm
from tools.tools_registry import get_registered_tools
from config import Config
from langsmith import traceable
import json
import logging
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

'''
Planner - Call LLM to decide which tools to use or no tools required ; Fallback when LLM fails to decide which tools to use
Executor - Invoke tools based on planner output
Responder - Generate final response based on planner and executor output by calling LLM
'''


class AgentState(TypedDict):
    """State for the Autonomous LangGraph Agent."""
    # Is of TypedDict
    # we access all these inside workflow as state["<field name>"]
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    session_id: str
    plan: Optional[Dict[str, Any]]  # What the planner decided
    tool_results: List[Dict[str, Any]]  # Results from tool execution
    iteration_count: int
    max_iterations: int
    next_action: str  # What to do next


class AutonomousLangGraphAgent:
    """
    Debuggable autonomous LangGraph agent with clear separation of concerns.
    
    Architecture:
    - Planner: Decides what tools to use and why
    - Executor: Executes the planned tools
    - Responder: Generates final response based on results
    
    Easy to debug because each step is explicit and logged.
    """
    
    def __init__(self, llm_provider: str, llm_model: str, llm_host: str, tools: list[str]):
        # Get the ChatLLM
        self.llm = get_llm(llm_provider, llm_model, llm_host)
        
        # Get tools using existing registry
        self.tools = get_registered_tools(tools)
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        
        # Setup persistent checkpointer for memory
        self.checkpointer = self._setup_checkpointer()
        
        # Create the workflow graph with checkpointer
        self.workflow = self._create_workflow()
    
    def _setup_checkpointer(self):
        """Setup SQLite checkpointer for persistent memory"""
        # https://langchain-ai.github.io/langgraph/concepts/persistence/#using-in-langgraph
        db_path = Config.CHECKPOINTER_DB_PATH
        logger.info(f"Setting up checkpointer with database: {db_path}")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        return SqliteSaver(conn)
    
    def _create_workflow(self) -> StateGraph:
        
        """Create the debuggable workflow with clear steps."""
        workflow = StateGraph(AgentState)
        
        # Add nodes with clear responsibilities
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("executor", self._executor_node)
        workflow.add_node("responder", self._responder_node)
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Add clear routing
        workflow.add_conditional_edges(
            "planner",
            self._route_after_planning,
            {
                "execute_tools": "executor",
                "respond_directly": "responder"
            }
        )
        
        workflow.add_edge("executor", "responder")
        workflow.add_edge("responder", END)
       
       # There is workflow.add_sequence where we can add all the nodes executed in sequential order
        
        # Compile with checkpointer for persistent memory
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _planner_node(self, state: AgentState) -> AgentState:
        """
        PLANNER: Analyzes the question and decides what tools to use.
        This is completely under our control and easy to debug.
        """
        logger.info("PLANNER: Starting planning phase")
        
        # Get the user's question
        # we have different message type like human, system (prompt), ai(response from llm), etc.
        # messages contain all the messages 
        last_human_message = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_human_message = msg
                break
        
        if not last_human_message:
            logger.error("PLANNER: No human message found")
            state["plan"] = {"action": "respond_directly", "reason": "No user question found"}
            state["next_action"] = "respond_directly"
            return state
        
        user_question = last_human_message.content
        logger.info(f"PLANNER: User question: {user_question[:100]}...")
        
        # Create planning prompt or we can say routing as well which decide which tool to use
        # mentioning structure of response about tool helps for next steps
        system_message = f"""You are an assistant with access to the following tools:

    Available Tools:
    {self._get_tool_descriptions()}

    Your task: Analyze the user's question and decide if you need to use any tools.  
    Be specific about WHY.

    When responding, reply only with JSON in this exact format:
            {{
                "needs_tools": true/false,
                "reasoning": "explain your decision why the tools is used, if its false explain why other tools are not used",
                "tools_to_use": [
                    {{
                        "tool_name": "exact_tool_name",
                        "parameters": {{"param1": "value1"}},
                        "reason": "why this tool with these parameters"
                    }}
                ]
            }}

    If no tools are needed, use an empty array for tools_to_use and set needs_tools to false. Reply this also with only JSON format.
    """ 
        
        try:
            # Get planning decision from LLM
            # having the role helps LLM to have more context.
            '''
            "system" = instructions/assistant persona ; contains tool info + instructions — this sets context for the assistant.
            "user" = user inputs/questions
            "assistant" = model’s prior responses        
            '''
            messages = [
                {
                    "role": "system", 
                    "content": system_message
                },
                {   
                    "role": "user", 
                    "content": user_question
                }
            ]           

            response = self.llm.invoke(messages)
            plan_text = response.content.strip()
            
            logger.info(f"PLANNER: LLM response: {plan_text[:500]}...")
            
            # Parse the plan
            if plan_text.startswith('{') and plan_text.endswith('}'):
                try:
                    plan = json.loads(plan_text)
                    logger.info(f"PLANNER: Successfully parsed plan: {plan}")
                except json.JSONDecodeError as e:
                    logger.error(f"PLANNER: JSON parsing failed: {e}")
                    plan = self._fallback_plan(user_question)
            else:
                logger.warning("PLANNER: LLM didn't return JSON, using fallback")
                plan = self._fallback_plan(user_question)
            
            # Store the plan
            state["plan"] = plan
            
            # Decide next action
            if plan.get("needs_tools", False) and plan.get("tools_to_use"):
                state["next_action"] = "execute_tools"
                logger.info(f"PLANNER: Will execute {len(plan['tools_to_use'])} tools")
            else:
                state["next_action"] = "respond_directly"
                logger.info("PLANNER: Will respond directly without tools")
            
        except Exception as e:
            logger.error(f"PLANNER: Error during planning: {e}")
            state["plan"] = self._fallback_plan(user_question)
            state["next_action"] = "execute_tools"
        
        return state
    
    @traceable
    def _fallback_plan(self, user_question: str) -> Dict[str, Any]:
        """Fallback planning when LLM fails."""
        logger.info("PLANNER: Using fallback planning logic")
        
        question_lower = user_question.lower()
        
        # Simple rule-based fallback
        if any(word in question_lower for word in ["practice", "question", "start"]):
            return {
                "needs_tools": True,
                "reasoning": "Fallback: Detected practice-related request",
                "tools_to_use": [{
                    "tool_name": "get_practice_question",
                    "parameters": {"user_id": "fallback", "topic": "Grammar", "difficulty": "medium"},
                    "reason": "User wants practice questions"
                }]
            }
        elif any(word in question_lower for word in ["progress", "performance"]):
            return {
                "needs_tools": True,
                "reasoning": "Fallback: Detected progress request",
                "tools_to_use": [{
                    "tool_name": "get_learning_progress",
                    "parameters": {"user_id": "fallback"},
                    "reason": "User wants to see progress"
                }]
            }
        elif any(word in question_lower for word in ["grammar", "english", "vocabulary"]):
            return {
                "needs_tools": True,
                "reasoning": "Fallback: Detected English learning request",
                "tools_to_use": [{
                    "tool_name": "english_search_document",
                    "parameters": {"query": user_question, "max_results": 5},
                    "reason": "User needs English learning content"
                }]
            }
        else:
            return {
                "needs_tools": False,
                "reasoning": "Fallback: General question, no tools needed",
                "tools_to_use": []
            }
    
    def _route_after_planning(self, state: AgentState) -> Literal["execute_tools", "respond_directly"]:
        """Route based on planner's decision."""
        # based on the planner output we decide which is the next step and it should be one of the two
        return state["next_action"]
    
    def _executor_node(self, state: AgentState) -> AgentState:
        """
        EXECUTOR: Executes the tools planned by the planner.
        Each execution is logged for easy debugging.
        """
        logger.info("EXECUTOR: Starting tool execution phase")
        
        plan = state.get("plan", {})
        tools_to_use = plan.get("tools_to_use", [])
        
        if not tools_to_use:
            logger.warning("EXECUTOR: No tools to execute")
            state["tool_results"] = []
            return state
        
        results = []
        
        for i, tool_spec in enumerate(tools_to_use):
            tool_name = tool_spec.get("tool_name")
            parameters = tool_spec.get("parameters", {})
            reason = tool_spec.get("reason", "No reason provided")
            
            logger.info(f"EXECUTOR: Executing tool {i+1}/{len(tools_to_use)}: {tool_name}")
            logger.info(f"EXECUTOR: Parameters: {parameters}")
            logger.info(f"EXECUTOR: Reason: {reason}")
            
            # Add user_id if not present
            if "user_id" not in parameters:
                parameters["user_id"] = state["user_id"]
            
            # Execute the tool
            try:
                result = self._execute_single_tool(tool_name, parameters)
                logger.info(f"EXECUTOR: Tool {tool_name} succeeded")
                logger.info(f"EXECUTOR: Result preview: {str(result)[:500]}...")
                
                results.append({
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "reason": reason,
                    "result": result,
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"EXECUTOR: Tool {tool_name} failed: {e}")
                results.append({
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "reason": reason,
                    "result": f"Error: {str(e)}",
                    "success": False
                })
        
        state["tool_results"] = results
        logger.info(f"EXECUTOR: Completed execution of {len(results)} tools")
        
        return state
    
    @traceable
    def _execute_single_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a single tool with proper error handling."""
        tool = self.tools_by_name.get(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
        
        result = tool.invoke(parameters)
        
        return str(result)
    
    def _responder_node(self, state: AgentState) -> AgentState:
        """
        RESPONDER: Generates the final response based on planning and execution results.
        This is where we format the final answer for the user.
        """
        logger.info("RESPONDER: Starting response generation")
        
        # Get the user's original question
        user_question = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_question = msg.content
                break
        
        plan = state.get("plan", {})
        tool_results = state.get("tool_results", [])
        
        logger.info(f"RESPONDER: Plan reasoning: {plan.get('reasoning', 'No reasoning')}")
        logger.info(f"RESPONDER: Tool results count: {len(tool_results)}")
        
        # Create response prompt
        if tool_results:
            # We have tool results to incorporate
            results_summary = []
            for result in tool_results:
                if result["success"]:
                    results_summary.append(f"Tool {result['tool_name']}: {result['result'][:1000]}...")
                else:
                    results_summary.append(f"Tool {result['tool_name']} failed: {result['result']}")
            
            # chr(10) - (\n) join results_summary
            system_context = f"""
            You are a helpful assistant specialized in CLAT exam preparation.

            Planning Decision:
            {plan.get('reasoning', 'No reasoning provided')}

            Tool Results:
            {chr(10).join(results_summary)}

            Please follow these guidelines when responding:
            1. Answer the user's question directly and helpfully using markdown formatting.
            2. Use the tool results provided to ensure accurate and relevant answers.
            3. **For practice questions**: Use this markdown format:
               - **Topic:** [topic] **Difficulty:** [level]
               - [Question text]
               - **Options:**
                 [Option A text]
                 [Option B text]
                 [Option C text]
                 [Option D text]
               - Please choose your answer.
            4. **For progress data**: Use emojis and bullet points to make it visually appealing
            5. **For submit answer**: If there is a next question in the tools output of submit answe, ask the question to the user in the same format as practise question
            6. Be encouraging and supportive, keeping in mind the user's exam preparation.
            7. If any tools failed, acknowledge this but still provide helpful guidance.

            Keep responses concise and well-formatted."""
        else:
            # No tool results, direct response
            system_context = f"""You are a helpful assistant guiding students preparing for the CLAT exam.

            Planning Decision:
            {plan.get('reasoning', 'Direct response without tools')}

            When responding to the user's question, follow these instructions:

            1. Provide clear and educational explanations related to CLAT topics.
            2. Be encouraging and supportive in tone.
            3. Share relevant advice, insights, or exam strategies where appropriate.
            4. If you can’t fully answer the question, suggest useful next steps or resources the user might explore.

            Your goal is to respond naturally, conversationally, and in a way that motivates the learner.
            """
        
        try:
            messages = [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_question}
            ]
                
            response = self.llm.invoke(messages)
            final_response = response.content
            
            logger.info(f"RESPONDER: Generated response: {final_response[:100]}...")
            
        except Exception as e:
            logger.error(f"RESPONDER: Error generating response: {e}")
            final_response = "I apologize, but I encountered an error while generating my response. Please try asking your question again."
        
        # Add final AI response
        ai_message = AIMessage(content=final_response)
        state["messages"].append(ai_message)
        
        return state
    
    

    # _get_tool_descriptions returns tool description and parameters for the llm to decide which tools and parameter to pass for tools
    def _get_tool_descriptions(self) -> str:
        descriptions = []
        for tool in self.tools:
            param_desc = []

            if hasattr(tool, "args_schema") and tool.args_schema:
                # Pydantic v2 - Use model_fields
                for param_name, field in tool.args_schema.model_fields.items():
                    description = field.description or "No description"
                    type_name = field.annotation.__name__ if hasattr(field.annotation, '__name__') else str(field.annotation)
                    param_desc.append(f"    - {param_name}: {description} (type: {type_name})")
            else:
                param_desc.append("    None")

            params_text = "\n".join(param_desc)
            descriptions.append(
                f"- {tool.name}: {tool.description}\n  Parameters:\n{params_text}"
            )

        logger.info(f"Tool descriptions: {descriptions}")
        return "\n".join(descriptions)
    
    """ answer_questions is the conversation agent interface"""
    @traceable
    def answer_questions(self, question: str, user_id: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Main interface method that processes questions using the debuggable workflow with persistent memory.
        
        Args:
            question: The user's question
            user_id: User ID for session management
            session_id: Session ID for conversation history
            
        Returns:
            Response dictionary with output and chat history
        """
        logger.info(f"Starting autonomous agent for user {user_id}, session {session_id}")
        logger.info(f"Question: {question}")
        
        # Create thread configuration for persistent memory
        thread_config = {
            "configurable": {
                "thread_id": f"{user_id}_{session_id}"
            }
        }

        user_question = "user with id"+user_id+" and asked "+question
        
        # Create initial state (checkpointer will handle history automatically)
        initial_state = AgentState(
            messages=[HumanMessage(content=user_question)],
            user_id=user_id,
            session_id=session_id,
            plan=None,
            tool_results=[],
            iteration_count=0,
            max_iterations=Config.MAX_ITERATIONS,
            next_action=""
        )
        
        try:
            # Execute workflow - checkpointer automatically loads/saves conversation history
            logger.info("Executing workflow with persistent memory...")
            final_state = self.workflow.invoke(initial_state, config=thread_config)
            
            # Extract the final response
            ai_messages = [msg for msg in final_state["messages"] if isinstance(msg, AIMessage)]
            output = ai_messages[-1].content if ai_messages else "I apologize, but I couldn't generate a response."
            
            # Format chat history for compatibility
            chat_history = []
            messages = final_state["messages"]
            for i in range(0, len(messages)):
                if isinstance(messages[i], HumanMessage):
                    # Find the next AI message
                    for j in range(i + 1, len(messages)):
                        if isinstance(messages[j], AIMessage):
                            chat_history.append({
                                "human": messages[i].content,
                                "ai": messages[j].content
                            })
                            break
            
            logger.info("Workflow completed successfully with persistent memory")
            
            # Return clean response structure without redundant data
            response_data = {
                "output": output,
                "chat_history": chat_history
            }
            
            # Only include debug info in development/debug mode
            # You can control this with an environment variable
            import os
            if os.getenv("DEBUG_MODE", "false").lower() == "true":
                response_data["debug_info"] = {
                    "planner_reasoning": final_state.get("plan", {}).get("reasoning"),
                    "tools_executed": len(final_state.get("tool_results", [])),
                    "workflow_steps": ["planner", "executor" if final_state.get("tool_results") else "responder"],
                    "memory_persistent": True,
                    "thread_id": thread_config["configurable"]["thread_id"]
                }
            
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Error in autonomous workflow: {e}")
            return {
                "output": f"I apologize, but I encountered an error: {str(e)}",
                "chat_history": []
            }
    
    def get_tool_info(self):
        """Get information about available tools and autonomous features."""
        tool_info = []
        for tool in self.tools:
            tool_info.append({
                "name": tool.name,
                "description": tool.description,
                "args_schema": str(tool.args_schema) if hasattr(tool, 'args_schema') else "No schema"
            })
        
        # Add autonomous features info
        tool_info.append({
            "name": "Debuggable Autonomous Features",
            "description": "Clear separation of concerns with explicit logging",
            "features": [
                "Planner: Decides what tools to use and why",
                "Executor: Executes planned tools with detailed logging",
                "Responder: Generates final response based on results",
                "Full debug information in response",
                "Easy to trace and troubleshoot"
            ]
        })
        
        return tool_info