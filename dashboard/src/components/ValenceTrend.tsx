"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Experience } from "@/lib/types";

export default function ValenceTrend({
  experiences,
}: {
  experiences: Experience[];
}) {
  const data = [...experiences]
    .sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
    .map((exp) => ({
      time: new Date(exp.timestamp).toLocaleDateString(),
      positive: exp.valence >= 0 ? exp.valence : 0,
      negative: exp.valence < 0 ? exp.valence : 0,
    }));

  return (
    <div className="rounded-xl bg-engram-card border border-engram-border p-4 h-full">
      <h3 className="text-xs uppercase tracking-wider text-engram-purple opacity-80 mb-4">
        Valence Trend
      </h3>
      {data.length === 0 ? (
        <div className="text-sm text-gray-500 flex items-center justify-center h-48">
          No data
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="posGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#34d399" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="negGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f87171" stopOpacity={0} />
                <stop offset="100%" stopColor="#f87171" stopOpacity={0.3} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              stroke="#2a2a4e"
            />
            <YAxis
              domain={[-1, 1]}
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              stroke="#2a2a4e"
            />
            <Tooltip
              contentStyle={{
                background: "#1a1a3e",
                border: "1px solid #2a2a4e",
                borderRadius: 8,
              }}
              labelStyle={{ color: "#94a3b8" }}
            />
            <Area
              type="monotone"
              dataKey="positive"
              stroke="#34d399"
              fill="url(#posGrad)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="negative"
              stroke="#f87171"
              fill="url(#negGrad)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
