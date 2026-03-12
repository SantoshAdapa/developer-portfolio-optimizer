"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  uploadResume,
  analyzeGitHub,
  runAnalysis,
  getAnalysisResults,
} from "@/services/api";

export function useUploadResume() {
  return useMutation({
    mutationFn: (file: File) => uploadResume(file),
  });
}

export function useAnalyzeGitHub() {
  return useMutation({
    mutationFn: (username: string) => analyzeGitHub(username),
  });
}

export function useRunAnalysis() {
  return useMutation({
    mutationFn: (params: { file?: File; github_username?: string; resume_id?: string }) =>
      runAnalysis(params),
  });
}

export function useAnalysisResults(analysisId: string | undefined) {
  return useQuery({
    queryKey: ["analysis-results", analysisId],
    queryFn: () => getAnalysisResults(analysisId!),
    enabled: !!analysisId,
    refetchInterval: (query) => {
      const data = query.state.data as Record<string, unknown> | undefined;
      return data?.status === "processing" ? 2000 : false;
    },
  });
}
