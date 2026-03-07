"use client";

import { motion } from "framer-motion";
import { BarChart3, Crown } from "lucide-react";
import type { BenchmarkResponse } from "@/types";

interface BenchmarkPanelProps {
  benchmark: BenchmarkResponse;
}

const archetypeGradients: Record<string, string> = {
  junior_developer: "from-slate-400 to-slate-300",
  mid_level_developer: "from-blue-500 to-cyan-400",
  senior_engineer: "from-violet-500 to-purple-400",
  ml_engineer: "from-emerald-500 to-green-400",
  open_source_contributor: "from-amber-500 to-yellow-400",
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 },
  },
};

const barVariant = {
  hidden: { opacity: 0, x: -16 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

export function BenchmarkPanel({ benchmark }: BenchmarkPanelProps) {
  // Build bar entries: your score + 3 key archetypes
  const archetypeKeys = ["junior_developer", "mid_level_developer", "senior_engineer"];
  const barEntries = [
    {
      label: "Your Score",
      value: benchmark.developer_overall,
      gradient: "from-blue-400 via-violet-400 to-purple-400",
      isUser: true,
    },
    ...benchmark.archetype_details
      .filter((a) => archetypeKeys.includes(a.key))
      .sort((a, b) => a.average_overall - b.average_overall)
      .map((a) => ({
        label: a.label,
        value: a.average_overall,
        gradient: archetypeGradients[a.key] || "from-gray-400 to-gray-300",
        isUser: false,
      })),
  ];

  return (
    <div className="glass-card p-6 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/15">
          <BarChart3 className="h-5 w-5 text-violet-400" />
        </div>
        <div>
          <h3 className="text-lg font-bold tracking-tight">
            You vs <span className="gradient-text">Industry Benchmarks</span>
          </h3>
          <p className="text-xs text-muted-foreground">
            See how you compare to typical developer profiles
          </p>
        </div>
      </div>

      {/* Closest archetype badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-violet-500/10 to-purple-500/10 border border-violet-500/20 w-fit"
      >
        <Crown className="h-4 w-4 text-violet-400" />
        <span className="text-sm font-medium">
          Closest Match:{" "}
          <span className="gradient-text font-semibold">
            {benchmark.closest_archetype_label}
          </span>
        </span>
        <span className="text-xs text-muted-foreground ml-2">
          Top {100 - benchmark.score_percentile}%
        </span>
      </motion.div>

      {/* Animated bars */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-4"
      >
        {barEntries.map((entry) => (
          <motion.div key={entry.label} variants={barVariant} className="space-y-1.5">
            <div className="flex items-center justify-between text-sm">
              <span className={`font-medium ${entry.isUser ? "text-white" : "text-muted-foreground"}`}>
                {entry.label}
                {entry.isUser && (
                  <span className="ml-2 text-[10px] uppercase tracking-widest text-violet-400 font-semibold">
                    you
                  </span>
                )}
              </span>
              <span className="text-muted-foreground tabular-nums text-xs">
                {entry.value}/100
              </span>
            </div>
            <div className="h-3 w-full rounded-full bg-white/[0.06] overflow-hidden">
              <motion.div
                className={`h-full rounded-full bg-gradient-to-r ${entry.gradient} ${
                  entry.isUser ? "shadow-[0_0_12px_rgba(139,92,246,0.3)]" : ""
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${entry.value}%` }}
                transition={{ duration: 1, delay: 0.4, ease: "easeOut" }}
              />
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Fit scores for all archetypes */}
      <div className="pt-2 border-t border-white/[0.06]">
        <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-3">
          Archetype Fit Scores
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {benchmark.archetype_details.map((a) => (
            <motion.div
              key={a.key}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.6 }}
              className="glass-card-hover px-3 py-2.5 text-center"
            >
              <p className="text-xs text-muted-foreground truncate">{a.label}</p>
              <p className="text-lg font-bold tabular-nums mt-0.5">
                {a.fit_score.toFixed(0)}
                <span className="text-xs text-muted-foreground font-normal">%</span>
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
