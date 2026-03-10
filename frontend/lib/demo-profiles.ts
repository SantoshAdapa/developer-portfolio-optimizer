import type {
  AnalysisResponse,
  DeveloperScore,
  Skill,
  GitHubSummary,
  CareerRoadmap,
  Suggestion,
  ProjectIdea,
} from "@/types";

export interface DemoProfile {
  name: string;
  githubUrl: string;
  analysis: AnalysisResponse;
  suggestions: Suggestion[];
  projectIdeas: ProjectIdea[];
  roadmap: CareerRoadmap;
}

// ── Shared helpers ───────────────────────────────────────

function sk(
  name: string,
  category: string,
  proficiency: "beginner" | "intermediate" | "advanced",
  source = "both"
): Skill {
  return { name, category, proficiency, source };
}

// ── 1. Alex Rivera – ML Specialist ───────────────────────

const alexScore: DeveloperScore = {
  overall: 92,
  categories: {
    resume_completeness: 95,
    skill_diversity: 88,
    github_activity: 82,
    repo_quality: 90,
    documentation: 96,
    community: 94,
  },
  justification:
    "Score breakdown — Resume Completeness: strong (95/100); Skill Diversity: strong (88/100); GitHub Activity: strong (82/100); Repo Quality: strong (90/100); Documentation: strong (96/100); Community: strong (94/100).",
};

const alexSkills: Skill[] = [
  sk("Python", "language", "advanced"),
  sk("TensorFlow", "framework", "advanced"),
  sk("PyTorch", "framework", "advanced"),
  sk("Deep Learning", "framework", "advanced"),
  sk("NLP", "framework", "advanced"),
  sk("Computer Vision", "framework", "advanced"),
  sk("MATLAB", "language", "advanced"),
  sk("Jupyter", "tool", "advanced"),
  sk("Docker", "tool", "intermediate"),
  sk("Technical Writing", "soft_skill", "advanced"),
  sk("Teaching", "soft_skill", "advanced"),
  sk("Public Speaking", "soft_skill", "advanced"),
];

const alexGitHub: GitHubSummary = {
  username: "alexrivera",
  avatar_url: null,
  bio: "Machine Learning researcher and educator",
  public_repos: 25,
  followers: 50000,
  top_languages: { Python: 60, "Jupyter Notebook": 25, MATLAB: 15 },
  total_stars: 80000,
  commit_frequency: "weekly",
  notable_repos: [],
};

// ── 2. Jordan Chen – Systems Engineer ────────────────────

const jordanScore: DeveloperScore = {
  overall: 96,
  categories: {
    resume_completeness: 90,
    skill_diversity: 78,
    github_activity: 98,
    repo_quality: 99,
    documentation: 92,
    community: 99,
  },
  justification:
    "Score breakdown — Resume Completeness: strong (90/100); Skill Diversity: strong (78/100); GitHub Activity: strong (98/100); Repo Quality: strong (99/100); Documentation: strong (92/100); Community: strong (99/100).",
};

const jordanSkills: Skill[] = [
  sk("C", "language", "advanced"),
  sk("Bash", "language", "advanced"),
  sk("Git", "tool", "advanced"),
  sk("Linux Kernel", "framework", "advanced"),
  sk("Assembly", "language", "advanced"),
  sk("Makefile", "tool", "advanced"),
  sk("Perl", "language", "intermediate"),
  sk("Code Review", "soft_skill", "advanced"),
  sk("Technical Vision", "soft_skill", "advanced"),
];

const jordanGitHub: GitHubSummary = {
  username: "jordanchen",
  avatar_url: null,
  bio: "Systems engineer and open-source contributor",
  public_repos: 7,
  followers: 200000,
  top_languages: { C: 80, Shell: 15, Makefile: 5 },
  total_stars: 180000,
  commit_frequency: "daily",
  notable_repos: [],
};

// ── 3. Sample ML Engineer ────────────────────────────────

