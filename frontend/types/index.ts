// ─── API Response Types ───────────────────────────────────────

export interface ApiError {
  detail: string;
  status_code: number;
}

// ─── Resume Types ─────────────────────────────────────────────

export interface ResumeUploadResponse {
  analysis_id: string;
  filename: string;
  extracted_text_preview: string;
  skills: Skill[];
}

// ─── GitHub Types ─────────────────────────────────────────────

export interface GitHubAnalysisResponse {
  analysis_id: string;
  summary: GitHubSummary;
}

export interface RepoSummary {
  name: string;
  description: string | null;
  language: string | null;
  stars: number;
  forks: number;
  has_readme: boolean;
  topics: string[];
}

export interface GitHubSummary {
  username: string;
  avatar_url: string | null;
  bio: string | null;
  public_repos: number;
  followers: number;
  top_languages: Record<string, number>;
  total_stars: number;
  commit_frequency: "daily" | "weekly" | "monthly" | "sporadic";
  notable_repos: RepoSummary[];
}

// ─── Analysis Types ───────────────────────────────────────────

export interface AnalysisResponse {
  analysis_id: string;
  developer_score: DeveloperScore;
  skills: Skill[];
  skill_categories: SkillCategoryBreakdown[];
  radar_scores: RadarScores | null;
  programming_languages: ProgrammingLanguageScore[];
  ai_insights: AiInsights | null;
  score_breakdown: ScoreBreakdown | null;
  github_summary: GitHubSummary | null;
  portfolio_suggestions: Suggestion[];
  project_ideas: ProjectIdea[];
  career_roadmap: CareerRoadmap | null;
}

export interface DeveloperScore {
  overall: number;
  categories: Record<string, number>;
  justification: string;
}

export interface Skill {
  name: string;
  category: string;
  proficiency: "beginner" | "intermediate" | "advanced";
  source: string;
}

// ─── Recommendation Types ─────────────────────────────────────

export interface Suggestion {
  area: string;
  current_state: string;
  recommendation: string;
  priority: "high" | "medium" | "low";
  impact: string;
}

export interface ProjectIdea {
  title: string;
  description: string;
  tech_stack: string[];
  difficulty: string;
  estimated_time: string;
  skills_developed: string[];
}

export interface CareerRoadmap {
  current_level: string;
  target_role: string;
  milestones: Milestone[];
}

export interface ProgrammingLanguageScore {
  name: string;
  proficiency: "beginner" | "intermediate" | "advanced";
  confidence: number;
  context: string;
}

export interface SkillCategoryBreakdown {
  category: string;
  skills: string[];
  score: number;
}

export interface RadarScores {
  frontend: number;
  backend: number;
  data: number;
  ml_ai: number;
  devops: number;
  docs: number;
}

export interface AiInsights {
  strengths: string[];
  weaknesses: string[];
  career_potential: string;
  recommended_improvements: string[];
}

export interface ScoreBreakdown {
  resume_completeness: number;
  content_quality: number;
  skill_diversity: number;
  formatting_quality: number;
  impact_quantification: number;
  keyword_density: number;
  github_activity: number | null;
  repo_quality: number | null;
  documentation: number | null;
  community: number | null;
}

export interface Milestone {
  timeframe: string;
  goals: string[];
  skills_to_learn: string[];
  actions: string[];
}

// ─── UI State Types ───────────────────────────────────────────

export interface AnalysisState {
  step: "idle" | "uploading" | "analyzing" | "loading-results" | "complete" | "error";
  progress: number;
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
