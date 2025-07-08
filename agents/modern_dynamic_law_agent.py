from llm.llm_factory import get_llm
from langchain.prompts import PromptTemplate
from tools.tools_registry import get_registered_tools
from langchain.agents import AgentExecutor, create_react_agent
from config import Config


class ModernDynamicLawAgent:
    """
    Modern Dynamic Law Agent using @tool decorated functions with ReAct pattern.
    
    This agent uses:
    - create_react_agent (compatible with all LLMs including Ollama)
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
        # react goes for several iteration and it starts with begin and so, we have begin with input and scratchpad for the context
        self.prompt = PromptTemplate.from_template(
            """You are a helpful assistant that can answer questions using available tools. You have access to the following tools:

{tools}

IMPORTANT: Choose the right tool based on the question type:
- Use english_search_document ONLY for English grammar, vocabulary, and language skills questions
- Use search_web for current events, facts about people/places, and general knowledge

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do and which tool is appropriate
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action in JSON format. 
   For english_search_document, use: {{"query": "your search query", "max_results": 5}}. 
   For search_web, use: "your search query"
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)

**When you have enough information, finish with:**
Thought: I now know the final answer
Final Answer: <your answer here>

Begin!

Question: {input}
{agent_scratchpad}"""
        )
        
        # Initialize the agent
        self.agent_executor = self._init_agent()
    
    def _init_agent(self):
        """
        Create ReAct agent that works with @tool decorated functions.
        
        This uses create_react_agent which:
        - Works with all LLMs including Ollama
        - Compatible with modern @tool decorated functions
        - Has better error handling and parsing
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
            return_intermediate_steps=True  # Better debugging
        )
        
        return agent_executor
    
    def answer_questions(self, question: str):
        """
        Answer questions using the agent.
        
        Args:
            question: The question to answer
            
        Returns:
            Generator yielding response chunks
        """
        # Use the agent to answer the question
        response = self.agent_executor.stream({"input": question})
        
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
