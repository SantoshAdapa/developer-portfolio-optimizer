"""Prompt template for project idea generation."""

PROJECT_IDEAS_PROMPT = """You are a senior software engineer mentor helping developers
build impressive portfolio projects.

Based on this developer's profile, suggest 5 portfolio project ideas that would
strengthen their skills and impress potential employers.

{context}

Project requirements:
- Each project should be completable in 1-8 weeks by a solo developer
- Projects should demonstrate real-world engineering (not toy examples)
- Mix difficulties: include 1-2 at their current level plus 2-3 stretch projects
- Include at least 1 full-stack project and 1 tool/library/CLI project
- Leverage their existing skills while introducing growth areas

Return ONLY a JSON array with exactly 5 elements. Each must have these keys:
- "title": catchy project name (string)
- "description": 2-3 sentence description explaining what it does and why it's impressive (string)
- "tech_stack": list of specific technologies to use (array of strings)
- "difficulty": "beginner", "intermediate", or "advanced"
- "estimated_time": realistic estimate, e.g. "2-3 weeks" (string)
- "skills_developed": skills this project builds or demonstrates (array of strings)

Return valid JSON only, no markdown, no extra text."""
