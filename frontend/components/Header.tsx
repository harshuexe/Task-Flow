"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError, type SearchResponse } from "../lib/api";

export function Header() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const search = async (event: FormEvent) => {
    event.preventDefault();
    const value = query.trim();
    if (!value) {
      setResults(null);
      return;
    }
    setError(null);
    try {
      setResults(await api.search(value));
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Search failed.");
      setResults(null);
    }
  };

  const totalResults = results
    ? results.results.projects.length + results.results.tasks.length
    : 0;

  return (
    <header className="app-header">
      <form className="global-search" onSubmit={search} role="search">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search projects and tasks"
          aria-label="Search projects and tasks"
        />
        <button type="submit" disabled={!query.trim()}>
          Search
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {results && (
        <div className="search-results" role="region" aria-label="Search results">
          <strong>{totalResults} results for "{results.query}"</strong>
          {Object.entries(results.results).map(([group, entries]) =>
            entries.length > 0 ? (
              <section key={group}>
                <h3>{group}</h3>
                {entries.map((entry) => (
                  <div key={`${group}-${entry.id}`}>
                    {entry.title}
                    {entry.status && <small>{entry.status}</small>}
                  </div>
                ))}
              </section>
            ) : null,
          )}
        </div>
      )}
    </header>
  );
}