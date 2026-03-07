"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ArrowUpRight, ChevronRight } from "lucide-react";
import type { PortfolioSuggestion } from "@/types";

interface SuggestionsPanelProps {
  suggestions: PortfolioSuggestion[];
}

const priorityStyles: Record<string, { badge: string; bar: string }> = {
  high: {
    badge: "bg-red-500/15 text-red-300 border-red-500/20",
    bar: "bg-red-500",
  },
  medium: {
    badge: "bg-amber-500/15 text-amber-300 border-amber-500/20",
    bar: "bg-amber-500",
  },
  low: {
    badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/20",
    bar: "bg-emerald-500",
  },
};

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.1 },
  },
};

const item = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

export function SuggestionsPanel({ suggestions }: SuggestionsPanelProps) {
  if (!suggestions.length) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        Portfolio Improvements
      </h3>

      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        className="grid gap-4 sm:grid-cols-2"
      >
        {suggestions.map((s, i) => {
          const style = priorityStyles[s.priority] || priorityStyles.medium;

          return (
            <motion.div
              key={`${s.title}-${i}`}
              variants={item}
              className="group"
            >
              <div className="glass-card-hover p-5 h-full relative overflow-hidden">
                {/* Priority bar accent */}
                <div
                  className={cn(
                    "absolute top-0 left-0 w-1 h-full rounded-l-2xl",
                    style.bar
                  )}
                />

                <div className="flex items-start justify-between gap-2 mb-2">
                  <h4 className="text-sm font-semibold">{s.title}</h4>
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium border shrink-0",
                      style.badge
                    )}
                  >
                    {s.priority}
                  </span>
                </div>

                <p className="text-sm text-muted-foreground leading-relaxed mb-3">
                  {s.description}
                </p>

                {s.action_items.length > 0 && (
                  <ul className="space-y-1.5">
                    {s.action_items.map((action, j) => (
                      <li
                        key={j}
                        className="flex items-start gap-2 text-xs text-muted-foreground/80"
                      >
                        <ChevronRight className="h-3 w-3 mt-0.5 shrink-0 text-blue-400/60" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
