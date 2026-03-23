"use client";

import { useState, useCallback } from "react";
import PlacesAutocomplete from "./PlacesAutocomplete";

interface SearchFormProps {
  onSearch: (origin: string, destination: string) => void;
  loading: boolean;
}

export default function SearchForm({ onSearch, loading }: SearchFormProps) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (origin && destination) {
      onSearch(origin, destination);
    }
  };

  const handleOriginChange = useCallback((val: string) => setOrigin(val), []);
  const handleDestinationChange = useCallback((val: string) => setDestination(val), []);

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      <PlacesAutocomplete
        id="origin"
        label="From (City)"
        placeholder="e.g. New York"
        value={origin}
        onChange={handleOriginChange}
      />

      <PlacesAutocomplete
        id="destination"
        label="To (City)"
        placeholder="e.g. Washington DC"
        value={destination}
        onChange={handleDestinationChange}
      />

      <button
        type="submit"
        className="btn"
        disabled={!origin || !destination || loading}
      >
        {loading ? "Searching..." : "Search"}
      </button>
    </form>
  );
}
