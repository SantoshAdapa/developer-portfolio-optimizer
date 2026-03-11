"use client";

import { motion } from "framer-motion";
import { Layers, Code, Rocket, BarChart3, Boxes } from "lucide-react";
import type { PortfolioDepthScore } from "@/types";

interface PortfolioDepthProps {
  depth: PortfolioDepthScore;
}

const metrics = [
  { key: "technology_diversity", label: "Tech Diversity", icon: Code, color: "text-cyan-400" },
  { key: "complexity_score", label: "Complexity", icon: Layers, color: "text-violet-400" },
  { key: "deployment_signals", label: "Deployment", icon: Rocket, color: "text-emerald-400" },
  { key: "project_type_balance", label: "Project Variety", icon: Boxes, color: "text-amber-400" },
] as const;

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export function PortfolioDepth({ depth }: PortfolioDepthProps) {
  return (
    <div className="glass-card p-6 md:p-8 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-500/15">
            <BarChart3 className="h-4 w-4 text-violet-400" />
          </div>
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Portfolio Depth
          </h3>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold">{depth.overall}</span>
          <span className="text-sm text-muted-foreground">/100</span>
        </div>
      </div>

      <p className="text-sm text-muted-foreground">{depth.summary}</p>

      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        className="grid gap-3 sm:grid-cols-2"
      >
        {metrics.map((m) => {
          const val = depth[m.key];
          return (
            <motion.div
              key={m.key}
              variants={item}
              className="glass-card-hover px-4 py-3 !rounded-xl"
            >
              <div className="flex items-center gap-2 mb-2">
                <m.icon className={`h-3.5 w-3.5 ${m.color}`} />
                <span className="text-xs font-medium text-muted-foreground">{m.label}</span>
                <span className="ml-auto text-sm font-semibold">{val}</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${val}%` }}
                  transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
                />
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
