Autonomous AI agent for the Law exam personal coaching agent developing experience 

Jul 24, 2025

I've been exploring Vibe coding with the help of tools like Cline and Roo code agents, and I've seen some compelling use cases emerge. Recently, there's been a lot of buzz around autonomous AI agents powered by LLMs, tools, and integrated resources like databases and Retrieval-Augmented Generation (RAG). Inspired by this trend, I've decided to build a personal AI-powered application tailored to my own needs.
After considering various possibilities, I’ve chosen to develop a personal coaching agent with the following key features:
Start a practice session on a chosen topic with a set number of questions
Request a single question on a specific topic and difficulty level
Submit answers to questions
Automatically validate user answers and provide explanations
Track learning progress over time
Adapt learning content based on user performance
Respond to general queries (e.g., current affairs, grammar explanations, etc.)
I've decided to consider my niece as the primary user and gather feedback directly from her. Based on this, I chose to focus the application on specific exam coaching rather than generalizing it as a broad product.
Since I'm new to both AI and the Python programming language, I approached the project step by step. I selected the following technologies and frameworks to build the application, primarily based on their strong community support, comprehensive documentation, and the availability of learning resources.
LLM Strategy
I initially experimented with Ollama and various open-source models. Over time, I migrated to OpenAI’s models to better understand performance differences, particularly in terms of capability and latency.
Tech Stack
Backend
Language: Python
Frameworks: LangChain, LangGraph
Vector Database: ChromaDB
LLMs: Ollama, OpenAI
Embedding Model: Provided via Ollama (TODO)
Relational Database: SQLite
API Framework: FastAPI
Observability & Evaluation: LangSmith (for tracing and evaluation), along with local evaluation tools
Frontend
Framework: React.js

LawExamAgent 
I began by setting up the backend project with a simple structure. The first step was to install Ollama locally and load a suitable model. I then created a basic agent called LawExamAgent, which performs the following steps:
Input Classification: It uses an LLM to classify user input into predefined categories either Microservice or Law based on the prompt. Only the relevant category is returned.
Vector Retrieval: Depending on the classified category, it retrieves relevant data from the vector database.
LLM Response: The retrieved vector results are passed into the LLM using a structured prompt. All of these steps are composed using LangChain's runnable chain interface.
The overall architecture follows a chained execution model, where each step’s output is fed as input into the next essentially a mapper-style pipeline. I used the stream() method instead of invoke() to get incremental output from the chain, which provides better visibility into intermediate results rather than waiting for a final response.
At this stage, I deliberately used only the LLM interface (not ChatLLM) to keep things simple and controlled.
Initially, when I used an AI code agent to generate this flow, it implemented a rule-based classifier for categorizing questions. However, I felt this approach wasn’t truly autonomous. So, I replaced the rule-based logic with an LLM-driven classification step. Although using an LLM incurs token costs, I chose to prioritize learning and building a more adaptable system.
The vector database is structured with two collections one for Microservice content and the other for Law. (For testing, I even used a Microservices-related PDF to generate embeddings!)
When working with vector databases, it's critical to apply a thoughtful chunking strategy to preserve context. Fortunately, LangChain’s ChromaDB wrapper provides built-in utilities for chunking and embedding. By passing an embedding model during initialization, LangChain can automatically embed and store documents appropriately. Proper chunking ensures that the context is maintained throughout the retrieval process.
DynamicLawAgent
Next, I enhanced the original LawExamAgent by introducing a more dynamic architecture with a new agent called DynamicLawAgent.
In the earlier version, the agent queried the vector store directly, based on a category classified by the LLM. In the enhanced version, I wanted to give the LLM full autonomy to decide which tool to invoke based on the user's input, making the system more dynamic and flexible.
As I explored this, I realized that only certain advanced LLMs support native function/tool calling, and even then, it's limited to the latest models. To work around this limitation, I delegated tool execution to the LangChain framework, which can simulate tool usage through agent orchestration.
To implement this, I used LangChain’s create_react_agent, which operates on a structured reasoning loop:
Thought → Action → Observation,
repeating until the agent arrives at a confident final response.
(Note: While LangChain advises against using create_react_agent in production, it’s highly valuable for prototyping and learning purposes.)
A key requirement for this type of agent is the agent_scratchpad parameter in the prompt, where the agent keeps track of intermediate reasoning steps and tool interactions.
Tooling Setup
For tools, I followed the traditional approach using the langchain.tools.Tool class instead of the newer @tooldecorator. These tools were then manually bound to the agent. I also defined a list of tools in the prompt itself and instructed the LLM to select and invoke tools from that list as needed.
Since create_react_agent needs an executor, I used AgentExecutor from LangChain. This executor is responsible for:
Passing the tools to the agent
Receiving tool selection and input from the LLM
Executing the selected tool
Routing results back into the LLM loop
Because the LLM used here does not natively support function-calling, LangChain handles all tool invocation and orchestration internally.
During this process, I also discovered that LangChain provides predefined prompts for agents within the library, which can be reused or customized for consistency and faster setup.
ModernDynamicLawAgent
The next enhancement I explored was using the @tool decorator instead of the traditional Tool class, to better understand its capabilities and potential benefits. This also gave me the opportunity to implement stricter input validation for tool calls.
In the updated agent, ModernDynamicLawAgent, I introduced Pydantic-based input schemas for the tools to enforce validation and structure. During testing, I encountered an issue in LangChain: when the LLM returns an action with multiple parameters, LangChain incorrectly assigns all parameters to the first argument of the tool function.
To address this, I implemented a validation condition. If the initial input structure didn’t match the expected schema, I manually parsed the input and mapped values to the correct fields.
This workaround ensures that even with the current parsing limitation in LangChain, tool inputs are validated and assigned correctly, allowing for more robust and reliable tool execution.
ModernDynamicLawExamAgentWithSessionMemory
Next, I became interested in incorporating session memory, allowing the LLM to handle contextual queries like “What did I ask before?” To support this, I created a new agent called ModernDynamicLawExamAgentWithSessionMemory.
To enable memory, I wrapped the AgentExecutor inside LangChain’s RunnableWithMessageHistory, which manages conversational context across user interactions. I used a combination of user_id and session_id to uniquely identify and retrieve session-specific history.
For this setup, it's essential to pass both the current input message and the conversation history to the LLM as part of the prompt. This allows the agent to reason in context and provide more coherent, personalized responses over multiple turns.













