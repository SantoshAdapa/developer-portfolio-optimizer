const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// ─── Resume ───────────────────────────────────────────────────

export async function uploadResume(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${API_BASE_URL}/api/v1/resume/upload`;
  const res = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail || `Upload error: ${res.status}`);
  }

  return res.json();
}

// ─── GitHub ───────────────────────────────────────────────────

export async function analyzeGitHub(username: string) {
  return apiFetch("/api/v1/github/analyze", {
    method: "POST",
    body: JSON.stringify({ github_username: username }),
  });
}

// ─── Analysis ─────────────────────────────────────────────────

export async function runAnalysis(params: {
  resume_id?: string;
  github_username?: string;
}) {
  return apiFetch("/api/v1/analyze", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function getAnalysisResults(analysisId: string) {
  return apiFetch(`/api/v1/analyze/${encodeURIComponent(analysisId)}`);
}

// ─── Recommendations ─────────────────────────────────────────

export async function getPortfolioSuggestions(analysisId: string) {
  return apiFetch(`/api/v1/recommendations/${encodeURIComponent(analysisId)}/portfolio`);
}

export async function getProjectIdeas(analysisId: string) {
  return apiFetch(`/api/v1/recommendations/${encodeURIComponent(analysisId)}/projects`);
}

export async function getCareerRoadmap(analysisId: string) {
  return apiFetch(`/api/v1/recommendations/${encodeURIComponent(analysisId)}/roadmap`);
}

// ─── Benchmarks ───────────────────────────────────────────────

export async function getBenchmarks(analysisId: string) {
  return apiFetch(`/api/v1/benchmarks/${encodeURIComponent(analysisId)}`);
}

// ─── Comparison ───────────────────────────────────────────────

export async function compareProfiles(analysisIdA: string, analysisIdB: string) {
  return apiFetch("/api/v1/compare", {
    method: "POST",
    body: JSON.stringify({
      analysis_id_a: analysisIdA,
      analysis_id_b: analysisIdB,
    }),
  });
}
