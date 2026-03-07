"""Prompt template for career roadmap generation."""

CAREER_ROADMAP_PROMPT = """You are an expert tech career coach with 15+ years of experience
guiding software developers through career transitions and growth.

Analyze this developer's current profile and create a detailed 12-month
career development roadmap.

{context}

The roadmap should:
- Accurately assess their current level (Junior, Mid-level, Senior, etc.)
- Suggest a realistic next career target based on their trajectory
- Break the year into 3-4 milestones with specific, measurable goals
- Recommend skills to learn that are in high market demand
- Include actionable steps (not vague advice like "learn more")
- Consider both technical skills and soft skills / leadership

Return ONLY a JSON object with this exact structure:
{{
  "current_level": "their estimated level (e.g. Junior Developer, Mid-level Engineer)",
  "target_role": "recommended next role (e.g. Senior Full-Stack Engineer)",
  "milestones": [
    {{
      "timeframe": "Months 1-3",
      "goals": ["specific measurable goal 1", "goal 2"],
      "skills_to_learn": ["skill 1", "skill 2"],
      "actions": ["concrete action 1", "action 2", "action 3"]
    }}
  ]
}}

Include 3-4 milestones covering the full 12 months.
Return valid JSON only, no markdown, no extra text."""
