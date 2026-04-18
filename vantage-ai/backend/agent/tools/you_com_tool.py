import os
import requests
from dotenv import load_dotenv

load_dotenv()

YOU_COM_API_KEY = os.getenv("YOU_COM_API_KEY")
YOU_COM_BASE_URL = "https://api.ydc-index.io/search"


def search_web(query: str) -> str:
    """
    Search the live web for news, job postings, reviews, pricing, and signals
    about a company. Use this for any real-time competitive intelligence including
    recent news, executive changes, product launches, funding rounds, customer
    reviews from G2 or Capterra, and hiring trends.

    Args:
        query: Natural language search query, e.g.
               "Salesforce recent product launches 2024" or
               "HubSpot G2 customer reviews complaints"

    Returns:
        Formatted string of search results with sources and snippets.
    """
    if not YOU_COM_API_KEY:
        return "[ERROR] YOU_COM_API_KEY not set in environment."

    try:
        response = requests.get(
            YOU_COM_BASE_URL,
            headers={"X-API-Key": YOU_COM_API_KEY},
            params={
                "query": query,
                "num_web_results": 5,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        hits = data.get("hits", [])
        if not hits:
            return f"[NO RESULTS] No web results found for: {query}"

        formatted = []
        for hit in hits:
            title = hit.get("title", "No title")
            url = hit.get("url", "")
            snippet = hit.get("description", hit.get("snippets", [""])[0] if hit.get("snippets") else "")
            formatted.append(f"Source: {url}\nTitle: {title}\nSnippet: {snippet}\n")

        return "\n---\n".join(formatted)

    except requests.exceptions.Timeout:
        return f"[ERROR] You.com search timed out for query: {query}"
    except requests.exceptions.RequestException as e:
        return f"[ERROR] You.com search failed: {str(e)}"
