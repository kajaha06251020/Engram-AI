"use client";

import { ProjectProvider } from "@/contexts/ProjectContext";
import NavTabs from "@/components/NavTabs";
import ProjectSelector from "@/components/ProjectSelector";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProjectProvider>
      <header className="border-b border-engram-border px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-engram-purple to-purple-400" />
            <span className="font-bold text-sm">Engram-AI</span>
            <ProjectSelector />
          </div>
          <NavTabs />
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-6">{children}</main>
    </ProjectProvider>
  );
}
