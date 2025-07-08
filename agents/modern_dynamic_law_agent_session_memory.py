from llm.llm_factory import get_llm
from langchain.prompts import PromptTemplate
from tools.tools_registry import get_registered_tools
from langchain.agents import AgentExecutor, create_react_agent
from config import Config
from langchain_core.runnables.history import RunnableWithMessageHistory
from memory.memory_setup import get_session_history
from langchain_core.runnables.utils import ConfigurableFieldSpec





class ModernDynamicLawAgentWithSessionMemory:
    """
    Modern ModernDynamicLawAgentWithSessionMemory uses the session memory to remember the conversation history.
    
    This agent uses:
    - create_react_agent (compatible with all LLMs including Ollama)
    - memory for session context  which will be deprecated by langchain and suggestion to use langgraph
    - Modern @tool decorated functions
    - Better error handling and parameter validation
    """
    
    def __init__(self, llm_provider: str, llm_model: str, llm_host: str, tools: list[str]):
        # Get the specific LLM by providing provider, model name and host
        self.llm = get_llm(llm_provider, llm_model, llm_host)
        
        # Get modern tools using @tool decorator
        self.tools = get_registered_tools(tools)
        
        # Create ReAct prompt template (compatible with @tool functions)
        # agent_scratchpad - Stores previous agent thoughts, actions, observations during reasoning
        # tools - tools description and names
        # memory to pass the conversation history
        # react goes for several iteration and it starts with begin and so, we have begin with input and scratchpad for the context
        self.prompt = PromptTemplate.from_template(
            """You are a helpful assistant that can answer questions using available tools. You have access to the following tools:

{tools}

IMPORTANT: Choose the right tool based on the question type:
- Use english_search_document ONLY for English grammar, vocabulary, and language skills questions
- Use search_web for current events, facts about people/places, and general knowledge
- For questions about previous conversation (like "what did I ask before", "what was my last question"), check the chat history first

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do and which tool is appropriate. If the question is about previous conversation, check the chat history first.
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action in JSON format. 
   For english_search_document, use: {{"query": "your search query", "max_results": 5}}. 
   For search_web, use: "your search query"
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)

**When you have enough information, finish with:**
Thought: I now know the final answer
Final Answer: <your answer here>

**IMPORTANT: If the question is about previous conversation history (like "what did I ask before"), look at the chat history below and answer directly without using tools.**

---

Previous conversation:
{chat_history}

---

Begin!

Question: {input}
{agent_scratchpad}"""
        )
        
        # Initialize the agent
        self.agent_executor_with_memory = self._init_agent()
    
    def _init_agent(self):
        """
        Create ReAct agent that works with @tool decorated functions.
        
        This uses create_react_agent which:
        - Works with all LLMs including Ollama
        - Compatible with modern @tool decorated functions
        - Has better error handling and parsing

        Then create the agent executor and then pass it to the RunnableWithMessageHistory

        agent is core part and does not attached to memory always. 
        """
        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )


        
        # Create agent executor
        agent_executor = AgentExecutor(
            name="ModernDynamicLawAgent",
            agent=agent,
            tools=self.tools,
            verbose=Config.VERBOSE_MODE,
            handle_parsing_errors=True,
            max_iterations=Config.MAX_ITERATIONS,  # Use config value
            return_intermediate_steps=True,  # Better debugging
        )

        # -- Wrap the executor with memory
        agent_with_memory = RunnableWithMessageHistory(
                             agent_executor,
                             get_session_history,
                             input_messages_key="input",         # matches your key for user message
                             history_messages_key="chat_history",  # matches what your prompt uses
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
    
    def answer_questions(self, question: str, userID: str, session_id: str = "default"):
        """
        Answer questions using the agent.
        
        Args:
            question: The question to answer
            userID: User ID for conversation history
            session_id: Session ID for conversation history
            
        Returns:
            Response from the agent
        """
        # Use the agent to answer the question
        response = self.agent_executor_with_memory.invoke(
            {"input": question},
            config={"configurable": {"user_id": userID, "session_id": session_id}}
        )
        
        return response
    
    def get_tool_info(self):
        """Get information about available tools."""
        tool_info = []
        for tool in self.tools:
            tool_info.append({
                "name": tool.name,
                "description": tool.description,
                "args_schema": str(tool.args_schema) if hasattr(tool, 'args_schema') else "No schema"
            })
        return tool_info
