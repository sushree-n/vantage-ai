import os
import json
import requests
from backend.rag.retriever import retrieve_from_cache

EDGAR_BASE = "https://data.sec.gov"
EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"
USER_AGENT = "VantageAI team@vantage-ai.com"  # Required by SEC EDGAR

# Map common tickers to CIK numbers for fast lookup
TICKER_TO_CIK = {
    "CRM": "0001108524",   # Salesforce
    "HUBS": "0001404655",  # HubSpot
    "MSFT": "0000789019",  # Microsoft
    "GOOGL": "0001652044", # Alphabet
    "AMZN": "0001018724",  # Amazon
    "AAPL": "0000320193",  # Apple
    "META": "0001326801",  # Meta
    "ORCL": "0001341439",  # Oracle
    "SAP": "0000723254",   # SAP
    "NOW": "0001373715",   # ServiceNow
}


def search_filings(company_name: str, filing_type: str = "10-K") -> str:
    """
    Retrieve SEC EDGAR financial filing data for a public company.
    Use this to get authoritative financial information including revenue trends,
    debt levels, risk factors, executive compensation, and material events.
    Only works for US-listed public companies — returns a clear message for
    private companies so you can note this in the report.

    Args:
        company_name: Company name or ticker symbol, e.g. "Salesforce" or "CRM"
        filing_type: SEC filing type — "10-K" (annual), "10-Q" (quarterly),
                     "8-K" (material events). Defaults to "10-K".

    Returns:
        Relevant excerpts from the most recent filing with citation reference.
    """
    company_upper = company_name.upper().strip()

    # Step 1: Check pre-cached RAG data first (fast path for demo companies)
    cached = retrieve_from_cache(company_upper)
    if cached:
        return f"[FROM CACHED FILINGS — {company_upper}]\n\n{cached}"

    # Step 2: Try CIK lookup from known tickers
    cik = TICKER_TO_CIK.get(company_upper)

    # Step 3: Fall back to EDGAR full-text search
    if not cik:
        cik = _search_cik_by_name(company_name)

    if not cik:
        return (
            f"[PRIVATE OR NOT FOUND] No SEC EDGAR filings found for '{company_name}'. "
            f"This is likely a private company. Populate financial data from web sources only "
            f"and note 'N/A — private company' in the financial_health.source field."
        )

    # Step 4: Fetch the most recent filing
    return _fetch_filing_summary(cik, company_name, filing_type)


def _search_cik_by_name(company_name: str) -> str | None:
    """Search EDGAR for a company CIK by name."""
    try:
        response = requests.get(
            f"{EDGAR_BASE}/cgi-bin/browse-edgar",
            params={
                "company": company_name,
                "CIK": "",
                "type": "10-K",
                "dateb": "",
                "owner": "include",
                "count": "5",
                "search_text": "",
                "action": "getcompany",
                "output": "atom",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        # Parse CIK from response (simplified — full impl would parse XML)
        if "CIK=" in response.text:
            cik_start = response.text.find("CIK=") + 4
            cik_end = response.text.find("&", cik_start)
            return response.text[cik_start:cik_end].zfill(10)
    except Exception:
        pass
    return None


def _fetch_filing_summary(cik: str, company_name: str, filing_type: str) -> str:
    """Fetch and summarise key sections from the most recent filing."""
    try:
        # Get filing list
        submissions_url = f"{EDGAR_BASE}/submissions/CIK{cik}.json"
        resp = requests.get(
            submissions_url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])

        # Find most recent matching filing
        for i, form in enumerate(forms):
            if form == filing_type:
                accession = accession_numbers[i].replace("-", "")
                date = filing_dates[i]
                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik)}/{accession}/"
                )
                return (
                    f"[SEC {filing_type} FILING — {company_name}]\n"
                    f"Filed: {date}\n"
                    f"Source: {filing_url}\n\n"
                    f"Filing located. Use this citation reference in your report: "
                    f"'SEC {filing_type} filed {date}'. "
                    f"Key financial data should be retrieved from the RAG cache for this company. "
                    f"If not cached, note the filing date and URL as the citation source."
                )

        return (
            f"[NO {filing_type} FOUND] No {filing_type} filing found for {company_name} "
            f"(CIK: {cik}). Try filing_type='10-Q' or '8-K'."
        )

    except Exception as e:
        return f"[ERROR] Failed to fetch EDGAR data for {company_name}: {str(e)}"
