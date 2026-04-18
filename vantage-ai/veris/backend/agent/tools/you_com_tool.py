import os
import requests
from dotenv import load_dotenv

load_dotenv()

YOU_COM_API_KEY = os.getenv("YOU_COM_API_KEY")
YOU_COM_RESEARCH_URL = "https://api.you.com/v1/research"


def search_web(query: str) -> str:
    """
    Deep research the web for competitive intelligence about a company.
    Uses You.com Research API with deep effort to return a synthesised answer
    with cited sources rather than raw snippets.

    Args:
        query: Research question or topic, e.g.
               "Salesforce revenue growth and financial health 2024" or
               "HubSpot hiring trends and headcount changes 2024"

    Returns:
        Synthesised research answer with inline source citations.
    """
    if not YOU_COM_API_KEY:
        return "[ERROR] YOU_COM_API_KEY not set in environment."

    try:
        response = requests.post(
            YOU_COM_RESEARCH_URL,
            headers={
                "X-API-Key": YOU_COM_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "research_effort": "deep",
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        answer = data.get("answer", "")
        sources = data.get("sources", data.get("search_results", []))

        if not answer:
            return f"[NO RESULTS] Research returned no answer for: {query}"

        parts = [f"Research Answer:\n{answer}"]

        if sources:
            parts.append("\nSources:")
            for src in sources[:10]:
                url = src.get("url", src.get("link", ""))
                title = src.get("title", src.get("name", ""))
                if url:
                    parts.append(f"  - {title}: {url}")

        return "\n".join(parts)

    except requests.exceptions.Timeout:
        return f"[ERROR] You.com research timed out for query: {query}"
    except requests.exceptions.RequestException as e:
        return f"[ERROR] You.com research failed: {str(e)}"
