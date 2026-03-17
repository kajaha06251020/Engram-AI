"use client";

import { motion } from "framer-motion";
import { Status } from "@/lib/types";

const cards = [
  {
    key: "experiences",
    label: "Experiences",
    field: "total_experiences" as const,
    color: "text-engram-purple-light",
    bg: "bg-engram-purple/10",
  },
  {
    key: "skills",
    label: "Skills",
    field: "total_skills" as const,
    color: "text-engram-green-light",
    bg: "bg-engram-green/10",
  },
  {
    key: "unapplied",
    label: "Unapplied",
    field: "unapplied_skills" as const,
    color: "text-engram-amber-light",
    bg: "bg-engram-amber/10",
  },
];

export default function StatsCards({ status }: { status: Status | null }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {cards.map((card, i) => (
        <motion.div
          key={card.key}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className={`rounded-xl ${card.bg} border border-engram-border p-6 text-center`}
        >
          <div
            className={`text-xs uppercase tracking-wider ${card.color} opacity-80`}
          >
            {card.label}
          </div>
          <div className={`text-4xl font-bold mt-2 ${card.color}`}>
            {status?.[card.field] ?? 0}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
