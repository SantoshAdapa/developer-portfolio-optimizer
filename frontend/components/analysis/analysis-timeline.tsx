"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Check, Loader2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

export type TimelineStep = {
  id: string;
  label: string;
  status: "pending" | "active" | "complete";
};

interface AnalysisTimelineProps {
  steps: TimelineStep[];
}

const stepVariants = {
  hidden: { opacity: 0, x: -16 },
  visible: { opacity: 1, x: 0 },
};

export function AnalysisTimeline({ steps }: AnalysisTimelineProps) {
  return (
    <div className="space-y-1">
      {steps.map((step, i) => (
        <motion.div
          key={step.id}
          variants={stepVariants}
          initial="hidden"
          animate="visible"
          transition={{ duration: 0.4, delay: i * 0.08, ease: "easeOut" }}
          className="flex items-start gap-3 relative"
        >
          {/* Connector line */}
          {i < steps.length - 1 && (
            <div
              className={cn(
                "absolute left-[13px] top-[28px] w-[2px] h-[calc(100%)] transition-colors duration-500",
                step.status === "complete"
                  ? "bg-emerald-500/40"
                  : "bg-foreground/[0.06]"
              )}
            />
          )}

          {/* Icon */}
          <div className="relative z-10 mt-0.5 shrink-0">
            <AnimatePresence mode="wait">
              {step.status === "complete" ? (
                <motion.div
                  key="check"
                  initial={{ scale: 0, rotate: -90 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  className="flex h-[26px] w-[26px] items-center justify-center rounded-full bg-emerald-500/20 ring-2 ring-emerald-500/40"
                >
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                </motion.div>
              ) : step.status === "active" ? (
                <motion.div
                  key="active"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="flex h-[26px] w-[26px] items-center justify-center rounded-full bg-blue-500/20 ring-2 ring-blue-500/40"
                >
                  <Loader2 className="h-3.5 w-3.5 text-blue-400 animate-spin" />
                </motion.div>
              ) : (
                <motion.div
                  key="pending"
                  className="flex h-[26px] w-[26px] items-center justify-center rounded-full bg-foreground/[0.04] ring-2 ring-foreground/[0.08]"
                >
                  <Circle className="h-2.5 w-2.5 text-muted-foreground/40" />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Label */}
          <div className="min-h-[44px] flex items-center">
            <span
              className={cn(
                "text-sm transition-colors duration-300",
                step.status === "complete"
                  ? "text-emerald-400 font-medium"
                  : step.status === "active"
                  ? "text-foreground font-medium"
                  : "text-muted-foreground/60"
              )}
            >
              {step.label}
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ─── Hook: drive the timeline with simulated progress ─────────

const STEP_DEFINITIONS = [
  { id: "parse", label: "Parsing resume" },
  { id: "github", label: "Analyzing GitHub repositories" },
  { id: "skills", label: "Extracting developer skills" },
  { id: "score", label: "Computing developer score" },
  { id: "recs", label: "Generating recommendations" },
] as const;

import { useState, useEffect, useRef } from "react";

export function useTimelineProgress(isRunning: boolean) {
  const [steps, setSteps] = useState<TimelineStep[]>(
    STEP_DEFINITIONS.map((s) => ({ ...s, status: "pending" as const }))
  );

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentIndexRef = useRef(0);

  useEffect(() => {
    if (!isRunning) {
      // Reset
      currentIndexRef.current = 0;
      setSteps(STEP_DEFINITIONS.map((s) => ({ ...s, status: "pending" })));
      return;
    }

    // Start progressing
    currentIndexRef.current = 0;
    setSteps(
      STEP_DEFINITIONS.map((s, i) => ({
        ...s,
        status: i === 0 ? "active" : "pending",
      }))
    );

    intervalRef.current = setInterval(() => {
      currentIndexRef.current += 1;
      const idx = currentIndexRef.current;

      if (idx >= STEP_DEFINITIONS.length) {
        // All complete
        setSteps(STEP_DEFINITIONS.map((s) => ({ ...s, status: "complete" })));
        if (intervalRef.current) clearInterval(intervalRef.current);
        return;
      }

      setSteps(
        STEP_DEFINITIONS.map((s, i) => ({
          ...s,
          status: i < idx ? "complete" : i === idx ? "active" : "pending",
        }))
      );
    }, 2200);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isRunning]);

  // Allow instantly completing all steps
  const completeAll = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setSteps(STEP_DEFINITIONS.map((s) => ({ ...s, status: "complete" })));
  };

  return { steps, completeAll };
}
