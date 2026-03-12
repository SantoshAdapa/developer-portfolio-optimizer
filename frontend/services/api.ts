const API_BASE_URL = "";

/**
 * Delay helper for retry backoff.
 */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit,
  retries = 2,
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  for (let attempt = 0; attempt <= retries; attempt++) {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    // Retry on 429 with exponential backoff
    if (res.status === 429 && attempt < retries) {
      await delay(2000 * (attempt + 1));
      continue;
    }

    if (!res.ok && res.status !== 202) {
      const error = await res.json().catch(() => ({ detail: "Unknown error" }));
      let message: string;
      if (typeof error.detail === "string") {
        message = error.detail;
      } else if (Array.isArray(error.detail)) {
        message = error.detail.map((e: any) => e.msg).join("; ");
      } else if (res.status === 429) {
        message = "Too many requests. Please wait a moment and try again.";
      } else {
        message = `API error: ${res.status}`;
      }
      throw new Error(message);
    }

    return res.json();
  }

  // Should not reach here, but satisfy TypeScript
  throw new Error("Request failed after retries");
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
  file?: File;
  github_username?: string;
  resume_id?: string;
}) {
  const formData = new FormData();
  if (params.file) {
    formData.append("file", params.file);
  }
  if (params.github_username) {
    formData.append(
      "github_url",
      `https://github.com/${params.github_username}`
    );
  }
  if (params.resume_id && !params.file) {
    formData.append("resume_id", params.resume_id);
  }

  const url = `${API_BASE_URL}/api/v1/analyze`;
  const res = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Analysis failed" }));
    let message = `API error: ${res.status}`;
    if (typeof error.detail === "string") {
      message = error.detail;
    } else if (Array.isArray(error.detail)) {
      message = error.detail.map((e: any) => e.msg).join("; ");
    }
    throw new Error(message);
  }

  const data = await res.json();

  // Backend returns 202 with {analysis_id, status: "processing"} — poll until done
  if (data.status === "processing" && data.analysis_id) {
    return pollForResults(data.analysis_id);
  }

  return data;
}

async function pollForResults(
  analysisId: string,
  intervalMs = 2000,
  maxAttempts = 120,
) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await delay(intervalMs);
    const pollUrl = `${API_BASE_URL}/api/v1/analyze/${encodeURIComponent(analysisId)}`;
    const res = await fetch(pollUrl);

    if (res.status === 202) continue; // still processing

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: "Analysis failed" }));
      throw new Error(error.detail || `Analysis failed: ${res.status}`);
    }

    const result = await res.json();
    if (result.status === "failed") {
      throw new Error("Analysis failed. Please try again.");
    }
    if (result.status === "processing") continue;

    return result;
  }
  throw new Error("Analysis timed out. Please try again.");
}

export async function getAnalysisResults(analysisId: string) {
  return apiFetch(`/api/v1/analyze/${encodeURIComponent(analysisId)}`);
}

// ─── Recommendations ─────────────────────────────────────────

export async function getPortfolioSuggestions(analysisId: string) {
  const res = await apiFetch<{ suggestions: unknown[] }>(
    `/api/v1/recommendations/${encodeURIComponent(analysisId)}/portfolio`
  );
  return res.suggestions;
}

export async function getProjectIdeas(analysisId: string) {
  const res = await apiFetch<{ project_ideas: unknown[] }>(
    `/api/v1/recommendations/${encodeURIComponent(analysisId)}/projects`
  );
  return res.project_ideas;
}

export async function getCareerRoadmap(analysisId: string) {
  const res = await apiFetch<{ roadmap: unknown }>(
    `/api/v1/recommendations/${encodeURIComponent(analysisId)}/roadmap`
  );
  return res.roadmap;
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
