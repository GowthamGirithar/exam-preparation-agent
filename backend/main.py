from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agents.modern_dynamic_law_agent_session_memory import ModernDynamicLawAgentWithSessionMemory
from config import Config
from pydantic import BaseModel
from agents.agent_factory import get_agent




app = FastAPI()
agent = get_agent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInput(BaseModel):
    user_id: str
    question: str
    session_id: str = "default"


@app.post("/chat")
async def chat(input: ChatInput):
    response = agent.answer_questions(input.question, input.user_id, input.session_id)
    return {"response": response.get('output', response), "chat_history": response.get('chat_history', [])}

