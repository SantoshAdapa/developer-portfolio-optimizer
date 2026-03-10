"use client";

import { motion } from "framer-motion";
import { Zap, AlertTriangle, Rocket, Lightbulb } from "lucide-react";
import type { AiInsights } from "@/types";

interface InsightCalloutsProps {
  strengths: string[];
  weaknesses: string[];
  aiInsights?: AiInsights | null;
}

const cards = [
  {
    key: "strength",
    icon: Zap,
    title: "Key Strength",
    iconBg: "bg-emerald-500/15",
    iconColor: "text-emerald-400",
    borderHover: "hover:border-emerald-500/20",
    getContent: (s: string[], _w: string[]) => s[0] || "No data available",
  },
  {
    key: "improvement",
    icon: AlertTriangle,
    title: "Improvement Opportunity",
    iconBg: "bg-amber-500/15",
    iconColor: "text-amber-400",
    borderHover: "hover:border-amber-500/20",
    getContent: (_s: string[], w: string[]) => w[0] || "No data available",
  },
  {
    key: "potential",
    icon: Rocket,
    title: "Career Potential",
    iconBg: "bg-blue-500/15",
    iconColor: "text-blue-400",
    borderHover: "hover:border-blue-500/20",
    getContent: (s: string[], w: string[]) =>
      s[1] || w[1] || "Continue building your profile for deeper insights",
  },
] as const;

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.1 },
  },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

export function InsightCallouts({ strengths, weaknesses, aiInsights }: InsightCalloutsProps) {
  const careerPotential = aiInsights?.career_potential;
  const improvements = aiInsights?.recommended_improvements ?? [];

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        AI Insights
      </h3>

      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        className="grid gap-4 sm:grid-cols-3"
      >
        {cards.map((card) => (
          <motion.div key={card.key} variants={item}>
            <div
              className={`glass-card-hover p-5 h-full ${card.borderHover}`}
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-xl ${card.iconBg}`}
                >
                  <card.icon className={`h-4 w-4 ${card.iconColor}`} />
                </div>
                <span className="text-sm font-semibold">{card.title}</span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {card.key === "potential" && careerPotential
                  ? careerPotential
                  : card.getContent(strengths, weaknesses)}
              </p>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Recommended Improvements */}
      {improvements.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="glass-card-hover p-5"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/15">
              <Lightbulb className="h-4 w-4 text-indigo-400" />
            </div>
            <span className="text-sm font-semibold">Recommended Improvements</span>
          </div>
          <ul className="space-y-2">
            {improvements.map((imp, i) => (
              <li key={i} className="text-sm text-muted-foreground leading-relaxed flex items-start gap-2">
                <span className="text-indigo-400 mt-0.5 shrink-0">•</span>
                {imp}
              </li>
            ))}
          </ul>
        </motion.div>
      )}
    </div>
  );
}
