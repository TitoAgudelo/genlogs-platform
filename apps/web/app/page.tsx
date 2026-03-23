"use client";

import { useState } from "react";
import SearchForm from "./components/SearchForm";
import CarrierList from "./components/CarrierList";
import RouteMap from "./components/RouteMap";
import AIChat from "./components/AIChat";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Tab = "search" | "ai";

interface SearchResult {
  origin: string;
  destination: string;
  carriers: { carrier_name: string; trucks_per_day: number }[];
  total_carriers: number;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("search");
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [searchedCities, setSearchedCities] = useState<{
    origin: string;
    destination: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (origin: string, destination: string) => {
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ origin, destination }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      setSearchResult(data);
      setSearchedCities({ origin, destination });
    } catch {
      setError("Failed to search. Make sure the API server is running on port 8000.");
      setSearchResult(null);
      setSearchedCities(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container">
      <div className="tabs">
        <button
          className={`tab ${activeTab === "search" ? "active" : ""}`}
          onClick={() => setActiveTab("search")}
          type="button"
        >
          Route Search
        </button>
        <button
          className={`tab ${activeTab === "ai" ? "active" : ""}`}
          onClick={() => setActiveTab("ai")}
          type="button"
        >
          AI Assistant
        </button>
      </div>

      {activeTab === "search" && (
        <div>
          <div className="card">
            <SearchForm onSearch={handleSearch} loading={loading} />
          </div>

          {error && (
            <div className="error-message" style={{ marginTop: 16 }}>
              {error}
            </div>
          )}

          {loading && (
            <div className="loading" style={{ marginTop: 16 }}>
              <div className="spinner" />
              <span>Searching carriers...</span>
            </div>
          )}

          {!loading && searchedCities && (
            <div style={{ marginTop: 24 }}>
              <RouteMap
                origin={searchedCities.origin}
                destination={searchedCities.destination}
              />
            </div>
          )}

          {!loading && <CarrierList result={searchResult} />}
        </div>
      )}

      {activeTab === "ai" && (
        <div className="card">
          <AIChat />
        </div>
      )}
    </main>
  );
}
