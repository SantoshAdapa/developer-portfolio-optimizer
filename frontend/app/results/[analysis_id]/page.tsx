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
    transition: { duration: 0.5, delay: i * 0.12, ease: "easeOut" },
  }),
};

export default function ResultsPage() {
  const params = useParams<{ analysis_id: string }>();
  const analysisId = params.analysis_id;

  const analysis = useAnalysisResults(analysisId);
  const portfolio = usePortfolioSuggestions(analysisId);
  const projects = useProjectIdeas(analysisId);
  const roadmap = useCareerRoadmap(analysisId);
  const benchmarkQuery = useBenchmarks(analysisId);

  const data = analysis.data as AnalysisResponse | undefined;
  const portfolioData = portfolio.data as PortfolioSuggestion[] | undefined;
  const projectsData = projects.data as ProjectIdea[] | undefined;
  const roadmapData = roadmap.data as CareerRoadmap | undefined;
  const benchmarkData = benchmarkQuery.data as BenchmarkResponse | undefined;

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
  if (analysis.isError) {
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
        <motion.section
          custom={0}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
          {data ? <ScoreOverview score={data.developer_score} /> : <ScoreSkeleton />}
        </motion.section>

        {/* 2 — AI Confidence */}
        <motion.section
          custom={1}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
          {data ? <ConfidenceMeter confidence={confidence} /> : <SectionSkeleton lines={1} />}
        </motion.section>

        {/* 3 — Skill Analysis */}
        <motion.section
          custom={2}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
          {data ? <SkillAnalysis skills={data.skills} /> : <SectionSkeleton lines={4} />}
        </motion.section>

        {/* 4 — AI Insight Callouts */}
        <motion.section
          custom={3}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
          {data ? (
            <InsightCallouts strengths={data.strengths} weaknesses={data.weaknesses} />
          ) : (
            <SectionSkeleton lines={3} />
          )}
        </motion.section>

        {/* 5 — Portfolio Suggestions */}
        <motion.section
          custom={4}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
          {portfolioData ? (
            <SuggestionsPanel suggestions={portfolioData} />
          ) : portfolio.isLoading ? (
            <SectionSkeleton lines={4} />
          ) : null}
        </motion.section>

        {/* 6 — Project Ideas */}
        <motion.section
          custom={5}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
          {projectsData ? (
            <ProjectIdeas ideas={projectsData} />
          ) : projects.isLoading ? (
            <SectionSkeleton lines={4} />
          ) : null}
        </motion.section>

        {/* 7 — Skill Radar Chart */}
        <motion.section
          custom={6}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
          {radarData ? <SkillRadarChart data={radarData} /> : <SectionSkeleton lines={3} />}
        </motion.section>

        {/* 8 — AI Score Explanation */}
        <motion.section
          custom={7}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
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
        <motion.section
          custom={8}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
          {benchmarkData ? (
            <BenchmarkPanel benchmark={benchmarkData} />
          ) : benchmarkQuery.isLoading ? (
            <SectionSkeleton lines={4} />
          ) : null}
        </motion.section>

        {/* 10 — Career Roadmap */}
        <motion.section
          custom={9}
          variants={sectionVariant}
          initial="hidden"
          animate="visible"
        >
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