InteractiveLearningAgent 
Next, I focused on feature development based on the plan I outlined earlier. I utilized agentic coding to develop the initial implementation, then refactored the code extensively to remove unnecessary lines before committing it to the repository. Through this process, I learned new Python syntax, data processing techniques, and best practices for building autonomous agents. My main goal was to gain hands-on experience with autonomous agents, understand their inner workings, and be able to debug effectively—explaining each line of code clearly.
I named this iteration the InteractiveLearningAgent, with a primary focus on implementing a question-and-answer chat behavior. At this stage, I had also integrated SQL models and a database to persist user information and track learning performance.
However, the agent had some limitations. Since it was built as a React agent using LangChain’s create_react_agent, it formatted the questions but didn’t wait for user input; instead, it effectively answered its own questions as part of its action-observation loop. This behavior stems from how create_react_agent works and also highlighted an issue with parameter passing to tools.
I explored an alternative approach by creating a dedicated tool-calling function, but it didn’t work well because my LLM models—both in Ollama and others I tested—did not support function/tool calling as expected.
Given these constraints, I have decided to transition towards using LangGraph for the next phase of development.

Additional Implementations and Integrations Before Moving to LangGraph
Before starting development with LangGraph, I implemented several important features and integrations:
LangSmith Integration for Observability
Enabling observability with LangSmith is straightforward. By setting the following environment variables, tracing is automatically enabled for the entire application:
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY
LANGSMITH_API_URL
LANGSMITH_PROJECT
For methods that don’t involve direct LLM calls but still require tracing, we can simply add the @traceable decorator to those functions.
LangSmith Integration for Evaluations
To assess my application’s performance, especially its correctness and memory handling, I leveraged LangSmith’s evaluation capabilities. Datasets can be created and stored either locally or via the LangSmith API.
Local Evaluation:
The dataset is loaded from a local path. For each input, the agent is called, and responses are stored in a dictionary. Results are then analyzed by comparing expected vs. actual outputs to calculate a score. To improve accuracy, irrelevant jargon is stripped out during comparison.
LangSmith Evaluation:
Alternatively, datasets can be uploaded to LangSmith, which handles calling the agent and running evaluations using built-in evaluators.
For now, I have focused on correctness and memory evaluation using the ModernDynamicLawAgentWithSessionMemory.
FastAPI Integration
I chose FastAPI for the backend due to its support for:
Hot reloading during development
Asynchronous streaming capabilities
Native SQLite integration
Automatic API documentation
And several other performance and developer-experience benefits

Moving to LangGraph
I decided to implement the workflow by writing code directly instead of relying on external automation tools like n8n.
The workflow I created consists of three main nodes:
Planner Node: Determines which tools to use or indicates if no suitable tool is available.
Tool Executor: Responsible for invoking the selected tool.
Responder: Generates a response to the user based on the tool’s output.
The workflow uses conditional edges—if the Planner finds no applicable tools, it routes directly to the Responder node.
This setup gave me the flexible, modular solution I was looking for. I also signed up with OpenAI to access the GPT-4 Turbo model for enhanced performance.
LangGraph automatically passes the agent’s state across nodes, which I further improved by integrating Checkpointer Memory. This memory feature allows replaying the entire state flow for debugging purposes and supports human-in-the-loop interactions by pausing and waiting for user commands before continuing tool calls or other operations.
Currently, we cannot fully test the memory capacity by asking questions like “What did I ask before?” because, to manage token limits, I am not passing the entire conversation history to the model.
Additionally, I noticed that we are using OpenAI’s older ChatCompletion API rather than the newer Response API. To switch to the Response API, we simply need to set a few additional parameters in LangChain.
For more details on the Response API and how to enable it, please refer to the official documentation here


