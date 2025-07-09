from llm.llm_factory import get_llm
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from tools.legacy_tools_registry import get_legacy_tools
from langchain.agents import AgentExecutor
from langchain.agents import create_react_agent




class DynamicLawExamAgent:
    '''
    
    DynamicLawExamAgent does the following things.

    LLM decide whether to use vectore store or tool and we give the control to them
    
    '''
    def __init__(self, llm_provider: str, llm_model: str, llm_host: str, tools: list[str]):
        # get the specific llm by providing provider , model name and host
        self.llm = get_llm(llm_provider, llm_model, llm_host)

        # vector store for each topic - vector store has collection for each topic
        # external tools as well
        self.tools = get_legacy_tools(tools)

        # get prompt template for react
        # agent_scratchpad - Stores previous agent thoughts, actions, observations during reasoning
        # tools - tools description and names
        self.prompt = PromptTemplate.from_template(
            '''
            Answer the following questions as best you can. You have access to the following tools:

            {tools}

            Use the following format:

            Question: the input question you must answer
            Thought: you should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question

            Begin!

            Question: {input}
            {agent_scratchpad}
            '''
        )

        self.agent = self._init_agent()

        



    def _init_agent(self):
        '''
        create_react_agent Tells the agent what tools exist

        Bakes tool names + descriptions into the prompt (ReAct format)

        Gives the LLM a way to plan tool usage (e.g. "Action: LegalNewsTool")
        
        '''
        agent = create_react_agent(llm= self.llm,tools= self.tools, prompt=self.prompt)  

        '''
        Actually executes the actions the LLM chooses

        Maps tool names to actual Python functions

        Handles calling tool.func() when the LLM says Action: SomeTool
        '''
        return AgentExecutor(
            name ="DynamicLawAgent",
            agent=agent,
            tools=self.tools,
            verbose=True, # to print everything happening inside agent cl
            handle_parsing_errors=True # if agent do not know how to parse output, it can retry
        )


    def answer_questions(self, question: str) -> str:
        return self.agent.stream({"input": question})
