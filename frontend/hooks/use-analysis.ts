"use client";

import { useMutation } from "@tanstack/react-query";
import {
  uploadResume,
  analyzeGitHub,
  runAnalysis,
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
    mutationFn: (params: { resume_id?: string; github_username?: string }) =>
      runAnalysis(params),
  });
}
