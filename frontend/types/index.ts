// ─── API Response Types ───────────────────────────────────────

export interface ApiError {
  detail: string;
  status_code: number;
}

// ─── Resume Types ─────────────────────────────────────────────

export interface ResumeUploadResponse {
  resume_id: string;
  filename: string;
  extracted_text: string;
  skills: string[];
  experience_years: number;
}

// ─── GitHub Types ─────────────────────────────────────────────

export interface GitHubAnalysisResponse {
  github_username: string;
  repositories: Repository[];
  languages: Record<string, number>;
  total_stars: number;
  total_forks: number;
  contribution_score: number;
}

export interface Repository {
  name: string;
  description: string | null;
  language: string | null;
  stars: number;
  forks: number;
  url: string;
  topics: string[];
}

// ─── Analysis Types ───────────────────────────────────────────

export interface AnalysisRequest {
  resume_id?: string;
  github_username?: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  developer_score: DeveloperScore;
  skills: SkillAnalysis;
  github_insights: GitHubInsights;
  strengths: string[];
  weaknesses: string[];
}

export interface DeveloperScore {
  overall: number;
  categories: ScoreCategory[];
}

export interface ScoreCategory {
  name: string;
  score: number;
  max_score: number;
  description: string;
}

export interface SkillAnalysis {
  technical_skills: Skill[];
  soft_skills: Skill[];
  missing_skills: Skill[];
}

export interface Skill {
  name: string;
  level: "beginner" | "intermediate" | "advanced" | "expert";
  category: string;
}

export interface GitHubInsights {
  activity_level: string;
  top_languages: string[];
  project_diversity: number;
  code_quality_indicators: string[];
  collaboration_score: number;
}

// ─── Recommendation Types ─────────────────────────────────────

export interface PortfolioSuggestion {
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  category: string;
  action_items: string[];
}

export interface ProjectIdea {
  title: string;
  description: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  technologies: string[];
  estimated_time: string;
  impact_score: number;
  learning_outcomes: string[];
}

export interface CareerRoadmap {
  current_level: string;
  target_level: string;
  timeline: string;
  milestones: Milestone[];
}

export interface Milestone {
  title: string;
  description: string;
  timeframe: string;
  skills_to_learn: string[];
  projects_to_build: string[];
  resources: Resource[];
  completed: boolean;
}

export interface Resource {
  title: string;
  url: string;
  type: "course" | "book" | "tutorial" | "documentation" | "tool";
}

// ─── UI State Types ───────────────────────────────────────────

export interface AnalysisState {
  step: "idle" | "uploading" | "analyzing" | "loading-results" | "complete" | "error";
  progress: number;
  resumeId?: string;
  analysisId?: string;
  error?: string;
}

// ─── Benchmark Types ──────────────────────────────────────────

export interface ArchetypeDetail {
  key: string;
  label: string;
  description: string;
  average_overall: number;
  fit_score: number;
}

export interface BenchmarkResponse {
  analysis_id: string;
  closest_archetype: string;
  closest_archetype_label: string;
  score_percentile: number;
  developer_overall: number;
  benchmark_scores: Record<string, number>;
  archetype_details: ArchetypeDetail[];
}

// ─── Comparison Types ─────────────────────────────────────────

export interface DimensionComparison {
  dimension: string;
  developer_a: number;
  developer_b: number;
  difference: number;
}

export interface SkillGapEntry {
  skill: string;
  present_in: "developer_a" | "developer_b";
}

export interface CompareResponse {
  analysis_id_a: string;
  analysis_id_b: string;
  score_difference: number;
  dimension_comparison: DimensionComparison[];
  skill_gap: SkillGapEntry[];
  github_activity_diff: number;
  winner: "developer_a" | "developer_b" | "tie";
  summary: string;
}

// ─── Radar Chart Types ───────────────────────────────────────

export interface RadarDataPoint {
  dimension: string;
  value: number;
  fullMark: number;
}
