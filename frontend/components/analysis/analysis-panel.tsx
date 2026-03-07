"use client";

import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, Sparkles } from "lucide-react";
import {
  AnalysisTimeline,
  type TimelineStep,
} from "@/components/analysis/analysis-timeline";
import { ScoreMeter } from "@/components/analysis/score-meter";
import { Skeleton } from "@/components/ui/skeleton";

type PanelState = "idle" | "processing" | "complete" | "error";

interface AnalysisPanelProps {
  state: PanelState;
  timelineSteps: TimelineStep[];
  score?: number;
  error?: string | null;
}

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

export function AnalysisPanel({
  state,
  timelineSteps,
  score,
  error,
}: AnalysisPanelProps) {
  return (
    <div className="glass-card p-6 md:p-8 h-full min-h-[480px] flex flex-col">
      <AnimatePresence mode="wait">
        {/* ── Idle state ───────────────────────────────── */}
        {state === "idle" && (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex flex-col items-center justify-center text-center gap-4"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/[0.04] border border-white/[0.06]">
              <BrainCircuit className="h-8 w-8 text-muted-foreground/40" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground/60">
                AI Analysis
              </p>
              <p className="mt-1 text-xs text-muted-foreground/40 max-w-[240px]">
                Upload your resume or enter a GitHub profile, then click
                Analyze to start.
              </p>
            </div>
          </motion.div>
        )}

        {/* ── Processing state ─────────────────────────── */}
        {state === "processing" && (
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center gap-3 mb-6">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/20">
                <Sparkles className="h-4 w-4 text-blue-400 animate-pulse-glow" />
              </div>
              <div>
                <p className="text-sm font-semibold">AI is analyzing...</p>
                <p className="text-xs text-muted-foreground">
                  This usually takes under a minute
                </p>
              </div>
            </div>

            {/* Timeline */}
            <AnalysisTimeline steps={timelineSteps} />

            {/* Skeleton preview */}
            <div className="mt-8 space-y-4">
              <p className="text-xs text-muted-foreground/50 uppercase tracking-wider font-medium">
                Preview
              </p>
              <div className="flex items-center gap-4">
                <Skeleton className="h-20 w-20 rounded-full shrink-0" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Skeleton className="h-16 rounded-xl" />
                <Skeleton className="h-16 rounded-xl" />
              </div>
              <Skeleton className="h-12 rounded-xl" />
            </div>
          </motion.div>
        )}

        {/* ── Complete state (brief score preview) ──── */}
        {state === "complete" && score !== undefined && (
          <motion.div
            key="complete"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            exit={{ opacity: 0 }}
            className="flex-1 flex flex-col items-center justify-center gap-6"
          >
            <ScoreMeter score={score} />
            <div className="text-center">
              <p className="text-sm font-medium text-emerald-400">
                Analysis complete
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Redirecting to your results...
              </p>
            </div>
          </motion.div>
        )}

        {/* ── Error state ──────────────────────────────── */}
        {state === "error" && (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex flex-col items-center justify-center text-center gap-4"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/20">
              <BrainCircuit className="h-8 w-8 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-red-400">
                Analysis failed
              </p>
              <p className="mt-1 text-xs text-muted-foreground max-w-[280px]">
                {error || "Something went wrong. Please try again."}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
