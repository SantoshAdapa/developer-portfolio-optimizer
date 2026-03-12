"""Role templates for job-match and skill-gap analysis.

Each template has:
- ``required``: skills absolutely needed for the role.
- ``preferred``: nice-to-have skills that boost the match score.

Skill names MUST use the canonical form from ``skill_normalization``.

Experience-level presets map to generic expectations.
"""

from __future__ import annotations

# ── Role Templates ──────────────────────────────────────────

ROLE_TEMPLATES: dict[str, dict] = {
    "machine_learning_engineer": {
        "label": "Machine Learning Engineer",
        "required": {
            "Python": "advanced",
            "Machine Learning": "advanced",
            "Deep Learning": "intermediate",
            "PyTorch": "intermediate",
            "TensorFlow": "intermediate",
            "Scikit-Learn": "intermediate",
            "Statistics": "intermediate",
            "Feature Engineering": "intermediate",
            "Data Processing": "intermediate",
        },
        "preferred": {
            "MLOps": "intermediate",
            "Docker": "intermediate",
            "AWS": "intermediate",
            "Natural Language Processing": "intermediate",
            "Computer Vision": "intermediate",
            "Pandas": "intermediate",
            "NumPy": "intermediate",
            "Git": "intermediate",
            "Linux": "intermediate",
            "SQL": "intermediate",
        },
    },
    "data_scientist": {
        "label": "Data Scientist",
        "required": {
            "Python": "advanced",
            "Statistics": "advanced",
            "Machine Learning": "advanced",
            "Pandas": "advanced",
            "SQL": "intermediate",
            "Data Visualization": "intermediate",
            "Scikit-Learn": "intermediate",
            "Feature Engineering": "intermediate",
            "NumPy": "intermediate",
        },
        "preferred": {
            "Deep Learning": "intermediate",
            "TensorFlow": "intermediate",
            "PyTorch": "intermediate",
            "Natural Language Processing": "intermediate",
            "R": "intermediate",
            "Tableau": "intermediate",
            "Apache Spark": "intermediate",
            "Git": "intermediate",
        },
    },
    "backend_developer": {
        "label": "Backend Developer",
        "required": {
            "Python": "advanced",
            "SQL": "advanced",
            "REST API": "advanced",
            "PostgreSQL": "intermediate",
            "Docker": "intermediate",
            "Git": "intermediate",
            "Linux": "intermediate",
            "Testing": "intermediate",
            "CI/CD": "intermediate",
        },
        "preferred": {
            "Redis": "intermediate",
            "MongoDB": "intermediate",
            "Kubernetes": "intermediate",
            "Microservices": "intermediate",
            "AWS": "intermediate",
            "GraphQL": "intermediate",
            "Kafka": "intermediate",
            "Monitoring": "intermediate",
        },
    },
    "fullstack_developer": {
        "label": "Full-Stack Developer",
        "required": {
            "JavaScript": "advanced",
            "TypeScript": "intermediate",
            "React": "advanced",
            "Node.js": "intermediate",
            "SQL": "intermediate",
            "REST API": "intermediate",
            "Git": "intermediate",
            "Docker": "intermediate",
        },
        "preferred": {
            "Next.js": "intermediate",
            "PostgreSQL": "intermediate",
            "MongoDB": "intermediate",
            "Redis": "intermediate",
            "CI/CD": "intermediate",
            "Testing": "intermediate",
            "AWS": "intermediate",
            "Tailwind CSS": "intermediate",
        },
    },
    "python_developer": {
        "label": "Python Developer",
        "required": {
            "Python": "advanced",
            "SQL": "intermediate",
            "REST API": "intermediate",
            "Git": "intermediate",
            "Testing": "intermediate",
            "Docker": "intermediate",
            "Linux": "intermediate",
        },
        "preferred": {
            "FastAPI": "intermediate",
            "Django": "intermediate",
            "PostgreSQL": "intermediate",
            "Redis": "intermediate",
            "CI/CD": "intermediate",
            "AWS": "intermediate",
            "Celery": "intermediate",
        },
    },
    "qa_engineer": {
        "label": "QA Engineer",
        "required": {
            "Testing": "advanced",
            "Python": "intermediate",
            "SQL": "intermediate",
            "Git": "intermediate",
            "CI/CD": "intermediate",
            "REST API": "intermediate",
            "Linux": "intermediate",
        },
        "preferred": {
            "Docker": "intermediate",
            "JavaScript": "intermediate",
            "Java": "intermediate",
            "Monitoring": "intermediate",
            "AWS": "intermediate",
        },
    },
    "devops_engineer": {
        "label": "DevOps Engineer",
        "required": {
            "Docker": "advanced",
            "Kubernetes": "advanced",
            "Linux": "advanced",
            "CI/CD": "advanced",
            "Terraform": "intermediate",
            "AWS": "intermediate",
            "Git": "intermediate",
            "Bash": "intermediate",
            "Monitoring": "intermediate",
        },
        "preferred": {
            "Python": "intermediate",
            "GCP": "intermediate",
            "Azure": "intermediate",
            "Kafka": "intermediate",
            "Microservices": "intermediate",
        },
    },
    "frontend_developer": {
        "label": "Frontend Developer",
        "required": {
            "JavaScript": "advanced",
            "TypeScript": "advanced",
            "React": "advanced",
            "Tailwind CSS": "intermediate",
            "Responsive Design": "intermediate",
            "Git": "intermediate",
            "Testing": "intermediate",
        },
        "preferred": {
            "Next.js": "intermediate",
            "Vue": "intermediate",
            "Redux": "intermediate",
            "Sass": "intermediate",
            "Webpack": "intermediate",
            "Figma": "intermediate",
            "Framer Motion": "intermediate",
        },
    },
}

