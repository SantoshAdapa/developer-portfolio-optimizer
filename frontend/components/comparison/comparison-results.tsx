"use client";

import { motion } from "framer-motion";
import { Trophy, ArrowRight, Equal } from "lucide-react";
import { ScoreMeter } from "@/components/analysis/score-meter";
import { SkillRadarChart } from "@/components/charts/skill-radar-chart";
import type {
  CompareResponse,
  AnalysisResponse,
  RadarDataPoint,
} from "@/types";

interface ComparisonResultsProps {
  comparison: CompareResponse;
  analysisA: AnalysisResponse;
  analysisB: AnalysisResponse;
}

const RADAR_DIMS = [
  "backend",
  "frontend",
  "devops",
  "data",
  "machine_learning",
  "documentation",
];

function buildRadarData(analysis: AnalysisResponse): RadarDataPoint[] {
  return RADAR_DIMS.map((dim) => {
    const matching = analysis.skills.technical_skills.filter(
      (s) =>
        s.category.toLowerCase().includes(dim) ||
        dim.includes(s.category.toLowerCase())
    );
    const value =
      matching.length > 0
        ? Math.min(
            100,
            matching.length * 15 +
              (matching.some(
                (s) => s.level === "advanced" || s.level === "expert"
              )
                ? 25
                : 0)
          )
        : 0;
    return { dimension: dim, value, fullMark: 100 };
  });
}

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.1 },
  },
};

const section = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" },
  },
};

function formatDimension(d: string): string {
  return d
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function ComparisonResults({
  comparison,
  analysisA,
  analysisB,
}: ComparisonResultsProps) {
  const radarA = buildRadarData(analysisA);
  const radarB = buildRadarData(analysisB);

  const winnerLabel =
    comparison.winner === "developer_a"
      ? "Developer A"
      : comparison.winner === "developer_b"
        ? "Developer B"
        : null;

  const WinnerIcon =
    comparison.winner === "tie" ? Equal : Trophy;

  const winnerGradient =
    comparison.winner === "developer_a"
      ? "from-violet-500/15 to-purple-500/15 border-violet-500/25"
      : comparison.winner === "developer_b"
        ? "from-blue-500/15 to-cyan-500/15 border-blue-500/25"
        : "from-gray-500/15 to-gray-400/15 border-gray-500/25";

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* ── 1. Score Comparison ───────────────────────── */}
      <motion.div variants={section} className="glass-card p-6 md:p-8">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-6">
          Score Comparison
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] items-center gap-8">
          {/* Dev A */}
          <div className="flex flex-col items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-widest text-violet-400">
              Developer A
            </span>
            <ScoreMeter
              score={analysisA.developer_score.overall}
              label="Score A"
              size={160}
              strokeWidth={10}
            />
          </div>

          {/* VS divider */}
          <div className="hidden md:flex flex-col items-center gap-2">
            <div className="h-8 w-px bg-white/[0.08]" />
            <span className="text-xs font-bold text-muted-foreground/50 uppercase tracking-widest">
              vs
            </span>
            <div className="h-8 w-px bg-white/[0.08]" />
          </div>

          {/* Dev B */}
          <div className="flex flex-col items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-widest text-blue-400">
              Developer B
            </span>
            <ScoreMeter
              score={analysisB.developer_score.overall}
              label="Score B"
              size={160}
              strokeWidth={10}
            />
          </div>
        </div>
      </motion.div>

      {/* ── 2. Skill Radar Charts ────────────────────── */}
      <motion.div variants={section}>
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
          Skill Distribution
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-center font-semibold text-violet-400 uppercase tracking-widest mb-2">
              Developer A
            </p>
            <SkillRadarChart data={radarA} height={280} />
          </div>
          <div>
            <p className="text-xs text-center font-semibold text-blue-400 uppercase tracking-widest mb-2">
              Developer B
            </p>
            <SkillRadarChart data={radarB} height={280} />
          </div>
        </div>
      </motion.div>

      {/* ── 3. Dimension Breakdown ───────────────────── */}
      {comparison.dimension_comparison.length > 0 && (
        <motion.div variants={section} className="glass-card p-6 md:p-8">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-5">
            Dimension Breakdown
          </h3>
          <div className="space-y-4">
            {comparison.dimension_comparison.map((dim) => {
              const maxVal = Math.max(dim.developer_a, dim.developer_b, 1);
              const aWins = dim.developer_a > dim.developer_b;
              const tie = dim.developer_a === dim.developer_b;

              return (
                <div key={dim.dimension} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">
                      {formatDimension(dim.dimension)}
                    </span>
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {dim.developer_a} vs {dim.developer_b}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Dev A bar */}
                    <div className="flex-1 h-2 rounded-full bg-white/[0.06] overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${
                          aWins || tie
                            ? "bg-gradient-to-r from-violet-500 to-purple-400"
                            : "bg-violet-500/30"
                        }`}
                        initial={{ width: 0 }}
                        animate={{
                          width: `${(dim.developer_a / maxVal) * 100}%`,
                        }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                      />
                    </div>
                    {/* Dev B bar */}
                    <div className="flex-1 h-2 rounded-full bg-white/[0.06] overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${
                          !aWins || tie
                            ? "bg-gradient-to-r from-blue-500 to-cyan-400"
                            : "bg-blue-500/30"
                        }`}
                        initial={{ width: 0 }}
                        animate={{
                          width: `${(dim.developer_b / maxVal) * 100}%`,
                        }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="flex items-center justify-center gap-6 mt-5 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-violet-500" />
              Developer A
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-blue-500" />
              Developer B
            </span>
          </div>
        </motion.div>
      )}

      {/* ── 4. Skill Gap List ────────────────────────── */}
      {comparison.skill_gap.length > 0 && (
        <motion.div variants={section} className="glass-card p-6 md:p-8">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
            Skill Differences
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {comparison.skill_gap.map((gap) => {
              const isA = gap.present_in === "developer_a";
              return (
                <motion.div
                  key={gap.skill}
                  initial={{ opacity: 0, x: isA ? -8 : 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/[0.06]"
                >
                  <ArrowRight
                    className={`h-3.5 w-3.5 shrink-0 ${
                      isA ? "text-violet-400" : "text-blue-400 rotate-180"
                    }`}
                  />
                  <span className="text-sm capitalize">{gap.skill}</span>
                  <span
                    className={`ml-auto text-[10px] uppercase tracking-widest font-semibold ${
                      isA ? "text-violet-400" : "text-blue-400"
                    }`}
                  >
                    {isA ? "Dev A" : "Dev B"}
                  </span>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* ── 5. Winner Summary ────────────────────────── */}
      <motion.div
        variants={section}
        className={`glass-card p-6 md:p-8 bg-gradient-to-br ${winnerGradient}`}
      >
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/[0.06]">
            <WinnerIcon
              className={`h-6 w-6 ${
                comparison.winner === "developer_a"
                  ? "text-violet-400"
                  : comparison.winner === "developer_b"
                    ? "text-blue-400"
                    : "text-gray-400"
              }`}
            />
          </div>
          <div>
            <h3 className="text-lg font-bold tracking-tight">
              {winnerLabel ? (
                <>
                  <span
                    className={
                      comparison.winner === "developer_a"
                        ? "text-violet-400"
                        : "text-blue-400"
                    }
                  >
                    {winnerLabel}
                  </span>{" "}
                  leads by {Math.abs(comparison.score_difference)} points
                </>
              ) : (
                "It\u2019s a tie!"
              )}
            </h3>
            <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
              {comparison.summary}
            </p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
