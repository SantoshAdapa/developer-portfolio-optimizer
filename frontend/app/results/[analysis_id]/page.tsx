"use client";

import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAnalysisResults } from "@/hooks/use-analysis";
import {
  usePortfolioSuggestions,
  useProjectIdeas,
  useCareerRoadmap,
  useBenchmarks,
} from "@/hooks/use-recommendations";
import { ScoreOverview } from "@/components/results/score-overview";
import { ConfidenceMeter } from "@/components/results/confidence-meter";
import { SkillAnalysis } from "@/components/results/skill-analysis";
import { InsightCallouts } from "@/components/results/insight-callouts";
import { SuggestionsPanel } from "@/components/results/suggestions-panel";
import { ProjectIdeas } from "@/components/results/project-ideas";
import { CareerRoadmapSection } from "@/components/results/career-roadmap";
import { ExportReport } from "@/components/results/export-report";
import { BenchmarkPanel } from "@/components/benchmark/benchmark-panel";
import { SkillRadarChart } from "@/components/charts/skill-radar-chart";
import { AiExplanation } from "@/components/analysis/ai-explanation";
import {
  ScoreSkeleton,
  SectionSkeleton,
} from "@/components/results/result-skeletons";
import { demoProfiles } from "@/lib/demo-profiles";
import type {
  AnalysisResponse,
  BenchmarkResponse,
  PortfolioSuggestion,
  ProjectIdea,
  CareerRoadmap,
  RadarDataPoint,
} from "@/types";

const sectionVariant = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.08, ease: "easeOut" },
  }),
};

const sectionProps = (i: number) => ({
  custom: i,
  variants: sectionVariant,
  initial: "hidden" as const,
  whileInView: "visible" as const,
  viewport: { once: true, margin: "-60px" },
});

