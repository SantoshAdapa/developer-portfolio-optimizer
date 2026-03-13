import type {
  AnalysisResponse,
  DeveloperScore,
  Skill,
  GitHubSummary,
  CareerRoadmap,
  Suggestion,
  ProjectIdea,
  RadarScores,
  AiInsights,
  SkillGapResult,
  LearningRoadmapResult,
  MarketDemandResult,
  CareerDirectionResult,
  PortfolioDepthScore,
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

const alexRadar: RadarScores = {
  frontend: 8,
  backend: 35,
  data: 55,
  ml_ai: 95,
  devops: 18,
  testing: 12,
};

const alexInsights: AiInsights = {
  strengths: [
    "Exceptional ML/AI expertise with advanced proficiency in TensorFlow, PyTorch, and deep learning",
    "Strong research and education background with teaching and public speaking skills",
    "Impressive GitHub presence with 80,000+ stars and consistent contributions",
  ],
  weaknesses: [
    "Limited frontend and web development experience",
    "DevOps and infrastructure skills could be strengthened",
    "Testing practices not prominently demonstrated",
  ],
  career_potential:
    "Distinguished ML researcher with massive community impact. Well-positioned for Chief AI Officer, ML Research Director, or VP of AI roles.",
  recommended_improvements: [
    "Add a web-based ML demo project to showcase end-to-end deployment",
    "Learn Kubernetes for ML model serving at scale",
    "Build a testing framework for ML pipelines",
  ],
};

const alexSkillGap: SkillGapResult = {
  target_role: "ML Engineer",
  match_percentage: 88,
  matched_skills: [
    { skill: "Python", status: "matched", proficiency: "advanced", required_level: "advanced" },
    { skill: "TensorFlow", status: "matched", proficiency: "advanced", required_level: "intermediate" },
    { skill: "PyTorch", status: "matched", proficiency: "advanced", required_level: "intermediate" },
    { skill: "Deep Learning", status: "matched", proficiency: "advanced", required_level: "advanced" },
  ],
  missing_skills: [
    { skill: "Scikit-Learn", status: "gap", proficiency: "", required_level: "intermediate" },
  ],
  partial_skills: [
    { skill: "Docker", status: "partial", proficiency: "intermediate", required_level: "advanced" },
  ],
  summary: "88% match for ML Engineer. 4 skills fully matched. 1 skill needs leveling up. 1 skill to learn.",
};

const alexPortfolioDepth: PortfolioDepthScore = {
  overall: 85,
  project_count: 25,
  technology_diversity: 78,
  complexity_score: 92,
  deployment_signals: 65,
  project_type_balance: 70,
  summary: "Strong portfolio with deep ML expertise. Consider adding deployment and infrastructure projects.",
};

const alexCareerDirection: CareerDirectionResult = {
  primary_direction: "ML Research Lead",
  career_paths: [
    { role: "ML Research Lead", fit_score: 95, matching_skills: ["Python", "TensorFlow", "PyTorch", "Deep Learning"], skills_to_develop: ["System Design", "Kubernetes"], description: "Lead ML research teams and drive cutting-edge AI initiatives" },
    { role: "Chief AI Officer", fit_score: 82, matching_skills: ["Python", "Deep Learning", "NLP"], skills_to_develop: ["Business Strategy", "Product Management"], description: "Strategic AI leadership at the executive level" },
    { role: "AI Platform Engineer", fit_score: 68, matching_skills: ["Python", "Docker", "TensorFlow"], skills_to_develop: ["Kubernetes", "AWS", "CI/CD"], description: "Build and maintain ML infrastructure at scale" },
  ],
  summary: "Best fit: ML Research Lead (95% match). Also suited for: Chief AI Officer, AI Platform Engineer.",
};

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

const jordanRadar: RadarScores = {
  frontend: 5,
  backend: 88,
  data: 20,
  ml_ai: 8,
  devops: 45,
  testing: 35,
};

const jordanInsights: AiInsights = {
  strengths: [
    "World-class systems programming expertise with deep Linux kernel knowledge",
    "Exceptional community impact with 180,000+ stars and 200,000+ followers",
    "Strong code review and technical leadership skills",
  ],
  weaknesses: [
    "Narrow technology focus — limited web/frontend skills",
    "No ML/AI or data science experience",
    "Modern cloud-native technologies not represented",
  ],
  career_potential:
    "Distinguished systems engineer with legendary open-source contributions. Ideal for Technical Fellow, Chief Architect, or Distinguished Engineer roles.",
  recommended_improvements: [
    "Consider exploring Rust as a modern systems language complement",
    "Add cloud infrastructure experience (AWS/GCP)",
    "Build a project demonstrating container orchestration skills",
  ],
};

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

const mlEngRadar: RadarScores = {
  frontend: 15,
  backend: 40,
  data: 65,
  ml_ai: 70,
  devops: 20,
  testing: 10,
};

const mlEngInsights: AiInsights = {
  strengths: [
    "Strong Python and data science fundamentals with Scikit-learn and Pandas",
    "Good understanding of data pipelines and API development with FastAPI",
    "Practical ML deployment experience with Streamlit and Docker",
  ],
  weaknesses: [
    "Limited deep learning framework experience (no PyTorch/TensorFlow)",
    "Testing practices need significant improvement",
    "Community engagement and open-source visibility are low",
  ],
  career_potential:
    "Solid mid-level ML engineer with room to grow into senior ML roles by deepening framework expertise and building community presence.",
  recommended_improvements: [
    "Learn PyTorch or TensorFlow for deep learning projects",
    "Add comprehensive testing to existing ML projects",
    "Start contributing to open-source ML libraries",
    "Write blog posts about ML projects to build visibility",
  ],
};

const mlEngSkillGap: SkillGapResult = {
  target_role: "ML Engineer",
  match_percentage: 62,
  matched_skills: [
    { skill: "Python", status: "matched", proficiency: "advanced", required_level: "advanced" },
    { skill: "Scikit-Learn", status: "matched", proficiency: "advanced", required_level: "intermediate" },
    { skill: "Pandas", status: "matched", proficiency: "advanced", required_level: "intermediate" },
  ],
  missing_skills: [
    { skill: "Deep Learning", status: "gap", proficiency: "", required_level: "intermediate" },
    { skill: "PyTorch", status: "gap", proficiency: "", required_level: "intermediate" },
    { skill: "TensorFlow", status: "gap", proficiency: "", required_level: "intermediate" },
  ],
  partial_skills: [
    { skill: "Docker", status: "partial", proficiency: "intermediate", required_level: "advanced" },
  ],
  summary: "62% match for ML Engineer. 3 skills fully matched. 1 skill needs leveling up. 3 skills to learn.",
};

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

const fullstackRadar: RadarScores = {
  frontend: 90,
  backend: 72,
  data: 35,
  ml_ai: 5,
  devops: 30,
  testing: 22,
};

const fullstackInsights: AiInsights = {
  strengths: [
    "Excellent frontend expertise with React, Next.js, and TypeScript",
    "Broad full-stack capabilities spanning frontend, backend, and databases",
    "Good technology diversity covering both SQL and NoSQL databases",
  ],
  weaknesses: [
    "ML/AI skills are absent — limits versatility",
    "Testing practices need improvement",
    "Documentation habits could be stronger",
  ],
  career_potential:
    "Strong mid-level fullstack developer well-positioned for senior frontend or fullstack engineer roles. Adding testing and CI/CD expertise would accelerate career growth.",
  recommended_improvements: [
    "Add comprehensive testing (unit, integration, E2E) to projects",
    "Learn CI/CD and infrastructure-as-code",
    "Build a project demonstrating system design skills",
    "Improve project documentation and READMEs",
  ],
};

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
      skill_categories: [],
      radar_scores: alexRadar,
      programming_languages: [
        { name: "Python", proficiency: "advanced", confidence: 95, context: "Primary language across all ML projects" },
        { name: "MATLAB", proficiency: "advanced", confidence: 80, context: "Used in research and academic work" },
      ],
      ai_insights: alexInsights,
      score_breakdown: null,
      portfolio_depth: alexPortfolioDepth,
      skill_gap: alexSkillGap,
      learning_roadmap: null,
      market_demand: null,
      career_direction: alexCareerDirection,
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
      skill_categories: [],
      radar_scores: jordanRadar,
      programming_languages: [
        { name: "C", proficiency: "advanced", confidence: 98, context: "Primary systems programming language" },
        { name: "Bash", proficiency: "advanced", confidence: 85, context: "Shell scripting and automation" },
      ],
      ai_insights: jordanInsights,
      score_breakdown: null,
      portfolio_depth: null,
      skill_gap: null,
      learning_roadmap: null,
      market_demand: null,
      career_direction: null,
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
      skill_categories: [],
      radar_scores: mlEngRadar,
      programming_languages: [
        { name: "Python", proficiency: "advanced", confidence: 90, context: "Primary language for ML and data work" },
        { name: "SQL", proficiency: "intermediate", confidence: 70, context: "Database querying for data pipelines" },
      ],
      ai_insights: mlEngInsights,
      score_breakdown: null,
      portfolio_depth: null,
      skill_gap: mlEngSkillGap,
      learning_roadmap: null,
      market_demand: null,
      career_direction: null,
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
      skill_categories: [],
      radar_scores: fullstackRadar,
      programming_languages: [
        { name: "TypeScript", proficiency: "advanced", confidence: 92, context: "Primary language for frontend and backend" },
        { name: "JavaScript", proficiency: "advanced", confidence: 88, context: "Web development fundamentals" },
        { name: "Python", proficiency: "intermediate", confidence: 65, context: "Used in backend services" },
      ],
      ai_insights: fullstackInsights,
      score_breakdown: null,
      portfolio_depth: null,
      skill_gap: null,
      learning_roadmap: null,
      market_demand: null,
      career_direction: null,
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
