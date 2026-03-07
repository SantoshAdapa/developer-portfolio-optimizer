"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getPortfolioSuggestions,
  getProjectIdeas,
  getCareerRoadmap,
  getBenchmarks,
} from "@/services/api";

export function usePortfolioSuggestions(analysisId: string | undefined) {
  return useQuery({
    queryKey: ["portfolio-suggestions", analysisId],
    queryFn: () => getPortfolioSuggestions(analysisId!),
    enabled: !!analysisId,
  });
}

export function useProjectIdeas(analysisId: string | undefined) {
  return useQuery({
    queryKey: ["project-ideas", analysisId],
    queryFn: () => getProjectIdeas(analysisId!),
    enabled: !!analysisId,
  });
}

export function useCareerRoadmap(analysisId: string | undefined) {
  return useQuery({
    queryKey: ["career-roadmap", analysisId],
    queryFn: () => getCareerRoadmap(analysisId!),
    enabled: !!analysisId,
  });
}

export function useBenchmarks(analysisId: string | undefined) {
  return useQuery({
    queryKey: ["benchmarks", analysisId],
    queryFn: () => getBenchmarks(analysisId!),
    enabled: !!analysisId,
  });
}
