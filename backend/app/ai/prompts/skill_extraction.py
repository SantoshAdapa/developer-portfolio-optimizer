"""Prompt template for extracting skills from resume text."""

SKILL_EXTRACTION_PROMPT = """You are an expert technical recruiter with deep knowledge of
the software engineering industry.

Analyze the following resume content and extract ALL technical and soft skills.
For each skill, determine its category and estimate the proficiency level based
on context clues (years of experience, project complexity, role seniority).

{context}

Return ONLY a JSON array. Each element must have these exact keys:
- "name": the skill name (string, e.g. "Python", "React", "Team Leadership")
- "category": one of "language", "framework", "tool", "database", "cloud", "soft_skill"
- "proficiency": one of "beginner", "intermediate", "advanced"
- "source": "resume"

Proficiency guidelines:
- "beginner": mentioned but limited evidence of depth (< 1 year, coursework only)
- "intermediate": clear usage in projects or 1-3 years experience
- "advanced": deep expertise, 3+ years, leadership role, or core to multiple projects

Return valid JSON only, no markdown, no extra text."""
