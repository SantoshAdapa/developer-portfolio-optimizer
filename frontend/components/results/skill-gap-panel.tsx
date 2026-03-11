"use client";

import { motion } from "framer-motion";
import { Target, CheckCircle2, AlertCircle, ArrowUpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SkillGapResult } from "@/types";

interface SkillGapPanelProps {
  skillGap: SkillGapResult;
}

const statusConfig = {
  matched: {
    icon: CheckCircle2,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    label: "Matched",
  },
  partial: {
    icon: ArrowUpCircle,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    label: "Level Up",
  },
  gap: {
    icon: AlertCircle,
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
    label: "To Learn",
  },
} as const;

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.05, delayChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.3 } },
};

export function SkillGapPanel({ skillGap }: SkillGapPanelProps) {
  const allSkills = [
    ...skillGap.matched_skills,
    ...skillGap.partial_skills,
    ...skillGap.missing_skills,
  ];

  return (
    <div className="glass-card p-6 md:p-8 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/15">
            <Target className="h-4 w-4 text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Skill Gap Analysis
            </h3>
            <p className="text-xs text-muted-foreground/70 mt-0.5">
              Target: {skillGap.target_role}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold">{skillGap.match_percentage}%</span>
          <p className="text-xs text-muted-foreground">match</p>
        </div>
      </div>

      {/* Match progress bar */}
      <div className="h-2 w-full rounded-full bg-white/[0.06] overflow-hidden">
        <motion.div
          className={cn(
            "h-full rounded-full",
            skillGap.match_percentage >= 70
              ? "bg-gradient-to-r from-emerald-500 to-cyan-500"
              : skillGap.match_percentage >= 40
              ? "bg-gradient-to-r from-amber-500 to-orange-500"
              : "bg-gradient-to-r from-red-500 to-rose-500"
          )}
          initial={{ width: 0 }}
          animate={{ width: `${skillGap.match_percentage}%` }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>

      <p className="text-sm text-muted-foreground">{skillGap.summary}</p>

      {/* Skills list */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        className="space-y-2"
      >
        {allSkills.map((sm) => {
          const config = statusConfig[sm.status as keyof typeof statusConfig] ?? statusConfig.gap;
          const Icon = config.icon;
          return (
            <motion.div
              key={sm.skill}
              variants={item}
              className={cn(
                "flex items-center justify-between px-4 py-2.5 rounded-xl border",
                config.bg,
                config.border
              )}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={cn("h-4 w-4", config.color)} />
                <span className="text-sm font-medium">{sm.skill}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                {sm.proficiency && (
                  <span>
                    {sm.proficiency}
                    {sm.required_level ? ` → ${sm.required_level}` : ""}
                  </span>
                )}
                {!sm.proficiency && sm.required_level && (
                  <span>need {sm.required_level}</span>
                )}
                <span className={cn("font-medium", config.color)}>{config.label}</span>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