const mlEngScore: DeveloperScore = {
  overall: 68,
  categories: {
    resume_completeness: 72,
    skill_diversity: 65,
    github_activity: 58,
    repo_quality: 70,
    documentation: 66,
    community: 48,
  },
  justification:
    "Score breakdown — Resume Completeness: moderate (72/100); Skill Diversity: moderate (65/100); GitHub Activity: moderate (58/100); Repo Quality: moderate (70/100); Documentation: moderate (66/100); Community: needs improvement (48/100).",
};

const mlEngSkills: Skill[] = [
  sk("Python", "language", "advanced"),
  sk("Scikit-learn", "framework", "advanced"),
  sk("Pandas", "framework", "advanced"),
  sk("SQL", "language", "intermediate"),
  sk("FastAPI", "framework", "intermediate"),
  sk("Docker", "tool", "intermediate"),
  sk("Streamlit", "framework", "intermediate"),
  sk("Data Storytelling", "soft_skill", "intermediate"),
];

const mlEngGitHub: GitHubSummary = {
  username: "demo-ml-engineer",
  avatar_url: null,
  bio: "ML engineer focused on NLP and data pipelines",
  public_repos: 12,
  followers: 45,
  top_languages: { Python: 70, "Jupyter Notebook": 20, SQL: 10 },
  total_stars: 35,
  commit_frequency: "monthly",
  notable_repos: [],
};

// ── 4. Sample Fullstack Developer ────────────────────────

const fullstackScore: DeveloperScore = {
  overall: 74,
  categories: {
    resume_completeness: 80,
    skill_diversity: 82,
    github_activity: 70,
    repo_quality: 68,
    documentation: 60,
    community: 55,
  },
  justification:
    "Score breakdown — Resume Completeness: strong (80/100); Skill Diversity: strong (82/100); GitHub Activity: moderate (70/100); Repo Quality: moderate (68/100); Documentation: moderate (60/100); Community: moderate (55/100).",
};

const fullstackSkills: Skill[] = [
  sk("TypeScript", "language", "advanced"),
  sk("React", "framework", "advanced"),
  sk("Next.js", "framework", "advanced"),
  sk("Node.js", "framework", "advanced"),
  sk("PostgreSQL", "database", "intermediate"),
  sk("Tailwind CSS", "framework", "advanced"),
  sk("Docker", "tool", "intermediate"),
  sk("AWS", "cloud", "intermediate"),
  sk("GraphQL", "framework", "intermediate"),
  sk("Redis", "database", "intermediate"),
  sk("Agile", "soft_skill", "intermediate"),
  sk("Code Review", "soft_skill", "intermediate"),
];

const fullstackGitHub: GitHubSummary = {
  username: "demo-fullstack",
  avatar_url: null,
  bio: "Fullstack developer building modern web applications",
  public_repos: 22,
  followers: 120,
  top_languages: { TypeScript: 50, JavaScript: 30, Python: 20 },
  total_stars: 85,
  commit_frequency: "weekly",
  notable_repos: [],
};

// ── Shared enrichment data ───────────────────────────────

function buildSuggestions(gaps: string[]): Suggestion[] {
  return gaps.slice(0, 3).map((g, i) => ({
    area: g,
    current_state: `Limited exposure to ${g} in current portfolio.`,
    recommendation: `Adding ${g} projects or certifications would strengthen your portfolio.`,
    priority: (i === 0 ? "high" : "medium") as "high" | "medium",
    impact: `Improves employability for roles requiring ${g}.`,
  }));
}

function buildProjectIdeas(techs: string[][]): ProjectIdea[] {
  const templates = [
    {
      title: "AI-powered CLI Tool",
      description: "Build a developer productivity tool with AI capabilities.",
      difficulty: "intermediate",
      estimated_time: "2-3 weeks",
    },
    {
      title: "Real-time Dashboard",
      description: "Create a live analytics dashboard with WebSocket updates.",
      difficulty: "intermediate",
      estimated_time: "3-4 weeks",
    },
    {
      title: "Open Source Library",
      description: "Package a common pattern into a reusable library.",
      difficulty: "advanced",
      estimated_time: "4-6 weeks",
    },
  ];
  return templates.map((t, i) => ({
    ...t,
    tech_stack: techs[i] || [],
    skills_developed: [`Deepen expertise in ${(techs[i] || [])[0] || "best practices"}`],
  }));
}

