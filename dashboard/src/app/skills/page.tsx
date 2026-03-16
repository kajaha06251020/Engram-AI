"use client";

import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Skill } from "@/lib/types";
import { motion } from "framer-motion";

export default function SkillsPage() {
  const {
    data: skills,
    setData: setSkills,
    refetch,
  } = useApi<Skill[]>("/api/skills");
  const [crystallizing, setCrystallizing] = useState(false);
  const [evolving, setEvolving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useWebSocket({
    "skill.crystallized": (data) => {
      setSkills((prev) =>
        prev ? [...prev, data as Skill] : [data as Skill]
      );
    },
  });

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const handleCrystallize = async () => {
    setCrystallizing(true);
    try {
      const res = await fetch("/api/crystallize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const result = await res.json();
      showToast(`Crystallized ${result.length} skill(s)`);
      refetch();
    } catch {
      showToast("Crystallize failed");
    } finally {
      setCrystallizing(false);
    }
  };

  const handleEvolve = async () => {
    setEvolving(true);
    try {
      const res = await fetch("/api/evolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const result = await res.json();
      showToast(result ? "Config evolved!" : "No unapplied skills");
      refetch();
    } catch {
      showToast("Evolve failed");
    } finally {
      setEvolving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <button
          onClick={handleCrystallize}
          disabled={crystallizing}
          className="px-4 py-2 bg-engram-green/20 text-engram-green rounded-lg text-sm hover:bg-engram-green/30 transition-colors disabled:opacity-50"
        >
          {crystallizing ? "Crystallizing..." : "Crystallize Now"}
        </button>
        <button
          onClick={handleEvolve}
          disabled={evolving}
          className="px-4 py-2 bg-engram-amber/20 text-engram-amber rounded-lg text-sm hover:bg-engram-amber/30 transition-colors disabled:opacity-50"
        >
          {evolving ? "Evolving..." : "Evolve Config"}
        </button>
      </div>

      {toast && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-engram-card border border-engram-border rounded-lg px-4 py-2 text-sm text-gray-300"
        >
          {toast}
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(skills ?? []).length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            No skills crystallized yet.
          </div>
        ) : (
          (skills ?? []).map((skill, i) => (
            <motion.div
              key={skill.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-xl bg-engram-card border border-engram-border p-4 space-y-3"
            >
              <div>
                <h3 className="text-sm font-medium text-gray-200">
                  {skill.rule}
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  {skill.context_pattern}
                </p>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-500">Confidence</span>
                  <span className="text-gray-400 font-mono">
                    {(skill.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="h-1.5 bg-engram-border rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${skill.confidence * 100}%`,
                      background:
                        skill.confidence >= 0.8
                          ? "#34d399"
                          : skill.confidence >= 0.5
                            ? "#fbbf24"
                            : "#f87171",
                    }}
                  />
                </div>
              </div>

              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-0.5 bg-engram-purple/10 text-engram-purple rounded text-xs">
                  {skill.evidence_count} evidence
                </span>
                <span className="px-2 py-0.5 bg-engram-green/10 text-engram-green rounded text-xs">
                  +{skill.valence_summary.positive}
                </span>
                <span className="px-2 py-0.5 bg-engram-red/10 text-engram-red rounded text-xs">
                  -{skill.valence_summary.negative}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-xs ${
                    skill.applied
                      ? "bg-engram-green/10 text-engram-green"
                      : "bg-engram-amber/10 text-engram-amber"
                  }`}
                >
                  {skill.applied ? "Applied" : "Unapplied"}
                </span>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
