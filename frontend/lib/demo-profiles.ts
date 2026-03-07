import type {
  AnalysisResponse,
  DeveloperScore,
  SkillAnalysis,
  GitHubInsights,
  CareerRoadmap,
  PortfolioSuggestion,
  ProjectIdea,
} from "@/types";

export interface DemoProfile {
  name: string;
  githubUrl: string;
  analysis: AnalysisResponse;
  suggestions: PortfolioSuggestion[];
  projectIdeas: ProjectIdea[];
  roadmap: CareerRoadmap;
}

// ── Shared helpers ───────────────────────────────────────

function cat(name: string, score: number, max = 100, description = "") {
  return { name, score, max_score: max, description };
}

function skill(
  name: string,
  level: "beginner" | "intermediate" | "advanced" | "expert",
  category: string
) {
  return { name, level, category };
}

// ── 1. Andrew Ng – ML legend ─────────────────────────────

const andrewNgScore: DeveloperScore = {
  overall: 92,
  categories: [
    cat("Resume Completeness", 95),
    cat("Skill Diversity", 88),
    cat("GitHub Activity", 82),
    cat("Repo Quality", 90),
    cat("Documentation", 96),
    cat("Community", 94),
  ],
};

const andrewNgSkills: SkillAnalysis = {
  technical_skills: [
    skill("Python", "expert", "backend"),
    skill("TensorFlow", "expert", "machine_learning"),
    skill("PyTorch", "advanced", "machine_learning"),
    skill("Deep Learning", "expert", "machine_learning"),
    skill("NLP", "advanced", "machine_learning"),
    skill("Computer Vision", "advanced", "machine_learning"),
    skill("MATLAB", "advanced", "data"),
    skill("Jupyter", "advanced", "data"),
    skill("Docker", "intermediate", "devops"),
  ],
  soft_skills: [
    skill("Technical Writing", "expert", "communication"),
    skill("Teaching", "expert", "leadership"),
    skill("Public Speaking", "expert", "communication"),
  ],
  missing_skills: [
    skill("Kubernetes", "beginner", "devops"),
    skill("React", "beginner", "frontend"),
  ],
};

const andrewNgGitHub: GitHubInsights = {
  activity_level: "Very Active",
  top_languages: ["Python", "Jupyter Notebook", "MATLAB"],
  project_diversity: 85,
  code_quality_indicators: [
    "Comprehensive README files",
    "CI/CD pipelines",
    "Unit tests",
  ],
  collaboration_score: 92,
};

// ── 2. Linus Torvalds – OS legend ────────────────────────

const linusScore: DeveloperScore = {
  overall: 96,
  categories: [
    cat("Resume Completeness", 90),
    cat("Skill Diversity", 78),
    cat("GitHub Activity", 98),
    cat("Repo Quality", 99),
    cat("Documentation", 92),
    cat("Community", 99),
  ],
};

const linusSkills: SkillAnalysis = {
  technical_skills: [
    skill("C", "expert", "backend"),
    skill("Bash", "expert", "devops"),
    skill("Git", "expert", "devops"),
    skill("Linux Kernel", "expert", "backend"),
    skill("Assembly", "advanced", "backend"),
    skill("Makefile", "expert", "devops"),
    skill("Perl", "intermediate", "backend"),
  ],
  soft_skills: [
    skill("Code Review", "expert", "leadership"),
    skill("Technical Vision", "expert", "leadership"),
  ],
  missing_skills: [
    skill("TypeScript", "beginner", "frontend"),
    skill("Cloud Computing", "beginner", "devops"),
    skill("Machine Learning", "beginner", "machine_learning"),
  ],
};

const linusGitHub: GitHubInsights = {
  activity_level: "Extremely Active",
  top_languages: ["C", "Shell", "Makefile"],
  project_diversity: 45,
  code_quality_indicators: [
    "World-class code review process",
    "Extensive changelogs",
    "Kernel-grade testing",
  ],
  collaboration_score: 99,
};