export default function ResultsPage() {
  const params = useParams<{ analysis_id: string }>();
  const analysisId = params.analysis_id;

  // ── Demo detection ───────────────────────────────────────
  const isDemo = analysisId.startsWith("demo-");
  const demoProfile = isDemo
    ? demoProfiles.find((p) => p.analysis.analysis_id === analysisId)
    : undefined;

  // ── API queries (disabled for demo) ──────────────────────
  const analysis = useAnalysisResults(isDemo ? undefined : analysisId);
  const portfolio = usePortfolioSuggestions(isDemo ? undefined : analysisId);
  const projects = useProjectIdeas(isDemo ? undefined : analysisId);
  const roadmap = useCareerRoadmap(isDemo ? undefined : analysisId);
  const benchmarkQuery = useBenchmarks(isDemo ? undefined : analysisId);

  const data = (isDemo ? demoProfile?.analysis : analysis.data) as AnalysisResponse | undefined;
  const portfolioData = (isDemo ? demoProfile?.suggestions : portfolio.data) as PortfolioSuggestion[] | undefined;
  const projectsData = (isDemo ? demoProfile?.projectIdeas : projects.data) as ProjectIdea[] | undefined;
  const roadmapData = (isDemo ? demoProfile?.roadmap : roadmap.data) as CareerRoadmap | undefined;
  const benchmarkData = (isDemo ? undefined : benchmarkQuery.data) as BenchmarkResponse | undefined;

  // Build radar data from skill categories
  const radarDimensions = ["backend", "frontend", "devops", "data", "machine_learning", "documentation"];
  const radarData: RadarDataPoint[] | undefined = data
    ? radarDimensions.map((dim) => {
        // Try to derive a score from technical skills matching this dimension
        const matching = data.skills.technical_skills.filter(
          (s) => s.category.toLowerCase().includes(dim) || dim.includes(s.category.toLowerCase())
        );
        const value = matching.length > 0
          ? Math.min(100, matching.length * 15 + (matching.some((s) => s.level === "advanced" || s.level === "expert") ? 25 : 0))
          : 0;
        return { dimension: dim, value, fullMark: 100 };
      })
    : undefined;

  // ── Error state ──────────────────────────────────────────
  if (!isDemo && analysis.isError) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-20 text-center">
        <div className="glass-card p-10">
          <h2 className="text-xl font-bold text-red-400 mb-2">
            Failed to Load Results
          </h2>
          <p className="text-sm text-muted-foreground mb-6">
            {analysis.error?.message || "Something went wrong."}
          </p>
          <Button variant="glass" asChild>
            <Link href="/analyze">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Analysis
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  // ── Confidence score derived from data completeness ──────
  const confidence = data
    ? Math.min(
        100,
        Math.round(
          (data.developer_score.categories.length * 10 +
            data.skills.technical_skills.length * 3 +
            (data.github_insights ? 20 : 0)) *
            0.8
        )
      )
    : 0;

  return (
    <div className="mx-auto max-w-5xl px-6 py-12 md:py-20">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-10"
      >
        <div>
          <Button variant="ghost" size="sm" className="mb-2 -ml-3 text-muted-foreground" asChild>
            <Link href="/analyze">
              <ArrowLeft className="h-4 w-4 mr-1" />
              New Analysis
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">
            Your <span className="gradient-text">Results</span>
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            AI-powered analysis of your developer portfolio
          </p>
        </div>
        {data && (
          <ExportReport
            data={{ analysis: data, portfolio: portfolioData, projects: projectsData, roadmap: roadmapData }}
          />
        )}
      </motion.div>

      {/* Stacked sections with staggered reveal */}
      <div className="space-y-6">
        {/* 1 — Developer Score */}
        <motion.section {...sectionProps(0)}>
          {data ? <ScoreOverview score={data.developer_score} /> : <ScoreSkeleton />}
        </motion.section>

        {/* 2 — AI Confidence */}
        <motion.section {...sectionProps(1)}>
          {data ? <ConfidenceMeter confidence={confidence} /> : <SectionSkeleton lines={1} />}
        </motion.section>

        {/* 3 — Skill Analysis */}
        <motion.section {...sectionProps(2)}>
          {data ? <SkillAnalysis skills={data.skills} /> : <SectionSkeleton lines={4} />}
        </motion.section>

        {/* 4 — AI Insight Callouts */}
        <motion.section {...sectionProps(3)}>
          {data ? (
            <InsightCallouts strengths={data.strengths} weaknesses={data.weaknesses} />
          ) : (
            <SectionSkeleton lines={3} />
          )}
        </motion.section>

        {/* 5 — Portfolio Suggestions */}
        <motion.section {...sectionProps(4)}>
          {portfolioData ? (
            <SuggestionsPanel suggestions={portfolioData} />
          ) : portfolio.isLoading ? (
            <SectionSkeleton lines={4} />
          ) : null}
        </motion.section>

        {/* 6 — Project Ideas */}
        <motion.section {...sectionProps(5)}>
          {projectsData ? (
            <ProjectIdeas ideas={projectsData} />
          ) : projects.isLoading ? (
            <SectionSkeleton lines={4} />
          ) : null}
        </motion.section>

        {/* 7 — Skill Radar Chart */}
        <motion.section {...sectionProps(6)}>
          {radarData ? <SkillRadarChart data={radarData} /> : <SectionSkeleton lines={3} />}
        </motion.section>

        {/* 8 — AI Score Explanation */}
        <motion.section {...sectionProps(7)}>
          {data ? (
            <AiExplanation
              score={data.developer_score}
              skills={data.skills}
              github={data.github_insights}
            />
          ) : (
            <SectionSkeleton lines={4} />
          )}
        </motion.section>

        {/* 9 — Benchmark Panel */}
        <motion.section {...sectionProps(8)}>
          {benchmarkData ? (
            <BenchmarkPanel benchmark={benchmarkData} />
          ) : benchmarkQuery.isLoading ? (
            <SectionSkeleton lines={4} />
          ) : null}
        </motion.section>

        {/* 10 — Career Roadmap */}
        <motion.section {...sectionProps(9)}>
          {roadmapData ? (
            <CareerRoadmapSection roadmap={roadmapData} />
          ) : roadmap.isLoading ? (
            <SectionSkeleton lines={5} />
          ) : null}
        </motion.section>
      </div>
    </div>
  );
}
