from llm.llm_factory import get_llm
from langchain_core.prompts import PromptTemplate
from retrievers.vector_store_factory import get_vector_store
from langchain.schema.runnable import RunnableMap
from retrievers.chroma_retrievers import ChromaRetriever
from agents.law_exam_agent import LawExamAgent
from agents.dynamic_law_exam_agent import DynamicLawExamAgent
from agents.modern_dynamic_law_agent import ModernDynamicLawAgent
from agents.modern_dynamic_law_agent_session_memory import ModernDynamicLawAgentWithSessionMemory









'''

# get the law agent
law_agent = LawExamAgent(llm_provider="ollama", llm_model="llama3", llm_host="http://localhost:11434")

response =law_agent.answer_questions("Give me sample question from CLAT last exam in English and Comprehension with answer")
for chunk in response:
      print(chunk, end="", flush=True) # python command to flush immediately from buffer


# get the dynamic law agent

law_agent_dynamic = DynamicLawExamAgent(llm_provider="ollama", llm_model="llama3", llm_host="http://localhost:11434", tools=["search_document"])

response =law_agent_dynamic.answer_questions("what is microservice in 2 sentence")
for chunk in response:
      print(chunk, end="", flush=True) # python command to flush immediately from buffer


law_agent_dynamic = ModernDynamicLawAgent(llm_provider="ollama", llm_model="llama3", llm_host="http://localhost:11434", tools=["english_search_document", "search_web"])

response =law_agent_dynamic.answer_questions("current president of Germany")
for chunk in response:
      print(chunk, end="", flush=True) # python command to flush immediately from buffer

'''

law_agent_dynamic = ModernDynamicLawAgentWithSessionMemory(llm_provider="ollama", llm_model="llama3", llm_host="http://localhost:11434", tools=["english_search_document", "search_web"])

# First question
print("=== First Question ===")
response = law_agent_dynamic.answer_questions("current president of Germany", 12, "user_session_123")
print("Response:", response.get('output', response))
print()

# Second question - testing memory
print("=== Second Question (Testing Memory) ===")
response = law_agent_dynamic.answer_questions("what did I ask before", 12, "user_session_123")
print("Response:", response.get('output', response))
print()

# Check chat history
print("=== Chat History ===")
print("Chat history:", response.get('chat_history', []))
