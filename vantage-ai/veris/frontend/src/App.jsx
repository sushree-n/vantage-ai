import { useState } from "react";
import CompanySearch from "./components/CompanySearch";
import ReportView from "./components/ReportView";
import VoiceButton from "./components/VoiceButton";
import { analyzeCompany } from "./api";
import "./App.css";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const LOADING_STEPS = [
    "Searching live web signals...",
    "Retrieving SEC filings...",
    "Synthesising intelligence report...",
    "Scoring risk factors...",
  ];

  const runLoadingSteps = () => {
    let i = 0;
    const interval = setInterval(() => {
      setLoadingStep(LOADING_STEPS[i % LOADING_STEPS.length]);
      i++;
    }, 8000);
    return () => clearInterval(interval);
  };

  const handleAnalyze = async (company) => {
    setLoading(true);
    setError(null);
    setReport(null);
    setLoadingStep(LOADING_STEPS[0]);
    const clear = runLoadingSteps();
    try {
      const res = await analyzeCompany(company, "first_look", false);
      setReport(res.data.report);
    } catch (e) {
      setError(e.response?.data?.detail || "Something went wrong.");
    } finally {
      setLoading(false);
      clear();
    }
  };

  const reportText = report
    ? `${report.company_name}. ${report.strategic_summary}`
    : null;

  return (
    <div className="app">
      <header className="header">
        <h1>Vantage<span className="dot">.</span></h1>
        <p className="tagline">Competitive intelligence for startups</p>
      </header>

      <nav className="mode-tabs">
        <button className="tab active">Analysis</button>
      </nav>

      <main className="main">
        <CompanySearch onAnalyze={handleAnalyze} loading={loading} />

        {loading && (
          <div className="loading">
            <div className="spinner" />
            <p className="loading-step">{loadingStep}</p>
          </div>
        )}

        {error && (
          <div className="error">
            <p>{error}</p>
          </div>
        )}

        {report && <ReportView report={report} />}

        {reportText && (
          <VoiceButton reportText={reportText} onVoiceInput={handleAnalyze} />
        )}
      </main>
    </div>
  );
}
