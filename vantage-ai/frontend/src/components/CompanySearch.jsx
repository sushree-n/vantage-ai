import { useState } from "react";

export default function CompanySearch({ onAnalyze, loading }) {
  const [company, setCompany] = useState("");

  const handleSubmit = (demo = false) => {
    if (!company.trim()) return;
    onAnalyze(company.trim(), demo);
  };

  return (
    <div className="search-box">
      <input
        className="search-input"
        type="text"
        placeholder="Enter a company name (e.g. Salesforce, Stripe...)"
        value={company}
        onChange={(e) => setCompany(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        disabled={loading}
        autoFocus
      />
      <div className="search-actions">
        <button
          className="btn-primary"
          onClick={() => handleSubmit(false)}
          disabled={loading || !company.trim()}
        >
          {loading ? "Researching..." : "Analyze →"}
        </button>
        <button
          className="btn-secondary"
          onClick={() => { setCompany("Salesforce"); handleSubmit(true); }}
          disabled={loading}
          title="Load pre-cached demo data instantly"
        >
          Demo
        </button>
      </div>
      <p className="search-hint">
        Searches live web + SEC EDGAR filings. ~90 seconds for live analysis.
      </p>
    </div>
  );
}
