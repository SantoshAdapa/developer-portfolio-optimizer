"use client";

import { motion } from "framer-motion";
import { Compass, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CareerDirectionResult } from "@/types";

interface CareerDirectionPanelProps {
  direction: CareerDirectionResult;
}

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export function CareerDirectionPanel({ direction }: CareerDirectionPanelProps) {
  const topPaths = direction.career_paths.slice(0, 4);

  return (
    <div className="glass-card p-6 md:p-8 space-y-5">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-500/15">
          <Compass className="h-4 w-4 text-rose-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Career Direction
          </h3>
          <p className="text-xs text-muted-foreground/70 mt-0.5">
            Best fit: {direction.primary_direction}
          </p>
        </div>
      </div>

      <p className="text-sm text-muted-foreground">{direction.summary}</p>

      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        className="space-y-3"
      >
        {topPaths.map((path, i) => (
          <motion.div
            key={path.role}
            variants={item}
            className={cn(
              "glass-card-hover p-4 !rounded-xl",
              i === 0 && "ring-1 ring-violet-500/20"
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                {i === 0 && (
                  <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-[10px] font-bold text-violet-400">
                    TOP MATCH
                  </span>
                )}
                <span className="text-sm font-semibold">{path.role}</span>
              </div>
              <span className="text-sm font-bold">{path.fit_score}%</span>
            </div>

            <p className="text-xs text-muted-foreground mb-3">{path.description}</p>

            {path.matching_skills.length > 0 && (
              <div className="mb-2">
                <p className="text-[10px] text-emerald-400/80 font-medium mb-1">Matching Skills</p>
                <div className="flex flex-wrap gap-1">
                  {path.matching_skills.map((s) => (
                    <span
                      key={s}
                      className="rounded-md bg-emerald-500/10 px-1.5 py-0.5 text-[10px] text-emerald-300 border border-emerald-500/20"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {path.skills_to_develop.length > 0 && (
              <div>
                <p className="text-[10px] text-amber-400/80 font-medium mb-1">To Develop</p>
                <div className="flex flex-wrap gap-1">
                  {path.skills_to_develop.map((s) => (
                    <span
                      key={s}
                      className="flex items-center gap-0.5 rounded-md bg-amber-500/10 px-1.5 py-0.5 text-[10px] text-amber-300 border border-amber-500/20"
                    >
                      <ChevronRight className="h-2 w-2" />
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
