"""Prompt template for developer scoring justification."""

SCORING_PROMPT = """You are a technical assessment expert evaluating a developer's profile
for career readiness and portfolio quality.

Analyze the following developer profile and provide a detailed justification
for their developer score.

{context}

The scoring categories and their computed scores are:
{score_breakdown}

Provide a 2-3 paragraph analysis that:
1. Highlights the developer's key strengths
2. Identifies the most critical areas for improvement
3. Gives a specific, encouraging next step

Return ONLY a JSON object with this exact structure:
{{
  "justification": "Your detailed 2-3 paragraph analysis here.",
  "top_strengths": ["strength 1", "strength 2", "strength 3"],
  "critical_gaps": ["gap 1", "gap 2"]
}}

Return valid JSON only, no markdown, no extra text."""
