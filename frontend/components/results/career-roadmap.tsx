"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Check, Circle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { CareerRoadmap, Milestone } from "@/types";

interface CareerRoadmapSectionProps {
  roadmap: CareerRoadmap;
}

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.15 },
  },
};

const item = {
  hidden: { opacity: 0, x: -12 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

function MilestoneCard({
  milestone,
  isLast,
}: {
  milestone: Milestone;
  isLast: boolean;
}) {
  return (
    <motion.div variants={item} className="flex gap-4 relative">
      {/* Timeline connector */}
      <div className="flex flex-col items-center">
        <div
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-full shrink-0 ring-2",
            milestone.completed
              ? "bg-emerald-500/20 ring-emerald-500/40"
              : "bg-white/[0.04] ring-white/[0.1]"
          )}
        >
          {milestone.completed ? (
            <Check className="h-4 w-4 text-emerald-400" />
          ) : (
            <Circle className="h-3 w-3 text-muted-foreground/40" />
          )}
        </div>
        {!isLast && (
          <div
            className={cn(
              "w-[2px] flex-1 min-h-[40px]",
              milestone.completed ? "bg-emerald-500/30" : "bg-white/[0.06]"
            )}
          />
        )}
      </div>

      {/* Content */}
      <div className="pb-8 flex-1">
        <div className="glass-card-hover p-5">
          {/* Header */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <h4 className="text-sm font-semibold">{milestone.title}</h4>
            {milestone.timeframe && (
              <span className="text-[10px] text-muted-foreground/60 font-mono shrink-0">
                {milestone.timeframe}
              </span>
            )}
          </div>

          <p className="text-sm text-muted-foreground leading-relaxed mb-3">
            {milestone.description}
          </p>

          {/* Skills to learn */}
          {milestone.skills_to_learn.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {milestone.skills_to_learn.map((skill) => (
                <Badge key={skill} variant="gradient" className="text-[10px]">
                  {skill}
                </Badge>
              ))}
            </div>
          )}

          {/* Projects to build */}
          {milestone.projects_to_build.length > 0 && (
            <div className="space-y-1 mt-2">
              <p className="text-[10px] text-muted-foreground/50 uppercase tracking-wider font-medium">
                Build
              </p>
              {milestone.projects_to_build.map((proj) => (
                <p
                  key={proj}
                  className="text-xs text-muted-foreground/80 flex items-center gap-1.5"
                >
                  <span className="h-1 w-1 rounded-full bg-violet-400/60 shrink-0" />
                  {proj}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export function CareerRoadmapSection({ roadmap }: CareerRoadmapSectionProps) {
  if (!roadmap.milestones.length) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Career Roadmap
        </h3>
        <div className="flex items-center gap-2 text-xs text-muted-foreground/60">
          <span>{roadmap.current_level}</span>
          <span className="text-blue-400">→</span>
          <span className="text-foreground font-medium">
            {roadmap.target_level}
          </span>
          {roadmap.timeline && (
            <span className="ml-1 text-muted-foreground/40">
              ({roadmap.timeline})
            </span>
          )}
        </div>
      </div>

      <motion.div variants={container} initial="hidden" animate="visible">
        {roadmap.milestones.map((milestone, i) => (
          <MilestoneCard
            key={`${milestone.title}-${i}`}
            milestone={milestone}
            isLast={i === roadmap.milestones.length - 1}
          />
        ))}
      </motion.div>
    </div>
  );
}
