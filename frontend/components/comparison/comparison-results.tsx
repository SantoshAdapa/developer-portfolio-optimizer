"use client";

import { motion } from "framer-motion";
import { Trophy, Equal, Star, Code2, Lightbulb, Shield, Target } from "lucide-react";
import { ScoreMeter } from "@/components/analysis/score-meter";
import { SkillRadarChart } from "@/components/charts/skill-radar-chart";
import type {
  CompareResponse,
  AnalysisResponse,
  RadarDataPoint,
  RadarScores,
} from "@/types";

interface ComparisonResultsProps {
  comparison: CompareResponse;
  analysisA: AnalysisResponse;
  analysisB: AnalysisResponse;
}

function radarScoresToData(scores: RadarScores | null | undefined): RadarDataPoint[] {
  if (!scores) return [];
  const dims: (keyof RadarScores)[] = ["backend", "frontend", "devops", "data", "ml_ai", "testing"];
  return dims.map((dim) => ({
    dimension: dim,
    value: scores[dim] ?? 0,
    fullMark: 100,
  }));
}

function buildRadarDataFallback(analysis: AnalysisResponse): RadarDataPoint[] {
  if (analysis.radar_scores) {
    return radarScoresToData(analysis.radar_scores);
  }
  const RADAR_DIMS = ["backend", "frontend", "devops", "data", "ml_ai", "testing"];
  return RADAR_DIMS.map((dim) => {
    const matching = analysis.skills.filter(
      (s) =>
        s.category.toLowerCase().includes(dim) ||
        dim.includes(s.category.toLowerCase())
    );
    const value =
      matching.length > 0
        ? Math.min(
            100,
            matching.length * 15 +
              (matching.some((s) => s.proficiency === "advanced") ? 25 : 0)
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
  const radarA = comparison.radar_scores_a
    ? radarScoresToData(comparison.radar_scores_a)
    : buildRadarDataFallback(analysisA);
  const radarB = comparison.radar_scores_b
    ? radarScoresToData(comparison.radar_scores_b)
    : buildRadarDataFallback(analysisB);

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
            <div className="h-8 w-px bg-foreground/[0.08]" />
            <span className="text-xs font-bold text-muted-foreground/50 uppercase tracking-widest">
              vs
            </span>
            <div className="h-8 w-px bg-foreground/[0.08]" />
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
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: "var(--bar-track)" }}>
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
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: "var(--bar-track)" }}>
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

      {/* ── 4. Skill Differences ────────────────────── */}
      {comparison.skill_gap.length > 0 && (
        <motion.div variants={section} className="glass-card p-6 md:p-8">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-5">
            Skill Differences
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Developer A unique skills */}
            {(() => {
              const aSkills = comparison.skill_gap.filter(
                (g) => g.present_in === "developer_a"
              );
              return (
                aSkills.length > 0 && (
                  <div className="space-y-3 p-4 rounded-xl bg-foreground/[0.02] border border-foreground/[0.06]">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-violet-400" />
                      <span className="text-xs font-bold uppercase tracking-widest text-violet-400">
                        Developer A Strengths
                      </span>
                      <span className="ml-auto text-xs text-muted-foreground">
                        {aSkills.length} skills
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {aSkills.map((gap) => (
                        <span
                          key={gap.skill}
                          className="text-[11px] px-2.5 py-1 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20 capitalize"
                        >
                          {gap.skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )
              );
            })()}

            {/* Developer B unique skills */}
            {(() => {
              const bSkills = comparison.skill_gap.filter(
                (g) => g.present_in === "developer_b"
              );
              return (
                bSkills.length > 0 && (
                  <div className="space-y-3 p-4 rounded-xl bg-foreground/[0.02] border border-foreground/[0.06]">
                    <div className="flex items-center gap-2">
                      <Target className="h-4 w-4 text-blue-400" />
                      <span className="text-xs font-bold uppercase tracking-widest text-blue-400">
                        Developer B Strengths
                      </span>
                      <span className="ml-auto text-xs text-muted-foreground">
                        {bSkills.length} skills
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {bSkills.map((gap) => (
                        <span
                          key={gap.skill}
                          className="text-[11px] px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 capitalize"
                        >
                          {gap.skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )
              );
            })()}
          </div>
        </motion.div>
      )}

      {/* ── 5. Winner Summary ────────────────────────── */}
      <motion.div
        variants={section}
        className={`glass-card p-6 md:p-8 bg-gradient-to-br ${winnerGradient}`}
      >
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-foreground/[0.06]">
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

      {/* ── 6. Developer Summaries ────────────────────── */}
      {(comparison.developer_a_summary?.top_skills?.length > 0 ||
        comparison.developer_b_summary?.top_skills?.length > 0) && (
        <motion.div variants={section} className="glass-card p-6 md:p-8">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-5">
            Developer Summaries
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { data: comparison.developer_a_summary, color: "violet" },
              { data: comparison.developer_b_summary, color: "blue" },
            ].map(({ data, color }) => (
              <div
                key={data?.label}
                className="space-y-3 p-4 rounded-xl bg-foreground/[0.02] border border-foreground/[0.06]"
              >
                <div className="flex items-center gap-2">
                  <Star className={`h-4 w-4 text-${color}-400`} />
                  <span className={`text-sm font-bold text-${color}-400`}>
                    {data?.label}
                  </span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    Score: {data?.overall_score}
                  </span>
                </div>
                {data?.github_username && (
                  <p className="text-xs text-muted-foreground">
                    GitHub: @{data.github_username} · {data.public_repos} repos · {data.total_stars} stars
                  </p>
                )}
                <p className="text-xs text-muted-foreground">
                  {data?.skill_count} skills detected
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {data?.top_skills?.map((skill: string) => (
                    <span
                      key={skill}
                      className={`text-[10px] px-2 py-0.5 rounded-full bg-${color}-500/10 text-${color}-400 border border-${color}-500/20`}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── 7. Strengths & Weaknesses ────────────────── */}
      {comparison.strengths_weaknesses?.developer_a && (
        <motion.div variants={section} className="glass-card p-6 md:p-8">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-5">
            Strengths &amp; Weaknesses
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { data: comparison.strengths_weaknesses.developer_a, label: "Developer A", color: "violet" },
              { data: comparison.strengths_weaknesses.developer_b, label: "Developer B", color: "blue" },
            ].map(({ data, label, color }) => (
              <div key={label} className="space-y-3">
                <span className={`text-xs font-bold uppercase tracking-widest text-${color}-400`}>
                  {label}
                </span>
                {data?.strengths?.length > 0 && (
                  <div>
                    <p className="text-xs text-emerald-400 font-semibold mb-1">Strengths</p>
                    <ul className="text-xs text-muted-foreground space-y-0.5">
                      {data.strengths.map((s: string) => (
                        <li key={s} className="flex items-center gap-1.5">
                          <span className="h-1 w-1 rounded-full bg-emerald-400" />
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {data?.weaknesses?.length > 0 && (
                  <div>
                    <p className="text-xs text-amber-400 font-semibold mb-1">Weaknesses</p>
                    <ul className="text-xs text-muted-foreground space-y-0.5">
                      {data.weaknesses.map((w: string) => (
                        <li key={w} className="flex items-center gap-1.5">
                          <span className="h-1 w-1 rounded-full bg-amber-400" />
                          {w}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── 8. Comparison Insights ────────────────────── */}
      {comparison.insights?.length > 0 && (
        <motion.div variants={section} className="glass-card p-6 md:p-8">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="h-4 w-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Comparison Insights
            </h3>
          </div>
          <ul className="space-y-2">
            {comparison.insights.map((insight, i) => (
              <li key={i} className="text-sm text-muted-foreground leading-relaxed flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                {insight}
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      {/* ── 9. Skill Overlap ─────────────────────────── */}
      {comparison.skill_comparison?.shared_skills?.length > 0 && (
        <motion.div variants={section} className="glass-card p-6 md:p-8">
          <div className="flex items-center gap-2 mb-4">
            <Code2 className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Shared Skills ({comparison.skill_comparison.shared_skills.length})
            </h3>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {comparison.skill_comparison.shared_skills.map((skill: string) => (
              <span
                key={skill}
                className="text-[11px] px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 capitalize"
              >
                {skill}
              </span>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
