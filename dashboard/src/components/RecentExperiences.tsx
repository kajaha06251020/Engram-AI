"use client";

import { motion } from "framer-motion";
import { Experience } from "@/lib/types";

function valenceColor(v: number): string {
  if (v >= 0.5) return "text-engram-green";
  if (v > 0) return "text-engram-green opacity-60";
  if (v > -0.5) return "text-engram-red opacity-60";
  return "text-engram-red";
}

export default function RecentExperiences({
  experiences,
}: {
  experiences: Experience[];
}) {
  const recent = [...experiences]
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
    .slice(0, 10);

  return (
    <div className="rounded-xl bg-engram-card border border-engram-border p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-xs uppercase tracking-wider text-engram-green opacity-80">
          Recent Experiences
        </h3>
        <a
          href="/experiences"
          className="text-xs text-gray-500 hover:text-gray-300"
        >
          View All
        </a>
      </div>
      {recent.length === 0 ? (
        <div className="text-sm text-gray-500">
          No experiences recorded yet.
        </div>
      ) : (
        <div className="space-y-2">
          {recent.map((exp, i) => (
            <motion.div
              key={exp.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex justify-between items-center py-1.5 border-l-2 pl-3"
              style={{
                borderColor: exp.valence >= 0 ? "#34d399" : "#f87171",
              }}
            >
              <span className="text-sm text-gray-300 truncate mr-4">
                {exp.action}
              </span>
              <span className={`text-sm font-mono ${valenceColor(exp.valence)}`}>
                {exp.valence > 0 ? "+" : ""}
                {exp.valence.toFixed(1)}
              </span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
