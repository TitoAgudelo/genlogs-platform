"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AIResult {
  query: string;
  sql: string;
  results: Record<string, string | number>[];
  explanation: string;
}

const SUGGESTIONS = [
  "Which carriers operate between New York and Washington DC?",
  "Top carriers from San Francisco to Los Angeles",
  "How many carriers operate from Dallas to Houston?",
  "Show me all UPS routes",
  "What are the busiest freight routes?",
];

export default function AIChat() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AIResult | null>(null);
  const [error, setError] = useState("");

  const handleQuery = async (text: string) => {
    const q = text.trim();
    if (!q) return;

    setLoading(true);
    setError("");
    setResult(null);
    setQuery(q);

    try {
      const res = await fetch(`${API_URL}/ai-query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch {
      setError("Failed to process query. Make sure the API server is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleQuery(query);
  };

  return (
    <div className="chat-container">
      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about freight movements... e.g. 'Which carriers go from Dallas to Houston?'"
          disabled={loading}
        />
        <button type="submit" className="btn" disabled={loading || !query.trim()}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      <div className="suggestions">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            className="suggestion-chip"
            onClick={() => {
              setQuery(s);
              handleQuery(s);
            }}
            disabled={loading}
            type="button"
          >
            {s}
          </button>
        ))}
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading && (
        <div className="loading">
          <div className="spinner" />
          <span>Processing your query...</span>
        </div>
      )}

      {result && (
        <div className="ai-response">
          <div className="ai-section">
            <div className="ai-section-header">Generated SQL</div>
            <div className="ai-section-body">
              <pre className="sql-code">{result.sql}</pre>
            </div>
          </div>

          <div className="ai-section">
            <div className="ai-section-header">Explanation</div>
            <div className="ai-section-body">
              <p className="ai-explanation">{result.explanation}</p>
            </div>
          </div>

          {result.results.length > 0 && (
            <div className="ai-section">
              <div className="ai-section-header">
                Results ({result.results.length})
              </div>
              <div className="ai-section-body">
                <table className="carrier-table">
                  <thead>
                    <tr>
                      {Object.keys(result.results[0] ?? {}).map((key) => (
                        <th key={key}>{key.replace(/_/g, " ")}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.results.map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((val, j) => (
                          <td key={j}>
                            {typeof val === "number" ? (
                              <span className="trucks-badge">{val}</span>
                            ) : (
                              val
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