# ── Experience Level Presets ─────────────────────────────────

EXPERIENCE_LEVELS: dict[str, dict] = {
    "student": {
        "label": "Student",
        "description": "Currently studying, looking for internships",
        "expected_skills": 3,
        "expected_proficiency": "beginner",
    },
    "fresher": {
        "label": "Fresher",
        "description": "0-1 years of experience, recent graduate",
        "expected_skills": 5,
        "expected_proficiency": "beginner",
    },
    "junior": {
        "label": "Junior Developer",
        "description": "1-2 years of experience",
        "expected_skills": 7,
        "expected_proficiency": "intermediate",
    },
    "mid": {
        "label": "Mid-Level Developer",
        "description": "3-5 years of experience",
        "expected_skills": 10,
        "expected_proficiency": "intermediate",
    },
    "senior": {
        "label": "Senior Engineer",
        "description": "5+ years of experience",
        "expected_skills": 14,
        "expected_proficiency": "advanced",
    },
}

# ── Skill Domain Categorization ──────────────────────────────

SKILL_DOMAINS: dict[str, list[str]] = {
    "ML/AI": [
        "Machine Learning",
        "Deep Learning",
        "Natural Language Processing",
        "Computer Vision",
        "TensorFlow",
        "PyTorch",
        "Keras",
        "Scikit-Learn",
        "OpenCV",
        "XGBoost",
        "LightGBM",
        "Hugging Face",
        "LangChain",
        "spaCy",
        "NLTK",
        "Reinforcement Learning",
        "Neural Networks",
        "Feature Engineering",
        "Model Training",
        "MLOps",
        "Statistics",
        "Streamlit",
        "Gradio",
    ],
    "Backend": [
        "Python",
        "Java",
        "Go",
        "Rust",
        "Ruby",
        "PHP",
        "C#",
        "C++",
        "Scala",
        "Kotlin",
        "Node.js",
        "FastAPI",
        "Django",
        "Flask",
        "Express.js",
        "Spring Boot",
        "Ruby on Rails",
        "ASP.NET",
        "NestJS",
        "REST API",
        "GraphQL",
        "gRPC",
        "Microservices",
    ],
    "Frontend": [
        "JavaScript",
        "TypeScript",
        "React",
        "Next.js",
        "Vue",
        "Angular",
        "Svelte",
        "Tailwind CSS",
        "Bootstrap",
        "Material UI",
        "Redux",
        "Gatsby",
        "Nuxt.js",
        "Framer Motion",
        "Responsive Design",
        "Figma",
        "Sass",
        "Styled Components",
        "Webpack",
        "Vite",
    ],
    "DevOps": [
        "Docker",
        "Kubernetes",
        "Terraform",
        "AWS",
        "GCP",
        "Azure",
        "CI/CD",
        "Linux",
        "Bash",
        "Monitoring",
        "Git",
    ],
    "Data": [
        "SQL",
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Redis",
        "Elasticsearch",
        "Pandas",
        "NumPy",
        "Matplotlib",
        "Seaborn",
        "SciPy",
        "Apache Spark",
        "Kafka",
        "DynamoDB",
        "Cassandra",
        "Neo4j",
        "Firebase",
        "Supabase",
        "Prisma",
        "SQLAlchemy",
        "Data Visualization",
        "Data Processing",
        "Plotly",
        "Tableau",
        "Power BI",
        "Excel",
        "R",
    ],
    "Testing": [
        "Testing",
    ],
}

# Build reverse lookups
_SKILL_TO_DOMAIN: dict[str, str] = {}
for domain, skills in SKILL_DOMAINS.items():
    for skill in skills:
        _SKILL_TO_DOMAIN[skill.lower()] = domain


def get_skill_domain(skill_name: str) -> str:
    """Return the domain category for a skill, or 'Other'."""
    return _SKILL_TO_DOMAIN.get(skill_name.strip().lower(), "Other")


def compute_domain_distribution(skill_names: list[str]) -> dict[str, int]:
    """Compute percentage distribution of skills across domains.

    Returns e.g. ``{"ML/AI": 40, "Backend": 20, ...}``.
    """
    counts: dict[str, int] = {}
    for name in skill_names:
        domain = get_skill_domain(name)
        counts[domain] = counts.get(domain, 0) + 1

    total = sum(counts.values()) or 1
    return {domain: round(count / total * 100) for domain, count in counts.items()}
