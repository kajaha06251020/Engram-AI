export interface Experience {
  id: string;
  schema_version: number;
  action: string;
  context: string;
  outcome: string;
  valence: number;
  timestamp: string;
  metadata: Record<string, unknown>;
  status: string;
}

export interface Skill {
  id: string;
  schema_version: number;
  rule: string;
  context_pattern: string;
  confidence: number;
  source_experiences: string[];
  evidence_count: number;
  valence_summary: { positive: number; negative: number };
  created_at: string;
  applied: boolean;
}

export interface Status {
  total_experiences: number;
  total_skills: number;
  unapplied_skills: number;
}

export interface GraphNode {
  id: string;
  type: "experience" | "skill";
  label: string;
  valence?: number;
  confidence?: number;
  timestamp?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: "source" | "similarity";
  weight?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchResult {
  best: Array<{ experience: Experience; score: number }>;
  avoid: Array<{ experience: Experience; score: number }>;
}
