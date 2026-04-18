import os
from dotenv import load_dotenv
from youdotcom import You

load_dotenv()

YOU_COM_API_KEY = os.getenv("YOU_COM_API_KEY")


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
        with You(api_key_auth=YOU_COM_API_KEY) as you:
            results = you.search.unified(query=query, count=5)

        if not (results and results.results and results.results.web):
            return f"[NO RESULTS] No web results found for: {query}"

        formatted = []
        for result in results.results.web:
            title = result.title or "No title"
            url = result.url or ""
            snippet = result.description or (result.snippets[0] if result.snippets else "")
            formatted.append(f"Source: {url}\nTitle: {title}\nSnippet: {snippet}\n")

        return "\n---\n".join(formatted)

    except Exception as e:
        if "403 Forbidden" in str(e):
            return (
                "[ERROR] You.com search failed with 403 Forbidden. This likely means your "
                "YOU_COM_API_KEY is invalid, has expired, or your account has usage limit issues. "
                "Please check your You.com developer dashboard."
            )
        return f"[ERROR] You.com search failed: {str(e)}"