// ── 3. Sample ML Engineer ────────────────────────────────

const mlEngScore: DeveloperScore = {
  overall: 68,
  categories: [
    cat("Resume Completeness", 72),
    cat("Skill Diversity", 65),
    cat("GitHub Activity", 58),
    cat("Repo Quality", 70),
    cat("Documentation", 66),
    cat("Community", 48),
  ],
};

const mlEngSkills: SkillAnalysis = {
  technical_skills: [
    skill("Python", "advanced", "backend"),
    skill("Scikit-learn", "advanced", "machine_learning"),
    skill("Pandas", "advanced", "data"),
    skill("SQL", "intermediate", "data"),
    skill("FastAPI", "intermediate", "backend"),
    skill("Docker", "intermediate", "devops"),
    skill("Streamlit", "intermediate", "frontend"),
  ],
  soft_skills: [
    skill("Data Storytelling", "intermediate", "communication"),
  ],
  missing_skills: [
    skill("Kubernetes", "beginner", "devops"),
    skill("React", "beginner", "frontend"),
    skill("CI/CD", "beginner", "devops"),
    skill("Technical Writing", "beginner", "documentation"),
  ],
};

const mlEngGitHub: GitHubInsights = {
  activity_level: "Moderate",
  top_languages: ["Python", "Jupyter Notebook", "SQL"],
  project_diversity: 55,
  code_quality_indicators: ["Decent README files", "Some tests"],
  collaboration_score: 42,
};

// ── 4. Sample Fullstack Developer ────────────────────────

const fullstackScore: DeveloperScore = {
  overall: 74,
  categories: [
    cat("Resume Completeness", 80),
    cat("Skill Diversity", 82),
    cat("GitHub Activity", 70),
    cat("Repo Quality", 68),
    cat("Documentation", 60),
    cat("Community", 55),
  ],
};

const fullstackSkills: SkillAnalysis = {
  technical_skills: [
    skill("TypeScript", "advanced", "frontend"),
    skill("React", "advanced", "frontend"),
    skill("Next.js", "advanced", "frontend"),
    skill("Node.js", "advanced", "backend"),
    skill("PostgreSQL", "intermediate", "data"),
    skill("Tailwind CSS", "advanced", "frontend"),
    skill("Docker", "intermediate", "devops"),
    skill("AWS", "intermediate", "devops"),
    skill("GraphQL", "intermediate", "backend"),
    skill("Redis", "intermediate", "data"),
  ],
  soft_skills: [
    skill("Agile", "intermediate", "process"),
    skill("Code Review", "intermediate", "leadership"),
  ],
  missing_skills: [
    skill("Machine Learning", "beginner", "machine_learning"),
    skill("Terraform", "beginner", "devops"),
  ],
};

const fullstackGitHub: GitHubInsights = {
  activity_level: "Active",
  top_languages: ["TypeScript", "JavaScript", "Python"],
  project_diversity: 72,
  code_quality_indicators: [
    "ESLint configured",
    "GitHub Actions CI",
    "Good README files",
  ],
  collaboration_score: 60,
};

// ── Shared enrichment data ───────────────────────────────

function buildSuggestions(gaps: string[]): PortfolioSuggestion[] {
  return gaps.slice(0, 3).map((g, i) => ({
    title: `Improve ${g}`,
    description: `Adding ${g} projects or certifications would strengthen your portfolio.`,
    priority: i === 0 ? "high" : "medium",
    category: "skills",
    action_items: [`Build a project using ${g}`, `Add ${g} to your resume`],
  }));
}

