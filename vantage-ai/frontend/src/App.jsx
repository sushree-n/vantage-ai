import { useState } from "react";
import CompanySearch from "./components/CompanySearch";
import ReportView from "./components/ReportView";
import HeadToHead from "./components/HeadToHead";
import DigestView from "./components/DigestView";
import VoiceButton from "./components/VoiceButton";
import { analyzeCompany, headToHead, generateDigest } from "./api";
import "./App.css";

const MODES = ["first_look", "head_to_head", "always_on"];

export default function App() {
  const [mode, setMode] = useState("first_look");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [report, setReport] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [digest, setDigest] = useState(null);
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

  const handleAnalyze = async (company, demoMode = false) => {
    setLoading(true);
    setError(null);
    setReport(null);
    setLoadingStep(LOADING_STEPS[0]);
    const clear = runLoadingSteps();
    try {
      const res = await analyzeCompany(company, "first_look", demoMode);
      setReport(res.data.report);
    } catch (e) {
      setError(e.response?.data?.detail || "Something went wrong. Try demo mode.");
    } finally {
      setLoading(false);
      clear();
    }
  };

  const handleHeadToHead = async (companyA, companyB, demoMode = false) => {
    setLoading(true);
    setError(null);
    setComparison(null);
    setLoadingStep("Researching both companies in parallel...");
    try {
      const res = await headToHead(companyA, companyB, demoMode);
      setComparison(res.data.comparison);
    } catch (e) {
      setError(e.response?.data?.detail || "Comparison failed. Try demo mode.");
    } finally {
      setLoading(false);
    }
  };

  const handleDigest = async (companies, demoMode = false) => {
    setLoading(true);
    setError(null);
    setDigest(null);
    setLoadingStep("Scanning competitive landscape from last 7 days...");
    try {
      const res = await generateDigest(companies, demoMode);
      setDigest(res.data.digest);
    } catch (e) {
      setError(e.response?.data?.detail || "Digest failed. Try demo mode.");
    } finally {
      setLoading(false);
    }
  };

  const reportText = report
    ? `${report.company_name}. ${report.strategic_summary}`
    : comparison
    ? `Comparison: ${comparison.recommendation}`
    : digest
    ? `${digest.week_summary}. ${digest.recommended_action}`
    : null;

  return (
    <div className="app">
      <header className="header">
        <h1>Vantage<span className="dot">.</span></h1>
        <p className="tagline">Competitive intelligence for startups</p>
      </header>

      <nav className="mode-tabs">
        {MODES.map((m) => (
          <button
            key={m}
            className={`tab ${mode === m ? "active" : ""}`}
            onClick={() => { setMode(m); setReport(null); setComparison(null); setDigest(null); setError(null); }}
          >
            {m === "first_look" ? "First Look" : m === "head_to_head" ? "Head to Head" : "Always On"}
          </button>
        ))}
      </nav>

      <main className="main">
        {mode === "first_look" && (
          <CompanySearch onAnalyze={handleAnalyze} loading={loading} />
        )}
        {mode === "head_to_head" && (
          <HeadToHead onCompare={handleHeadToHead} loading={loading} />
        )}
        {mode === "always_on" && (
          <DigestView onDigest={handleDigest} loading={loading} digest={digest} />
        )}

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
        {comparison && (
          <div className="comparison-result">
            <h2>Head to Head: {comparison.company_a} vs {comparison.company_b}</h2>
            <p className="recommendation">{comparison.recommendation}</p>
            <pre>{JSON.stringify(comparison.comparison, null, 2)}</pre>
          </div>
        )}

        {reportText && (
          <VoiceButton reportText={reportText} onVoiceInput={handleAnalyze} />
        )}
      </main>
    </div>
  );
}
