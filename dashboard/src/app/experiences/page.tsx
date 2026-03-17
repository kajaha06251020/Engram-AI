"use client";

import React, { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Experience, SearchResult } from "@/lib/types";

function valenceBadge(v: number) {
  const color =
    v >= 0.5
      ? "bg-engram-green/20 text-engram-green"
      : v > 0
        ? "bg-engram-green/10 text-engram-green/60"
        : v > -0.5
          ? "bg-engram-red/10 text-engram-red/60"
          : "bg-engram-red/20 text-engram-red";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono ${color}`}>
      {v > 0 ? "+" : ""}
      {v.toFixed(2)}
    </span>
  );
}

export default function ExperiencesPage() {
  const { data: experiences, setData: setExperiences } =
    useApi<Experience[]>("/api/experiences");
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [filter, setFilter] = useState<
    "all" | "positive" | "negative" | "pending"
  >("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [sortBy, setSortBy] = useState<"timestamp" | "valence">("timestamp");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useWebSocket({
    "experience.recorded": (data) => {
      setExperiences((prev) =>
        prev ? [data as Experience, ...prev] : [data as Experience]
      );
    },
  });

  const handleSearch = async () => {
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const res = await fetch(
        `/api/experiences/search?q=${encodeURIComponent(query)}&k=10`
      );
      setSearchResults(await res.json());
    } finally {
      setSearching(false);
    }
  };

  const filtered = (experiences ?? []).filter((exp) => {
    if (filter === "positive") return exp.valence > 0;
    if (filter === "negative") return exp.valence < 0;
    if (filter === "pending") return exp.status === "pending";
    return true;
  });

  const toggleSort = (col: "timestamp" | "valence") => {
    if (sortBy === col) {
      setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(col);
      setSortOrder("desc");
    }
  };

  const sorted = [...filtered].sort((a, b) => {
    const mul = sortOrder === "asc" ? 1 : -1;
    if (sortBy === "valence") return (a.valence - b.valence) * mul;
    return (new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()) * mul;
  });

  const displayList = searchResults
    ? [
        ...searchResults.best.map((r) => r.experience),
        ...searchResults.avoid.map((r) => r.experience),
      ]
    : sorted;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Search experiences..."
          className="flex-1 bg-engram-card border border-engram-border rounded-lg px-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-engram-purple"
        />
        <button
          onClick={handleSearch}
          disabled={searching}
          className="px-4 py-2 bg-engram-purple/20 text-engram-purple rounded-lg text-sm hover:bg-engram-purple/30 transition-colors disabled:opacity-50"
        >
          {searching ? "..." : "Search"}
        </button>
      </div>

      <div className="flex gap-2">
        {(["all", "positive", "negative", "pending"] as const).map((f) => (
          <button
            key={f}
            onClick={() => {
              setFilter(f);
              setSearchResults(null);
            }}
            className={`px-3 py-1 rounded-lg text-xs capitalize ${
              filter === f
                ? "bg-engram-purple/20 text-engram-purple"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="rounded-xl bg-engram-card border border-engram-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-engram-border text-gray-500 text-xs uppercase">
              <th className="text-left p-3">Action</th>
              <th className="text-left p-3">Context</th>
              <th className="text-left p-3">Outcome</th>
              <th
                className="text-center p-3 cursor-pointer hover:text-gray-300"
                onClick={() => toggleSort("valence")}
              >
                Valence {sortBy === "valence" ? (sortOrder === "asc" ? "↑" : "↓") : ""}
              </th>
              <th
                className="text-right p-3 cursor-pointer hover:text-gray-300"
                onClick={() => toggleSort("timestamp")}
              >
                Time {sortBy === "timestamp" ? (sortOrder === "asc" ? "↑" : "↓") : ""}
              </th>
            </tr>
          </thead>
          <tbody>
            {displayList.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-gray-500">
                  No experiences found.
                </td>
              </tr>
            ) : (
              displayList.map((exp) => (
                <React.Fragment key={exp.id}>
                  <tr
                    onClick={() =>
                      setExpandedId(expandedId === exp.id ? null : exp.id)
                    }
                    className="border-b border-engram-border/50 hover:bg-engram-border/20 cursor-pointer"
                  >
                    <td className="p-3 text-gray-300 max-w-[200px] truncate">
                      {exp.action}
                    </td>
                    <td className="p-3 text-gray-400 max-w-[150px] truncate">
                      {exp.context}
                    </td>
                    <td className="p-3 text-gray-400 max-w-[200px] truncate">
                      {exp.outcome}
                    </td>
                    <td className="p-3 text-center">{valenceBadge(exp.valence)}</td>
                    <td className="p-3 text-right text-gray-500 text-xs">
                      {new Date(exp.timestamp).toLocaleString()}
                    </td>
                  </tr>
                  {expandedId === exp.id && (
                    <tr>
                      <td colSpan={5} className="p-4 bg-engram-bg/50 text-xs">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <strong className="text-gray-400">ID:</strong>{" "}
                            <span className="text-gray-500 font-mono">{exp.id}</span>
                          </div>
                          <div>
                            <strong className="text-gray-400">Status:</strong>{" "}
                            <span className="text-gray-500">{exp.status}</span>
                          </div>
                          <div className="col-span-2">
                            <strong className="text-gray-400">Action:</strong>{" "}
                            <span className="text-gray-300">{exp.action}</span>
                          </div>
                          <div className="col-span-2">
                            <strong className="text-gray-400">Context:</strong>{" "}
                            <span className="text-gray-300">{exp.context}</span>
                          </div>
                          <div className="col-span-2">
                            <strong className="text-gray-400">Outcome:</strong>{" "}
                            <span className="text-gray-300">{exp.outcome}</span>
                          </div>
                          <div className="col-span-2">
                            <strong className="text-gray-400">Metadata:</strong>{" "}
                            <span className="text-gray-500 font-mono">
                              {JSON.stringify(exp.metadata)}
                            </span>
                          </div>
                          {exp.parent_id && (
                            <div className="col-span-2">
                              <strong className="text-gray-400">Parent:</strong>{" "}
                              <span className="text-blue-400 font-mono text-xs">
                                {exp.parent_id.slice(0, 8)}...
                              </span>
                            </div>
                          )}
                          {exp.related_ids?.length > 0 && (
                            <div className="col-span-2">
                              <strong className="text-gray-400">Related:</strong>{" "}
                              <span className="text-gray-300">
                                {exp.related_ids.length} related experience(s)
                              </span>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