function buildProjectIdeas(techs: string[][]): ProjectIdea[] {
  const templates = [
    {
      title: "AI-powered CLI Tool",
      description: "Build a developer productivity tool with AI capabilities.",
      difficulty: "intermediate" as const,
      estimated_time: "2-3 weeks",
      impact_score: 78,
    },
    {
      title: "Real-time Dashboard",
      description: "Create a live analytics dashboard with WebSocket updates.",
      difficulty: "intermediate" as const,
      estimated_time: "3-4 weeks",
      impact_score: 72,
    },
    {
      title: "Open Source Library",
      description: "Package a common pattern into a reusable library.",
      difficulty: "advanced" as const,
      estimated_time: "4-6 weeks",
      impact_score: 85,
    },
  ];
  return templates.map((t, i) => ({
    ...t,
    technologies: techs[i] || [],
    learning_outcomes: [`Deepen expertise in ${(techs[i] || [])[0] || "best practices"}`],
  }));
}

function buildRoadmap(
  current: string,
  target: string
): CareerRoadmap {
  return {
    current_level: current,
    target_level: target,
    timeline: "12 months",
    milestones: [
      {
        title: "Foundation",
        description: "Strengthen core skills and fill gaps.",
        timeframe: "0-3 months",
        skills_to_learn: ["System Design", "Testing"],
        projects_to_build: ["Portfolio Website"],
        resources: [
          {
            title: "System Design Primer",
            url: "https://github.com/donnemartin/system-design-primer",
            type: "documentation",
          },
        ],
        completed: false,
      },
      {
        title: "Growth",
        description: "Build visibility and deepen specialisation.",
        timeframe: "3-6 months",
        skills_to_learn: ["Architecture", "Mentoring"],
        projects_to_build: ["Open Source Contribution"],
        resources: [],
        completed: false,
      },
      {
        title: "Leadership",
        description: "Demonstrate technical leadership and impact.",
        timeframe: "6-12 months",
        skills_to_learn: ["Technical Writing", "Public Speaking"],
        projects_to_build: ["Conference Talk"],
        resources: [],
        completed: false,
      },
    ],
  };
}

// ── Assemble profiles ────────────────────────────────────

export const demoProfiles: DemoProfile[] = [
  {
    name: "Andrew Ng",
    githubUrl: "https://github.com/andrewng",
    analysis: {
      analysis_id: "demo-andrew-ng",
      developer_score: andrewNgScore,
      skills: andrewNgSkills,
      github_insights: andrewNgGitHub,
      strengths: [
        "World-class machine learning expertise",
        "Exceptional documentation and teaching ability",
        "Strong community presence and collaboration",
      ],
      weaknesses: [
        "Limited frontend and DevOps experience",
        "Could diversify open-source contributions beyond ML",
      ],
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
    name: "Linus Torvalds",
    githubUrl: "https://github.com/torvalds",
    analysis: {
      analysis_id: "demo-linus-torvalds",
      developer_score: linusScore,
      skills: linusSkills,
      github_insights: linusGitHub,
      strengths: [
        "Creator of Git and the Linux kernel",
        "Unmatched system-level expertise",
        "Highest community impact in open source",
      ],
      weaknesses: [
        "Narrow technology stack focused on low-level systems",
        "Limited experience with modern web and cloud ecosystems",
      ],
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
      github_insights: mlEngGitHub,
      strengths: [
        "Solid machine learning fundamentals",
        "Good data engineering skills",
        "Growing backend capabilities",
      ],
      weaknesses: [
        "Limited community engagement",
        "Needs more comprehensive documentation",
        "Missing DevOps and deployment expertise",
      ],
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
      github_insights: fullstackGitHub,
      strengths: [
        "Broad full-stack skill set across frontend and backend",
        "Good adoption of modern frameworks",
        "Consistent GitHub activity",
      ],
      weaknesses: [
        "Documentation could be more comprehensive",
        "Limited community contributions",
        "Missing ML and data science exposure",
      ],
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

export function getDemoProfileByName(name: string): DemoProfile | undefined {
  return demoProfiles.find(
    (p) => p.name.toLowerCase() === name.toLowerCase()
  );
}
