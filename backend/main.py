from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents.modern_dynamic_law_agent_session_memory import ModernDynamicLawAgentWithSessionMemory
from config import Config
from pydantic import BaseModel
from agents.agent_factory import get_agent
from ingestion.ingest import get_data_ingestor
from typing import Optional
import logging






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

class HumanApprovalInput(BaseModel):
    user_id: str
    session_id: str
    decision: str  # "approve", "reject", "modify"
    feedback_message: Optional[str] = None


@app.post("/chat")
async def chat(input: ChatInput):
    try:
        # Call the agent with human feedback enabled
        response = agent.answer_questions(
            input.question,
            input.user_id,
            input.session_id,
            human_feedback_enabled=True  # Force enable for testing, if its empty rely on config
        )
        
        # Check if workflow was interrupted and needs approval
        if response.get('interrupted') and response.get('needs_approval'):
            # Get workflow state for approval details
            workflow = agent.workflow
            thread_config = {
                "configurable": {
                    "thread_id": f"{input.user_id}_{input.session_id}"
                }
            }
            current_state = workflow.get_state(thread_config)
            
            if current_state and current_state.values.get("needs_human_approval", False):
                # Workflow is interrupted and waiting for approval
                pending_review = current_state.values.get("pending_human_review", "")
                confidence_score = current_state.values.get("confidence_score", 0.0)
                plan = current_state.values.get("plan", {})
                
                return {
                    "needs_approval": True,
                    "confidence_score": confidence_score,
                    "plan_reasoning": plan.get("reasoning", ""),
                    "tools_to_use": plan.get("tools_to_use", []),
                    "pending_review": pending_review,
                    "message": f"This action requires approval (confidence: {confidence_score:.2f}). Please review and decide.",
                    "user_id": input.user_id,
                    "session_id": input.session_id
                }
        
        # Normal response
        return {"response": response.get('output', response), "chat_history": response.get('chat_history', [])}
        
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return {"response": f"I apologize, but I encountered an error: {str(e)}", "chat_history": []}


@app.post("/human-approval")
async def submit_human_approval(input: HumanApprovalInput):
    """
    Submit human approval decision and resume interrupted workflow
    """
    try:
        # Validate decision
        if input.decision not in ["approve", "reject", "modify"]:
            raise HTTPException(status_code=400, detail="Invalid decision. Must be 'approve', 'reject', or 'modify'")
        
        # Get the agent's workflow instance
        workflow = agent.workflow
        
        # Create thread configuration
        thread_config = {
            "configurable": {
                "thread_id": f"{input.user_id}_{input.session_id}"
            }
        }
        
        # Get current state
        current_state = workflow.get_state(thread_config)
        
        if not current_state or not current_state.values.get("needs_human_approval", False):
            raise HTTPException(status_code=404, detail="No pending approval found for this session")
        
        # Update state with human decision
        updated_values = {
            **current_state.values,
            "human_decision": input.decision,
            "human_feedback_message": input.feedback_message or "",
        }
        
        # Update the workflow state
        workflow.update_state(thread_config, updated_values)
    
        
        # Resume workflow execution using streaming
        logging.info(f"Resuming workflow for {input.user_id}_{input.session_id} with decision: {input.decision}")
        
        events = []
        for event in workflow.stream(None, config=thread_config): # The None parameter in workflow.stream(None, ...) means "continue from where you left off" rather than starting with new input.
            events.append(event)
            logging.info(f"Resume event: {list(event.keys())}")
        
        # Get final state after resuming
        final_state = workflow.get_state(thread_config)
        
        # Extract the final response
        from langchain_core.messages import AIMessage
        ai_messages = [msg for msg in final_state.values["messages"] if isinstance(msg, AIMessage)]
        output = ai_messages[-1].content if ai_messages else "Workflow resumed successfully."
        
        logging.info(f"Workflow resumed successfully. Final output: {output[:100]}...")
        
        return {
            "success": True,
            "message": f"Decision '{input.decision}' submitted successfully",
            "response": output,
            "workflow_resumed": True
        }
        
    except Exception as e:
        logging.error(f"Error submitting approval decision: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing approval: {str(e)}")


@app.post("/load_data", description="Load the data into vector DB")
async def load_data():
    response = get_data_ingestor().ingest_data()
    return {"is_success": response}


# Note: Learning functionality is now integrated into the main /chat endpoint
# Users can send learning commands like:
# - "start practice [topic]"
# - "answer A/B/C/D"
# - "my progress"
# - "explain [topic]"
# - "end session"
