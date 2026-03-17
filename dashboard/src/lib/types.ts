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
  parent_id: string | null;
  related_ids: string[];
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
  skill_type: "positive" | "anti";
  status: "active" | "superseded";
  conflicts_with: string[];
  reinforcement_count: number;
  last_reinforced_at: string | null;
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
  skill_type?: "positive" | "anti";
  status?: "active" | "superseded";
  conflicts_with?: string[];
  parent_id?: string | null;
  related_ids?: string[];
}

export interface GraphEdge {
  source: string;
  target: string;
  type: "source" | "similarity" | "chain" | "related" | "conflict";
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

export interface SchedulerStatus {
  enabled: boolean;
  running: boolean;
  next_decay: string | null;
  next_conflict_check: string | null;
  crystallize_threshold: number;
  experience_counts: Record<string, number>;
}
