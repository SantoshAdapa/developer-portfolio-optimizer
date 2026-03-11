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
import { PortfolioDepth } from "@/components/results/portfolio-depth";
import { SkillGapPanel } from "@/components/results/skill-gap-panel";
import { LearningRoadmapPanel } from "@/components/results/learning-roadmap-panel";
import { MarketDemandPanel } from "@/components/results/market-demand-panel";
import { CareerDirectionPanel } from "@/components/results/career-direction-panel";
import {
  ScoreSkeleton,
  SectionSkeleton,
} from "@/components/results/result-skeletons";
import { demoProfiles } from "@/lib/demo-profiles";
import type {
  AnalysisResponse,
  BenchmarkResponse,
  Suggestion,
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
  const portfolioData = (isDemo ? demoProfile?.suggestions : portfolio.data) as Suggestion[] | undefined;
  const projectsData = (isDemo ? demoProfile?.projectIdeas : projects.data) as ProjectIdea[] | undefined;
  const roadmapData = (isDemo ? demoProfile?.roadmap : roadmap.data) as CareerRoadmap | undefined;
  const benchmarkData = (isDemo ? undefined : benchmarkQuery.data) as BenchmarkResponse | undefined;

  // Build radar data from radar_scores (skill distribution) or fall back to score categories
  const radarData: RadarDataPoint[] | undefined = data?.radar_scores
    ? Object.entries(data.radar_scores)
        .filter(([, value]) => typeof value === "number")
        .map(([dim, value]) => ({
          dimension: dim,
          value: value as number,
          fullMark: 100,
        }))
    : data
    ? Object.entries(data.developer_score.categories).map(([dim, value]) => ({
        dimension: dim,
        value,
        fullMark: 100,
      }))
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
          (Object.keys(data.developer_score.categories).length * 10 +
            data.skills.length * 3 +
            (data.github_summary ? 20 : 0)) *
            0.8
        )
      )
    : 0;

  // ── Derive strengths / weaknesses from AI insights or score categories ──
  const strengths = data?.ai_insights?.strengths ??
    (data
      ? Object.entries(data.developer_score.categories)
          .sort(([, a], [, b]) => b - a)
          .filter(([, v]) => v >= 60)
          .slice(0, 3)
          .map(([k, v]) => `Strong ${k.replace(/_/g, " ")} (${v}/100)`)
      : []);
  const weaknesses = data?.ai_insights?.weaknesses ??
    (data
      ? Object.entries(data.developer_score.categories)
          .sort(([, a], [, b]) => a - b)
          .filter(([, v]) => v < 60)
          .slice(0, 3)
          .map(([k, v]) => `${k.replace(/_/g, " ")} needs improvement (${v}/100)`)
      : []);

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
          {data ? (
            <SkillAnalysis
              skills={data.skills}
              programmingLanguages={data.programming_languages}
            />
          ) : (
            <SectionSkeleton lines={4} />
          )}
        </motion.section>

        {/* 4 — AI Insight Callouts */}
        <motion.section {...sectionProps(3)}>
          {data ? (
            <InsightCallouts
              strengths={strengths}
              weaknesses={weaknesses}
              aiInsights={data.ai_insights}
            />
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

        {/* 8 — Portfolio Depth */}
        <motion.section {...sectionProps(7)}>
          {data?.portfolio_depth ? (
            <PortfolioDepth depth={data.portfolio_depth} />
          ) : null}
        </motion.section>

        {/* 9 — Skill Gap Analysis */}
        <motion.section {...sectionProps(8)}>
          {data?.skill_gap ? (
            <SkillGapPanel skillGap={data.skill_gap} />
          ) : null}
        </motion.section>

        {/* 10 — Learning Roadmap */}
        <motion.section {...sectionProps(9)}>
          {data?.learning_roadmap && data.learning_roadmap.steps.length > 0 ? (
            <LearningRoadmapPanel roadmap={data.learning_roadmap} />
          ) : null}
        </motion.section>

        {/* 11 — Market Demand */}
        <motion.section {...sectionProps(10)}>
          {data?.market_demand ? (
            <MarketDemandPanel demand={data.market_demand} />
          ) : null}
        </motion.section>

        {/* 12 — Career Direction */}
        <motion.section {...sectionProps(11)}>
          {data?.career_direction ? (
            <CareerDirectionPanel direction={data.career_direction} />
          ) : null}
        </motion.section>

        {/* 13 — AI Score Explanation */}
        <motion.section {...sectionProps(12)}>
          {data ? (
            <AiExplanation
              score={data.developer_score}
              skills={data.skills}
              github={data.github_summary}
            />
          ) : (
            <SectionSkeleton lines={4} />
          )}
        </motion.section>

        {/* 14 — Benchmark Panel */}
        <motion.section {...sectionProps(13)}>
          {benchmarkData ? (
            <BenchmarkPanel benchmark={benchmarkData} />
          ) : benchmarkQuery.isLoading ? (
            <SectionSkeleton lines={4} />
          ) : null}
        </motion.section>

        {/* 15 — Career Roadmap */}
        <motion.section {...sectionProps(14)}>
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
