"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MarketDemandResult, MarketSkillDemand } from "@/types";

interface MarketDemandPanelProps {
  demand: MarketDemandResult;
}

const trendConfig = {
  rising: { icon: TrendingUp, color: "text-emerald-400", label: "Rising" },
  stable: { icon: Minus, color: "text-blue-400", label: "Stable" },
  declining: { icon: TrendingDown, color: "text-red-400", label: "Declining" },
};

const demandColors = {
  high: "bg-emerald-500/15 text-emerald-300 border-emerald-500/20",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/20",
  low: "bg-zinc-500/15 text-zinc-300 border-zinc-500/20",
};

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.04, delayChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.3 } },
};

function SkillChip({ skill }: { skill: MarketSkillDemand }) {
  const trend = trendConfig[skill.trend] ?? trendConfig.stable;
  const TrendIcon = trend.icon;

  return (
    <motion.div variants={item} className="glass-card-hover px-3 py-2 !rounded-xl">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium">{skill.skill}</span>
        <div className="flex items-center gap-1.5">
          <span
            className={cn(
              "inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium border",
              demandColors[skill.demand_level]
            )}
          >
            {skill.demand_level}
          </span>
          <TrendIcon className={cn("h-3 w-3", trend.color)} />
        </div>
      </div>
    </motion.div>
  );
}

export function MarketDemandPanel({ demand }: MarketDemandPanelProps) {
  return (
    <div className="glass-card p-6 md:p-8 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/15">
            <BarChart2 className="h-4 w-4 text-emerald-400" />
          </div>
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Market Demand
          </h3>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold">{demand.market_readiness}%</span>
          <p className="text-xs text-muted-foreground">readiness</p>
        </div>
      </div>

      <p className="text-sm text-muted-foreground">{demand.summary}</p>

      {demand.high_demand_matches.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-emerald-400/80">
            Your In-Demand Skills
          </h4>
          <motion.div
            variants={container}
            initial="hidden"
            animate="visible"
            className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3"
          >
            {demand.high_demand_matches.map((s) => (
              <SkillChip key={s.skill} skill={s} />
            ))}
          </motion.div>
        </div>
      )}

      {demand.missing_high_demand.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-amber-400/80">
            High-Demand Skills to Learn
          </h4>
          <motion.div
            variants={container}
            initial="hidden"
            animate="visible"
            className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3"
          >
            {demand.missing_high_demand.slice(0, 6).map((s) => (
              <SkillChip key={s.skill} skill={s} />
            ))}
          </motion.div>
        </div>
      )}
    </div>
  );
}
