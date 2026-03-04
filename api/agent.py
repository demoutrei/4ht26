import os
import asyncio
from dotenv import load_dotenv

# 1. FIXED: Correct imports for AutoGen v0.4+
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo

load_dotenv()

# sanity check: ensure API key is provided
if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY must be set in environment for the LLM client")

# 2. FIXED: Added ModelInfo to satisfy the "model_info is required" error
# Groq models are not in the built-in OpenAI list, so we must define their capabilities.
llm_client = OpenAIChatCompletionClient(
    model="llama-3.1-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    model_info=ModelInfo(
        vision=False,
        function_calling=True,
        json_output=True,
        family="unknown",
    ),
)

# --- System Messages ---
PLANNER_SYSTEM_MESSAGE = """
You are a careful university admin assistant.
Your job: understand the request, plan steps, extract info.
NEVER auto-approve or send anything. Always require human review.
"""

WRITER_SYSTEM_MESSAGE = """
You are a professional document writer for university admin.
Turn the plan into polite, formal text. Use proper structure.
"""

APPROVER_SYSTEM_MESSAGE = """
You are a senior approver simulator.
Review the document. Output "DECISION: APPROVE" or "DECISION: REJECT" with a reason.
"""

# --- Agent and Team Creation ---
def create_agents():
    """Constructs the agent team and returns the user proxy and manager.

    The FastAPI router expects a tuple ``(user_proxy, manager)`` so that it
    can .initiate_chat() on the proxy and pass the manager object.
    """

    planner = AssistantAgent(
        name="Planner",
        description="Understands user request and plans next steps",
        system_message=PLANNER_SYSTEM_MESSAGE,
        model_client=llm_client,
    )

    writer = AssistantAgent(
        name="DocumentWriter",
        description="Writes professional document content",
        system_message=WRITER_SYSTEM_MESSAGE,
        model_client=llm_client,
    )

    approver = AssistantAgent(
        name="Approver",
        description="Reviews and decides approve/reject",
        system_message=APPROVER_SYSTEM_MESSAGE,
        model_client=llm_client,
    )

    # In v0.4, UserProxyAgent is a simple proxy for the actual human.
    user_proxy = UserProxyAgent(name="HumanUser")

    # 3. FIXED: Define termination conditions (v0.4 style)
    # Stop after 10 messages OR when the word "APPROVE" is mentioned.
    termination = MaxMessageTermination(max_messages=10) | TextMentionTermination("APPROVE")

    # 4. FIXED: RoundRobinGroupChat is the modern "Manager"
    manager = RoundRobinGroupChat(
        participants=[user_proxy, planner, writer, approver],
        termination_condition=termination,
    )

    return user_proxy, manager

# --- Execution Logic (v0.4 is Async) ---
async def run_workflow(user_request: str):
    """Execute the workflow end‑to‑end for a standalone script run.

    This helper is primarily intended for manual testing and will display the
    agents' internal reasoning to the console.
    """
    _, manager = create_agents()

    # Console.run_stream prints the "thought process" nicely in your terminal
    await Console(manager.run_stream(task=user_request))

if __name__ == "__main__":
    task = "Draft a memo for a staff meeting regarding the new leave policy."
    asyncio.run(run_workflow(task))