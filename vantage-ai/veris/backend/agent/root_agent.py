import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Task, Process, LLM
from crewai.tools import tool
from backend.agent.tools.you_com_tool import search_web
from backend.agent.tools.edgar_tool import search_filings
from backend.agent.prompts import SYSTEM_PROMPT, HEAD_TO_HEAD_PROMPT, DIGEST_PROMPT

load_dotenv()

BASETEN_API_KEY = os.getenv("BASETEN_API_KEY")
BASETEN_MODEL_SLUG = os.getenv("BASETEN_MODEL_SLUG")

if not BASETEN_API_KEY or not BASETEN_MODEL_SLUG:
    raise ValueError(
        "BASETEN_API_KEY and BASETEN_MODEL_SLUG must be set in your .env file.\n"
        "Example: BASETEN_MODEL_SLUG=deepseek-ai/DeepSeek-V3.1"
    )

# Baseten Model APIs are OpenAI-compatible — CrewAI connects directly, no LiteLLM needed.
baseten_llm = LLM(
    model=f"openai/{BASETEN_MODEL_SLUG}",
    base_url="https://inference.baseten.co/v1",
    api_key=BASETEN_API_KEY,
)


# ── Wrap existing tool functions for CrewAI ───────────────────────────────────

@tool("Web search")
def web_search_tool(query: str) -> str:
    """Search the live web for news, job postings, reviews, and signals about a company."""
    return search_web(query)


@tool("SEC EDGAR search")
def edgar_search_tool(company_name: str) -> str:
    """Retrieve SEC EDGAR financial filing data for a public US company."""
    return search_filings(company_name)


# ── Agents ────────────────────────────────────────────────────────────────────

researcher = Agent(
    role="Competitive Intelligence Researcher",
    goal=(
        "Gather comprehensive, cited intelligence about a company from live web sources "
        "and SEC financial filings. Search for news, executive changes, product launches, "
        "funding rounds, customer reviews, job postings, and financial data."
    ),
    backstory=(
        "You are a seasoned competitive intelligence researcher who knows how to find "
        "signal in noise. You are persistent and resourceful. If one tool fails, you "
        "document the failure and continue gathering information with other available tools. "
        "You always cite your sources and never fabricate data."
    ),
    tools=[web_search_tool, edgar_search_tool],
    llm=baseten_llm,
    verbose=True,
)

analyst = Agent(
    role="Competitive Intelligence Analyst",
    goal=(
        "Analyse the raw research and produce a structured, risk-scored intelligence report "
        "in valid JSON format. Score financial, legal, market, and management risk 1-10. "
        "Write a strategic summary that tells a founder what to DO with this information."
    ),
    backstory=(
        "You are a senior analyst at a top-tier strategy firm. You synthesise raw data into "
        "clear, actionable intelligence. You always return valid JSON with no markdown fences. "
        "Every claim in your report has a citation."
    ),
    tools=[],
    llm=baseten_llm,
    verbose=True,
)


# ── Crew factory functions ────────────────────────────────────────────────────

def build_first_look_crew(company: str) -> Crew:
    research_task = Task(
        description=(
            f"Research '{company}' thoroughly. Use web_search_tool to find recent news, "
            f"job postings, executive changes, product launches, customer reviews (G2, Capterra), "
            f"and pricing signals. Use edgar_search_tool to retrieve SEC filing data if the company "
            f"is publicly listed. Gather as much cited evidence as possible."
        ),
        expected_output=(
            "A comprehensive collection of cited facts about the company including: "
            "business model, funding, executives, recent news, financial data (if public), "
            "hiring trends, product moves, and customer sentiment. Every fact must have a source URL."
        ),
        agent=researcher,
    )

    analysis_task = Task(
        description=(
            f"Using the research provided, produce a structured intelligence report for '{company}'. "
            f"Follow this exact JSON structure:\n{SYSTEM_PROMPT}\n"
            f"Return ONLY the JSON object. No markdown fences. No preamble."
        ),
        expected_output="A valid JSON object matching the structure defined in the system prompt.",
        agent=analyst,
        context=[research_task],
    )

    return Crew(
        agents=[researcher, analyst],
        tasks=[research_task, analysis_task],
        process=Process.sequential,
        verbose=True,
    )


def build_head_to_head_crew(company_a: str, company_b: str) -> Crew:
    research_a = Task(
        description=f"Research '{company_a}' using web_search_tool and edgar_search_tool. Gather cited facts.",
        expected_output=f"Cited intelligence facts about {company_a}.",
        agent=researcher,
    )

    research_b = Task(
        description=f"Research '{company_b}' using web_search_tool and edgar_search_tool. Gather cited facts.",
        expected_output=f"Cited intelligence facts about {company_b}.",
        agent=researcher,
    )

    comparison_task = Task(
        description=(
            f"Compare {company_a} and {company_b} using the research gathered. "
            f"Follow this JSON structure:\n{HEAD_TO_HEAD_PROMPT}\n"
            f"Return ONLY the JSON object."
        ),
        expected_output="A valid JSON comparison object with winner per category and recommendation.",
        agent=analyst,
        context=[research_a, research_b],
    )

    return Crew(
        agents=[researcher, analyst],
        tasks=[research_a, research_b, comparison_task],
        process=Process.sequential,
        verbose=True,
    )


def build_digest_crew(companies: list[str]) -> Crew:
    companies_str = ", ".join(companies)

    research_task = Task(
        description=(
            f"Search for news from the last 7 days for each of these companies: {companies_str}. "
            f"Use web_search_tool with queries like '[company] news this week' and "
            f"'[company] product launch funding announcement'. Gather cited signals."
        ),
        expected_output="Cited recent news signals for each company with source URLs.",
        agent=researcher,
    )

    digest_task = Task(
        description=(
            f"Generate a Monday morning competitive digest for these companies: {companies_str}. "
            f"Follow this JSON structure:\n{DIGEST_PROMPT}\n"
            f"Keep the full digest under 200 words — it will be read aloud. "
            f"Return ONLY the JSON object."
        ),
        expected_output="A valid JSON digest object with severity-tagged signals and recommended action.",
        agent=analyst,
        context=[research_task],
    )

    return Crew(
        agents=[researcher, analyst],
        tasks=[research_task, digest_task],
        process=Process.sequential,
        verbose=True,
    )
