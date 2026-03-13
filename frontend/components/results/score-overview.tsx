"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ScoreMeter } from "@/components/analysis/score-meter";
import type { DeveloperScore } from "@/types";

interface ScoreOverviewProps {
  score: DeveloperScore;
}

const barColors: Record<string, string> = {
  "resume completeness": "from-blue-500 to-cyan-400",
  "content quality": "from-teal-500 to-emerald-400",
  "skill diversity": "from-violet-500 to-purple-400",
  "formatting quality": "from-fuchsia-500 to-pink-400",
  "impact quantification": "from-orange-500 to-amber-400",
  "keyword density": "from-lime-500 to-green-400",
  "github activity": "from-emerald-500 to-green-400",
  "repo quality": "from-amber-500 to-yellow-400",
  documentation: "from-pink-500 to-rose-400",
  community: "from-indigo-500 to-blue-400",
  "technology depth": "from-cyan-500 to-teal-400",
};

function getBarGradient(name: string): string {
  const key = name.toLowerCase();
  for (const [k, v] of Object.entries(barColors)) {
    if (key.includes(k)) return v;
  }
  return "from-blue-500 to-violet-500";
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.3 },
  },
};

const barVariant = {
  hidden: { opacity: 0, x: -12 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

export function ScoreOverview({ score }: ScoreOverviewProps) {
  return (
    <div className="glass-card p-6 md:p-8">
      <div className="flex flex-col md:flex-row items-center gap-8 md:gap-12">
        {/* Radial score */}
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="shrink-0"
        >
          <ScoreMeter score={score.overall} size={200} strokeWidth={12} />
        </motion.div>

        {/* Category bars */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="flex-1 w-full space-y-4"
        >
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
            Score Breakdown
          </h3>

          {Object.entries(score.categories).map(([name, value]) => {
            const displayName = name.replace(/_/g, " ");
            const gradient = getBarGradient(displayName);

            return (
              <motion.div key={name} variants={barVariant} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium capitalize">{displayName}</span>
                  <span className="text-muted-foreground tabular-nums">
                    {value}/100
                  </span>
                </div>
                <div className="h-2.5 w-full rounded-full overflow-hidden" style={{ background: "var(--bar-track)" }}>
                  <motion.div
                    className={cn(
                      "h-full rounded-full bg-gradient-to-r",
                      gradient
                    )}
                    initial={{ width: 0 }}
                    animate={{ width: `${value}%` }}
                    transition={{
                      duration: 1.2,
                      ease: [0.22, 1, 0.36, 1],
                      delay: 0.4,
                    }}
                  />
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </div>
  );
}
