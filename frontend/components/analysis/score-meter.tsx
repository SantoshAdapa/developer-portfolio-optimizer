"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ScoreMeterProps {
  score: number; // 0–100
  label?: string;
  size?: number;
  strokeWidth?: number;
  className?: string;
  animate?: boolean;
}

export function ScoreMeter({
  score,
  label = "Developer Score",
  size = 180,
  strokeWidth = 10,
  className,
  animate = true,
}: ScoreMeterProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  // Animated counter
  const [displayScore, setDisplayScore] = useState(animate ? 0 : score);

  useEffect(() => {
    if (!animate) {
      setDisplayScore(score);
      return;
    }

    let start = 0;
    const duration = 1400;
    const startTime = performance.now();

    const tick = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * score);
      setDisplayScore(current);
      if (progress < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
  }, [score, animate]);

  // Color based on score tier
  const getGradientId = "score-gradient";

  return (
    <div className={cn("flex flex-col items-center gap-4", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="-rotate-90"
        >
          <defs>
            <linearGradient
              id={getGradientId}
              x1="0%"
              y1="0%"
              x2="100%"
              y2="100%"
            >
              <stop offset="0%" stopColor="hsl(217, 91%, 60%)" />
              <stop offset="50%" stopColor="hsl(271, 91%, 65%)" />
              <stop offset="100%" stopColor="hsl(295, 91%, 60%)" />
            </linearGradient>
          </defs>

          {/* Background ring */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth={strokeWidth}
            opacity={0.3}
          />

          {/* Progress ring */}
          <motion.circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={`url(#${getGradientId})`}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{
              strokeDashoffset:
                circumference - (circumference * score) / 100,
            }}
            transition={{
              duration: animate ? 1.6 : 0,
              ease: [0.22, 1, 0.36, 1],
            }}
          />
        </svg>

        {/* Center score display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            key={displayScore}
            className="text-4xl font-bold tabular-nums tracking-tighter"
          >
            {displayScore}
          </motion.span>
          <span className="text-xs text-muted-foreground mt-0.5">/ 100</span>
        </div>

        {/* Glow effect */}
        <div
          className="absolute inset-0 rounded-full opacity-20 blur-xl pointer-events-none"
          style={{
            background: `conic-gradient(from 0deg, hsl(217 91% 60% / 0.3), hsl(271 91% 65% / 0.3), transparent 70%)`,
          }}
        />
      </div>

      <span className="text-sm font-medium text-muted-foreground">
        {label}
      </span>
    </div>
  );
}
