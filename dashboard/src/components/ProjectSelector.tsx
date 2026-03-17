"use client";

import { useEffect, useState } from "react";
import { useProject } from "@/contexts/ProjectContext";

export default function ProjectSelector() {
  const { project, setProject } = useProject();
  const [projects, setProjects] = useState<string[]>([]);

  useEffect(() => {
    fetch("/api/projects")
      .then((r) => r.json())
      .then((data) => setProjects(data))
      .catch(() => {});
  }, []);

  return (
    <select
      value={project}
      onChange={(e) => setProject(e.target.value)}
      className="bg-engram-card border border-engram-border rounded px-2 py-1 text-xs text-gray-300"
    >
      {projects.length === 0 && <option value="default">default</option>}
      {projects.map((p) => (
        <option key={p} value={p}>
          {p}
        </option>
      ))}
    </select>
  );
}
