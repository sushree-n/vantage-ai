import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.tools.you_com_tool import search_web
from backend.agent.tools.edgar_tool import search_filings

load_dotenv()

BASETEN_MODEL_ID = os.getenv("BASETEN_MODEL_ID")

if not BASETEN_MODEL_ID:
    raise ValueError(
        "BASETEN_MODEL_ID is not set in your .env file. "
        "Find your model ID in the Baseten dashboard."
    )

# ── Root agent ────────────────────────────────────────────────────────────────
# ADK automatically:
#   - Discovers tools from function signatures + docstrings
#   - Routes to You.com and EDGAR in parallel when appropriate
#   - Handles retries and error recovery
#   - Maintains session state across follow-up questions
# ─────────────────────────────────────────────────────────────────────────────

root_agent = Agent(
    name="vantage_agent",
    model=f"litellm/baseten/{BASETEN_MODEL_ID}",
    description=(
        "Vantage — competitive intelligence co-pilot for startups. "
        "Researches companies using live web data and SEC filings, "
        "returning structured cited reports."
    ),
    instruction=SYSTEM_PROMPT,
    tools=[search_web, search_filings],
)