function buildRoadmap(current: string, target: string): CareerRoadmap {
  return {
    current_level: current,
    target_role: target,
    milestones: [
      {
        timeframe: "0-3 months",
        goals: ["Strengthen core skills and fill gaps"],
        skills_to_learn: ["System Design", "Testing"],
        actions: ["Build a Portfolio Website", "Complete a system design course"],
      },
      {
        timeframe: "3-6 months",
        goals: ["Build visibility and deepen specialisation"],
        skills_to_learn: ["Architecture", "Mentoring"],
        actions: ["Contribute to open source", "Write technical blog posts"],
      },
      {
        timeframe: "6-12 months",
        goals: ["Demonstrate technical leadership and impact"],
        skills_to_learn: ["Technical Writing", "Public Speaking"],
        actions: ["Give a conference talk", "Lead a technical project"],
      },
    ],
  };
}

// ── Assemble profiles ────────────────────────────────────

export const demoProfiles: DemoProfile[] = [
  {
    name: "Alex Rivera",
    githubUrl: "https://github.com/alexrivera",
    analysis: {
      analysis_id: "demo-alex-rivera",
      developer_score: alexScore,
      skills: alexSkills,
      github_summary: alexGitHub,
      portfolio_suggestions: [],
      project_ideas: [],
      career_roadmap: null,
    },
    suggestions: buildSuggestions(["Kubernetes", "React", "Terraform"]),
    projectIdeas: buildProjectIdeas([
      ["Python", "LangChain", "FastAPI"],
      ["Streamlit", "Plotly", "WebSocket"],
      ["PyPI", "Python", "GitHub Actions"],
    ]),
    roadmap: buildRoadmap("Distinguished ML Researcher", "CTO / VP Engineering"),
  },
  {
    name: "Jordan Chen",
    githubUrl: "https://github.com/jordanchen",
    analysis: {
      analysis_id: "demo-jordan-chen",
      developer_score: jordanScore,
      skills: jordanSkills,
      github_summary: jordanGitHub,
      portfolio_suggestions: [],
      project_ideas: [],
      career_roadmap: null,
    },
    suggestions: buildSuggestions(["TypeScript", "Cloud Computing", "ML"]),
    projectIdeas: buildProjectIdeas([
      ["C", "Rust", "Linux"],
      ["C", "eBPF", "Grafana"],
      ["C", "Git", "GitHub Actions"],
    ]),
    roadmap: buildRoadmap("Distinguished Engineer", "Technical Fellow"),
  },
  {
    name: "Sample ML Engineer",
    githubUrl: "https://github.com/demo-ml-engineer",
    analysis: {
      analysis_id: "demo-ml-engineer",
      developer_score: mlEngScore,
      skills: mlEngSkills,
      github_summary: mlEngGitHub,
      portfolio_suggestions: [],
      project_ideas: [],
      career_roadmap: null,
    },
    suggestions: buildSuggestions(["Kubernetes", "CI/CD", "Technical Writing"]),
    projectIdeas: buildProjectIdeas([
      ["Python", "FastAPI", "OpenAI"],
      ["Streamlit", "Pandas", "WebSocket"],
      ["PyPI", "Python", "pytest"],
    ]),
    roadmap: buildRoadmap("Mid-Level ML Engineer", "Senior ML Engineer"),
  },
  {
    name: "Sample Fullstack Developer",
    githubUrl: "https://github.com/demo-fullstack",
    analysis: {
      analysis_id: "demo-fullstack-dev",
      developer_score: fullstackScore,
      skills: fullstackSkills,
      github_summary: fullstackGitHub,
      portfolio_suggestions: [],
      project_ideas: [],
      career_roadmap: null,
    },
    suggestions: buildSuggestions(["Machine Learning", "Terraform", "Technical Writing"]),
    projectIdeas: buildProjectIdeas([
      ["Next.js", "TypeScript", "OpenAI"],
      ["React", "D3.js", "WebSocket"],
      ["npm", "TypeScript", "GitHub Actions"],
    ]),
    roadmap: buildRoadmap("Mid-Level Fullstack Developer", "Senior Engineer"),
  },
];
