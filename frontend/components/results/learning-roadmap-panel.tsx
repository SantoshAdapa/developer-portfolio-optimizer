"use client";

import { motion } from "framer-motion";
import { BookOpen, Clock, ExternalLink } from "lucide-react";
import type { LearningRoadmapResult } from "@/types";

interface LearningRoadmapPanelProps {
  roadmap: LearningRoadmapResult;
}

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export function LearningRoadmapPanel({ roadmap }: LearningRoadmapPanelProps) {
  return (
    <div className="glass-card p-6 md:p-8 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/15">
            <BookOpen className="h-4 w-4 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Learning Roadmap
            </h3>
            <p className="text-xs text-muted-foreground/70 mt-0.5">
              Path to {roadmap.target_role}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Clock className="h-3.5 w-3.5" />
          <span>~{roadmap.total_estimated_weeks} weeks</span>
        </div>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        className="space-y-3"
      >
        {roadmap.steps.map((step) => (
          <motion.div
            key={step.order}
            variants={item}
            className="glass-card-hover px-4 py-3 !rounded-xl"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-400">
                  {step.order}
                </span>
                <span className="text-sm font-semibold">{step.skill}</span>
              </div>
              <span className="text-xs text-muted-foreground">
                {step.estimated_weeks}w
              </span>
            </div>
            <div className="ml-7 space-y-1.5">
              <p className="text-xs text-muted-foreground">
                {step.current_level === "none" ? "Start from scratch" : `${step.current_level} → ${step.target_level}`}
              </p>
              {step.resources.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {step.resources.map((res, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 rounded-md bg-white/[0.05] px-2 py-0.5 text-[10px] text-muted-foreground"
                    >
                      <ExternalLink className="h-2.5 w-2.5" />
                      {res}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
