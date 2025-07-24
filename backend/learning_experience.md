# Autonomous AI Agent for the Law Exam – Personal Coaching Agent Development Experience

**Date:** Jul 24, 2025

I've been exploring **Vibe coding** with the help of tools like **Cline** and **Roo code agents**, and I've seen some compelling use cases emerge. Recently, there's been a lot of buzz around **autonomous AI agents** powered by **LLMs**, tools, and integrated resources like **databases** and **Retrieval-Augmented Generation (RAG)**.

Inspired by this trend, I've decided to build a **personal AI-powered application** tailored to my own needs.

## 🧠 Project Goal: Personal Coaching Agent

After considering various possibilities, I’ve chosen to develop a personal coaching agent with the following key features:

- Start a practice session on a chosen topic with a set number of questions  
- Request a single question on a specific topic and difficulty level  
- Submit answers to questions  
- Automatically validate user answers and provide explanations  
- Track learning progress over time  
- Adapt learning content based on user performance  
- Respond to general queries (e.g., current affairs, grammar explanations, etc.)

## 🎯 Target User

I've decided to consider **my niece** as the primary user and gather feedback directly from her. Based on this, I chose to focus the application on **specific exam coaching** rather than generalizing it as a broad product.

## 🛠️ Tech Stack and Learning Approach

Since I'm **new to both AI and the Python programming language**, I approached the project step by step. I selected the following technologies and frameworks to build the application, primarily based on:

- Strong community support  
- Comprehensive documentation  
- Availability of learning resources
## 🤖 LLM Strategy

I initially experimented with **Ollama** and various open-source models. Over time, I migrated to **OpenAI’s models** to better understand performance differences, particularly in terms of **capability** and **latency**.


## 🧰 Tech Stack

### 🔙 Backend

- **Language:** Python  
- **Frameworks:** LangChain, LangGraph  
- **Vector Database:** ChromaDB  
- **LLMs:** Ollama, OpenAI  
- **Embedding Model:** Provided via Ollama (**TODO**)  
- **Relational Database:** SQLite  
- **API Framework:** FastAPI  
- **Observability & Evaluation:**  
  - LangSmith (for tracing and evaluation)  
  - Local evaluation tools

### 🖥️ Frontend

- **Framework:** React.js

## 🧑‍⚖️ LawExamAgent – Initial Implementation

I began by setting up the backend project with a simple structure. The first step was to **install Ollama locally** and load a suitable model.

I then created a basic agent called **`LawExamAgent`**, which performs the following steps:

### 🧭 Agent Workflow

1. **Input Classification**  
   Uses an LLM to classify user input into predefined categories:  
   - `Microservice`  
   - `Law`  
   
   Only the relevant category is returned based on prompt context.

2. **Vector Retrieval**  
   Based on the classification result, relevant data is retrieved from the **vector database**.

3. **LLM Response**  
   The retrieved vector results are passed into the LLM using a structured prompt.  
   These steps are composed using **LangChain’s `runnable chain` interface**.

---

### ⚙️ Architecture Overview

The architecture follows a **chained execution model**, where:

- Each step’s output becomes the input to the next step.
- A **mapper-style pipeline** approach is used.
- I opted for the `stream()` method instead of `invoke()` to gain **incremental output visibility**, making debugging and experimentation easier.

At this stage, I **deliberately used the base `LLM` interface** (not `ChatLLM`) to keep things simple and controlled.

---

### 🤖 Evolving the Classifier

Initially, I used an **AI code agent** to generate the flow, which implemented a **rule-based classifier**. However, this didn’t feel **autonomous** enough. So I:

- Replaced the rule-based logic with an **LLM-powered classification step**.
- Accepted the **tradeoff of token cost** for a more flexible and learning-oriented system.

---

### 🧠 Vector Database Setup

The vector database (ChromaDB) is structured with **two collections**:

- One for **Microservice** content  
- One for **Law** content  

*(For testing, I even used a Microservices-related PDF to generate embeddings!)*

---

### 📚 Chunking & Embedding Strategy

Effective **chunking is critical** for preserving context during retrieval.

Thanks to **LangChain’s ChromaDB wrapper**, I could:

