"use client";

import { motion } from "framer-motion";
import { ShieldCheck, Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useEffect, useState } from "react";

interface ConfidenceMeterProps {
  /** 0–100 */
  confidence: number;
}

function getConfidenceLabel(c: number): string {
  if (c >= 90) return "Very High";
  if (c >= 75) return "High";
  if (c >= 55) return "Moderate";
  if (c >= 35) return "Low";
  return "Very Low";
}

function getConfidenceColor(c: number): string {
  if (c >= 75) return "from-emerald-500 to-green-400";
  if (c >= 55) return "from-amber-500 to-yellow-400";
  return "from-red-500 to-orange-400";
}

export function ConfidenceMeter({ confidence }: ConfidenceMeterProps) {
  const [displayVal, setDisplayVal] = useState(0);

  useEffect(() => {
    const duration = 1200;
    const start = performance.now();

    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayVal(Math.round(eased * confidence));
      if (progress < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
  }, [confidence]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="glass-card p-5 md:p-6"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span className="text-sm font-semibold">AI Confidence</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold tabular-nums">{displayVal}%</span>
          <span className="text-xs text-muted-foreground">
            {getConfidenceLabel(confidence)}
          </span>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button className="text-muted-foreground/50 hover:text-muted-foreground transition-colors">
                  <Info className="h-3.5 w-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-[260px] text-xs leading-relaxed">
                Confidence is computed based on the amount of data available —
                resume detail, GitHub activity level, and repository quality
                signals. More data leads to higher confidence.
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Bar */}
      <div className="h-2.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${getConfidenceColor(confidence)}`}
          initial={{ width: 0 }}
          animate={{ width: `${confidence}%` }}
          transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
        />
      </div>
    </motion.div>
  );
}
