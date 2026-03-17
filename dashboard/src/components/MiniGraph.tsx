"use client";

import { motion } from "framer-motion";
import { GraphData } from "@/lib/types";
import Link from "next/link";

export default function MiniGraph({ graph }: { graph: GraphData | null }) {
  const nodes = graph?.nodes.slice(0, 20) ?? [];

  return (
    <Link href="/graph" className="block">
      <div className="rounded-xl bg-engram-card border border-engram-border p-4 h-full hover:border-engram-purple/50 transition-colors cursor-pointer">
        <h3 className="text-xs uppercase tracking-wider text-engram-purple opacity-80 mb-4">
          Neural Graph
        </h3>
        <div className="flex items-center justify-center h-48">
          {nodes.length === 0 ? (
            <div className="text-sm text-gray-500">No data</div>
          ) : (
            <svg viewBox="0 0 200 150" className="w-full h-full">
              {nodes.map((node, i) => {
                const angle = (2 * Math.PI * i) / nodes.length;
                const cx = 100 + 60 * Math.cos(angle);
                const cy = 75 + 45 * Math.sin(angle);
                const fill =
                  node.type === "skill"
                    ? "#fbbf24"
                    : (node.valence ?? 0) >= 0
                      ? "#34d399"
                      : "#f87171";
                const r =
                  node.type === "skill"
                    ? 6
                    : 4 + Math.abs(node.valence ?? 0) * 4;
                return (
                  <motion.circle
                    key={node.id}
                    cx={cx}
                    cy={cy}
                    r={r}
                    fill={fill}
                    opacity={0.8}
                    animate={{ r: [r, r + 1.5, r] }}
                    transition={{
                      duration: 2 + i * 0.3,
                      repeat: Infinity,
                    }}
                  />
                );
              })}
            </svg>
          )}
        </div>
        <div className="text-center text-xs text-gray-500 mt-2">
          Click to explore
        </div>
      </div>
    </Link>
  );
}
