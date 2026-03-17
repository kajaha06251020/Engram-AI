"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface ProjectContextType {
  project: string;
  setProject: (p: string) => void;
}

const ProjectContext = createContext<ProjectContextType>({
  project: "default",
  setProject: () => {},
});

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [project, setProject] = useState("default");
  return (
    <ProjectContext.Provider value={{ project, setProject }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  return useContext(ProjectContext);
}