- Pass an embedding model during initialization  
- Automatically **chunk**, **embed**, and **store** documents  
- Maintain context integrity throughout the retrieval process

Proper chunking ensures that responses remain **relevant and coherent** during LLM interaction.

## ⚖️ DynamicLawAgent – Building a More Autonomous System

After building the initial `LawExamAgent`, I enhanced the architecture by introducing a more dynamic and flexible agent: **`DynamicLawAgent`**.

### 🔄 From Static to Dynamic Tool Use

In the earlier version:

- The LLM classified the user input into a category (`Microservice` or `Law`)
- The system then queried the vector store **based on that category**

In the **enhanced version**, the LLM is given **full autonomy** to:

- Decide **which tool to invoke** based on the user’s intent  
- Dynamically control the flow, enabling more **context-aware and adaptable behavior**

---

### 🔧 Tool Invocation via LangChain

While exploring this dynamic approach, I discovered that:

- Only certain **advanced LLMs** support **native function/tool calling** (and even then, only the latest models)
- To work around this limitation, I used **LangChain’s agent framework**, which simulates tool usage via **agent orchestration**

### 🧠 Agent Reasoning with `create_react_agent`

To implement this, I used:

```python
from langchain.agents import create_react_agent

repeating until the agent arrives at a confident final response.
(Note: While LangChain advises against using create_react_agent in production, it’s highly valuable for prototyping and learning purposes.)

- A key requirement for this type of agent is the agent_scratchpad parameter in the prompt, where the agent keeps track of intermediate reasoning steps and tool interactions.

## 🧰 Tooling Setup

For tools, I followed the **traditional approach** using the `langchain.tools.Tool` class instead of the newer `@tool` decorator. These tools were **manually bound** to the agent.

I also:

- Defined a **list of tools** within the prompt itself
- Instructed the **LLM** to **select and invoke** tools from that list as needed

--- 

### ⚙️ Agent Execution with `AgentExecutor`

Since `create_react_agent` requires an executor, I used **`AgentExecutor`** from LangChain. This component is responsible for:

- Passing the tools to the agent  
- Receiving tool selection and input from the LLM  
- Executing the selected tool  
- Routing the results back into the LLM reasoning loop

Because the LLM used here **does not natively support function-calling**, **LangChain handles all tool invocation and orchestration internally**.

### 📦 Prompt Templates & Reusability

During setup, I discovered that **LangChain provides predefined prompts** for common agent use cases. These:

- Can be **reused** out-of-the-box  
- Can also be **customized** for consistent behavior and faster prototyping

This saved time and helped ensure prompt structure followed best practices.


## ⚖️ ModernDynamicLawAgent – Enhanced Tooling with Validation

The next enhancement I explored was transitioning from the traditional `Tool` class to the **`@tool` decorator**, to better understand its capabilities and benefits.

This upgrade also provided an opportunity to implement **stricter input validation** for tool calls.

---

### 🧪 Structured Input with Pydantic

In the updated agent, **`ModernDynamicLawAgent`**, I introduced:

- **Pydantic-based input schemas** for tools  
- Enforced **structured input and validation** before tool execution

---

### 🐞 LangChain Parsing Limitation

During testing, I encountered a **known issue in LangChain**:

> When the LLM returns an action with **multiple parameters**, LangChain incorrectly assigns **all parameters to the first argument** of the tool function.

---

### ✅ Custom Validation Workaround

To address this limitation:

- I added a **validation check** on the tool input
- If the structure didn’t match the expected Pydantic schema:
  - I manually **parsed** the input
  - Then **mapped values** to the correct fields in the tool function

---

This workaround ensures:

- **Robust validation** of tool inputs  
- **Correct field mapping**, even with parsing issues  
- A more **reliable and resilient execution flow** for dynamic tool invocation

---

This step significantly improved the maintainability and correctness of tool interactions, while also preparing the architecture for production-grade input handling.

## 🧠 ModernDynamicLawExamAgentWithSessionMemory – Adding Contextual Memory

Next, I focused on incorporating **session memory** to allow the LLM to handle contextual queries like:

> “What did I ask before?”

To support this, I created a new agent called **`ModernDynamicLawExamAgentWithSessionMemory`**.

---

### 💾 Memory Management

To enable memory, I:

- Wrapped the `AgentExecutor` inside LangChain’s **`RunnableWithMessageHistory`**, which manages conversational context across user interactions  
- Used a combination of **`user_id`** and **`session_id`** to uniquely identify and retrieve **session-specific history**

---

### 🔄 Contextual Prompting

For this setup, it’s essential to:

- Pass both the **current input message** and the **conversation history** to the LLM as part of the prompt  
- This allows the agent to **reason in context** and provide **more coherent, personalized responses** over multiple turns

## 🎓 InteractiveLearningAgent – Hands-On Autonomous Agent Development

Next, I focused on feature development based on the plan I outlined earlier.

I utilized **agentic coding** to develop the initial implementation, then **refactored the code extensively** to remove unnecessary lines before committing it to the repository.

Through this process, I learned:

- New Python syntax  
- Data processing techniques  
- Best practices for building autonomous agents

My main goal was to gain **hands-on experience** with autonomous agents, understand their inner workings, and be able to debug effectively—explaining each line of code clearly.

---

### 🤖 Agent Focus & Features

I named this iteration the **`InteractiveLearningAgent`**, with a primary focus on implementing a:

- **Question-and-answer chat behavior**

At this stage, I had also integrated:

- SQL models and a database to persist user information  
- Tracking of learning performance

---

### ⚠️ Limitations Encountered

- Built as a **React agent** using LangChain’s `create_react_agent`  
- The agent formatted questions but **didn’t wait for user input**; instead, it effectively answered its own questions as part of the action-observation loop  
- This behavior is due to how `create_react_agent` works  
- Highlighted an issue with **parameter passing to tools**

I explored an alternative approach by creating a **dedicated tool-calling function**, but it didn’t work well because:

- My LLM models (Ollama and others tested) did **not support function/tool calling as expected**

---

### 🚀 Next Steps

Given these constraints, I have decided to **transition towards using LangGraph** for the next phase of development.
## LangSmith Integration for Evaluations

To assess my application’s performance, especially its correctness and memory handling, I leveraged LangSmith’s evaluation capabilities. Datasets can be created and stored either locally or via the LangSmith API.

### Local Evaluation

- The dataset is loaded from a local path.  
- For each input, the agent is called, and responses are stored in a dictionary.  
- Results are then analyzed by comparing expected vs. actual outputs to calculate a score.  
- To improve accuracy, irrelevant jargon is stripped out during comparison.

### LangSmith Evaluation

- Alternatively, datasets can be uploaded to LangSmith.  
- LangSmith handles calling the agent and running evaluations using built-in evaluators.

For now, I have focused on correctness and memory evaluation using the **ModernDynamicLawAgentWithSessionMemory**.

---

## FastAPI Integration

I chose **FastAPI** for the backend due to its support for:

- Hot reloading during development  
- Asynchronous streaming capabilities  
- Native SQLite integration  
- Automatic API documentation  
- And several other performance and developer-experience benefits

---

## Moving to LangGraph

I decided to implement the workflow by writing code directly instead of relying on external automation tools like n8n.

The workflow I created consists of three main nodes:

- **Planner Node:** Determines which tools to use or indicates if no suitable tool is available.  
- **Tool Executor:** Responsible for invoking the selected tool.  
- **Responder:** Generates a response to the user based on the tool’s output.

The workflow uses conditional edges—if the Planner finds no applicable tools, it routes directly to the Responder node.

This setup gave me the flexible, modular solution I was looking for. I also signed up with OpenAI to access the GPT-4 Turbo model for enhanced performance.

LangGraph automatically passes the agent’s state across nodes, which I further improved by integrating **Checkpointer Memory**. This memory feature allows:

- Replaying the entire state flow for debugging purposes  
- Supporting human-in-the-loop interactions by pausing and waiting for user commands before continuing tool calls or other operations

Currently, we cannot fully test the memory capacity by asking questions like “What did I ask before?” because, to manage token limits, I am not passing the entire conversation history to the model.

Additionally, I noticed that we are using OpenAI’s older ChatCompletion API rather than the newer Response API. To switch to the Response API, we simply need to set a few additional parameters in LangChain.

For more details on the Response API and how to enable it, please refer to the official documentation [here](https://platform.openai.com/docs/api-reference/response).
