from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from llm.llm_factory import get_llm
from tools.tools_registry import get_registered_tools
from config import Config
import json
import logging

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
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        
        # Session storage for conversation history
        # later this can be convereted into checkpointer memory
        self.session_histories = {}
    
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
        
        return workflow.compile()
    
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
            
            # chr(10) - (\n) joun results_summary 
            system_context = f"""
            You are a helpful assistant specialized in CLAT exam preparation.

            Planning Decision:
            {plan.get('reasoning', 'No reasoning provided')}

            Tool Results:
            {chr(10).join(results_summary)}

            Please follow these guidelines when responding:
            1. Answer the user's question directly and helpfully.
            2. Use any tool results or planning info provided to ensure accurate and relevant answers.
            3. If the tool result includes a next question (e.g., under 'next_question'), present it clearly to the user with options listed.
            4. If the tool result includes progress info, summarize it to show how far along the user is in the session.
            5. Be encouraging and supportive, keeping in mind the user's exam preparation.
            6. If any tools failed or provided incomplete information, acknowledge this but still do your best to assist.

            Generate responses that are natural, conversational, and informative."""
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
            
            # Enhance response with structured data if available
            final_response = self._enhance_response_with_structured_data(final_response, tool_results)
            
            logger.info(f"RESPONDER: Generated response: {final_response[:100]}...")
            
        except Exception as e:
            logger.error(f"RESPONDER: Error generating response: {e}")
            final_response = "I apologize, but I encountered an error while generating my response. Please try asking your question again."
        
        # Add final AI response
        ai_message = AIMessage(content=final_response)
        state["messages"].append(ai_message)
        
        return state
    
    def _enhance_response_with_structured_data(self, response: str, tool_results: List[Dict[str, Any]]) -> str:
        """Enhance response by parsing and formatting structured data from tools."""
        '''
        if no tool results then return llm response

        This function acts like a post-processor, ensuring:
            Practice questions get formatted cleanly
            Progress data is rendered with emojis & bullet points
            LLM output is enhanced, clarified, and made structured
        '''
        for result in tool_results:
            if not result["success"]:
                continue
                
            try:
                result_content = result["result"]
                # Look for JSON in tool results
                if '{"success":' in result_content or '{"question":' in result_content:
                    # Extract JSON part
                    json_start = result_content.find('{')
                    json_end = result_content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = result_content[json_start:json_end]
                        parsed = json.loads(json_str)
                        
                        # Format based on content type
                        if "question" in parsed and parsed.get("success"):
                            question_data = parsed["question"]
                            formatted_question = f"""

                                        📚 **Practice Question:**
                                        **Topic:** {question_data.get('topic', 'General')}
                                        **Difficulty:** {question_data.get('difficulty', 'Medium')}

                                        {question_data.get('text', '')}

                                        **Options:**
                                        {question_data.get('options', '')}

                                        Please provide your answer (A, B, C, or D).
                                        """
                            response = response + formatted_question
                        
                        elif "analytics" in parsed and parsed.get("success"):
                            analytics = parsed["analytics"]
                            if analytics and "topics" in analytics:
                                progress_text = "\n\n📊 **Your Learning Progress:**\n"
                                for topic in analytics["topics"][:5]:
                                    status_emoji = "🟢" if topic["status"] == "excellent" else "🟡" if topic["status"] == "good" else "🔴"
                                    progress_text += f"{status_emoji} **{topic['topic']}**: {topic['accuracy']:.1f}% ({topic['total_questions']} questions)\n"
                                response = response + progress_text
            except (json.JSONDecodeError, KeyError):
                continue
        
        return response
    

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
    def answer_questions(self, question: str, user_id: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Main interface method that processes questions using the debuggable workflow.
        
        Args:
            question: The user's question
            user_id: User ID for session management
            session_id: Session ID for conversation history
            
        Returns:
            Response dictionary with output and chat history
        """
        logger.info(f"Starting autonomous agent for user {user_id}, session {session_id}")
        logger.info(f"Question: {question}")
        
        # Get or create session history
        session_key = f"{user_id}_{session_id}"
        if session_key not in self.session_histories:
            self.session_histories[session_key] = []
        
        # Create initial state
        initial_state = AgentState(
            messages=[HumanMessage(content=question)],
            user_id=user_id,
            session_id=session_id,
            plan=None,
            tool_results=[],
            iteration_count=0,
            max_iterations=Config.MAX_ITERATIONS,
            next_action=""
        )
        
        # Add conversation history to state
        initial_state["messages"] = self.session_histories[session_key] + initial_state["messages"]
        
        try:
            # Execute the debuggable workflow
            logger.info("Executing workflow...")
            final_state = self.workflow.invoke(initial_state)
            
            # Update session history
            self.session_histories[session_key] = final_state["messages"]
            
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
            
            logger.info("Workflow completed successfully")
            
            return {
                "output": output,
                "chat_history": chat_history,
                "plan": final_state.get("plan"),
                "tool_results": final_state.get("tool_results", []),
                "debug_info": {
                    "planner_reasoning": final_state.get("plan", {}).get("reasoning"),
                    "tools_executed": len(final_state.get("tool_results", [])),
                    "workflow_steps": ["planner", "executor" if final_state.get("tool_results") else "responder"]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error in autonomous workflow: {e}")
            return {
                "output": f"I apologize, but I encountered an error: {str(e)}",
                "chat_history": [],
                "plan": None,
                "tool_results": [],
                "debug_info": {"error": str(e)}
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