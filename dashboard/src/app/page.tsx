"use client";

import { useApi } from "@/hooks/useApi";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Status, Experience, GraphData } from "@/lib/types";
import StatsCards from "@/components/StatsCards";
import ValenceTrend from "@/components/ValenceTrend";
import MiniGraph from "@/components/MiniGraph";
import RecentExperiences from "@/components/RecentExperiences";

export default function OverviewPage() {
  const { data: status, setData: setStatus } = useApi<Status>("/api/status");
  const { data: experiences, setData: setExperiences } =
    useApi<Experience[]>("/api/experiences");
  const { data: graph } = useApi<GraphData>("/api/graph");

  useWebSocket({
    "experience.recorded": (data) => {
      const exp = data as Experience;
      setExperiences((prev) => (prev ? [exp, ...prev] : [exp]));
      setStatus((prev) =>
        prev
          ? { ...prev, total_experiences: prev.total_experiences + 1 }
          : prev
      );
    },
    "skill.crystallized": () => {
      setStatus((prev) =>
        prev
          ? {
              ...prev,
              total_skills: prev.total_skills + 1,
              unapplied_skills: prev.unapplied_skills + 1,
            }
          : prev
      );
    },
  });

  return (
    <div className="space-y-6">
      <StatsCards status={status} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ValenceTrend experiences={experiences ?? []} />
        <MiniGraph graph={graph} />
      </div>
      <RecentExperiences experiences={experiences ?? []} />
    </div>
  );
}
