# routers/agent1.py
import asyncio
from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from schemas import Instruction
from agent import create_agents
from pdf_utils import generate_memo_pdf
from db import log_request

router = APIRouter(prefix="/agent", tags=["Autonomous Agent"])

@router.post("/process")
async def process_instruction(
    instr: Instruction,
    current_user = Depends(get_current_user)
):
    id_number = current_user["id_number"]
    role = current_user["role"]

    if role not in ["student", "faculty"]:
        raise HTTPException(403, "Only students and faculty can use the agent")

    try:
        user_proxy, manager = create_agents()

        # Send instruction + role context to the agent system
        await user_proxy.initiate_chat(
            manager,
            message=f"[User role: {role} | ID: {id_number}] {instr.text}"
        )

        # Retrieve the final conversation message
        chat_history = user_proxy.chat_messages.get(manager, [])
        if not chat_history:
            raise ValueError("No response from agent team")
        final_message = chat_history[-1]["content"]

        # Very basic parsing (improve later)
        title = "University Memorandum"
        body = final_message
        recipients = "All Concerned Faculty and Staff"

        if "subject:" in final_message.lower():
            parts = final_message.lower().split("subject:")
            if len(parts) > 1:
                title = parts[1].strip().split("\n")[0].strip().capitalize()

        pdf_path = generate_memo_pdf(title, body, f"{role} {id_number}", recipients)

        request_id = log_request(
            requester_id=id_number,
            instruction=instr.text,
            intent="memo",
            pdf_path=pdf_path
        )

        return {
            "status": "draft_generated",
            "request_id": request_id,
            "pdf_path": pdf_path,
            "title": title,
            "preview": body[:250] + "..." if len(body) > 250 else body,
            "message": "Draft created. Human approval required."
        }

    except Exception as e:
        raise HTTPException(500, f"Agent error: {str(e)}")