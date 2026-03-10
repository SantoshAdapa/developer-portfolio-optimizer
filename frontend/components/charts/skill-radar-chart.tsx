"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { RadarDataPoint } from "@/types";

interface SkillRadarChartProps {
  data: RadarDataPoint[];
  /** Optional second dataset for comparison overlay */
  comparisonData?: RadarDataPoint[];
  height?: number;
}

const DIMENSION_LABELS: Record<string, string> = {
  resume_completeness: "Resume",
  skill_diversity: "Skills",
  github_activity: "GitHub",
  repo_quality: "Repo Quality",
  documentation: "Docs",
  community: "Community",
  backend: "Backend",
  frontend: "Frontend",
  devops: "DevOps",
  data: "Data",
  machine_learning: "ML / AI",
};

function formatLabel(dimension: string): string {
  return DIMENSION_LABELS[dimension] || dimension.replace(/_/g, " ");
}

function normalize(value: number): number {
  return Math.min(100, Math.max(0, value));
}

export function SkillRadarChart({
  data,
  comparisonData,
  height = 320,
}: SkillRadarChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Delay render by a tick so the animation plays nicely
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const formatted = data.map((d) => ({
    ...d,
    value: normalize(d.value),
    label: formatLabel(d.dimension),
  }));

  // Merge comparison data onto the same records if provided
  const merged = comparisonData
    ? formatted.map((d) => {
        const match = comparisonData.find((c) => c.dimension === d.dimension);
        return { ...d, comparison: normalize(match?.value ?? 0) };
      })
    : formatted;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={mounted ? { opacity: 1, scale: 1 } : {}}
      transition={{ duration: 0.7, ease: "easeOut" }}
      className="glass-card p-4 md:p-6"
    >
      <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
        Skill Distribution
      </h4>
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={merged}>
          <PolarGrid
            stroke="rgba(255,255,255,0.08)"
            strokeDasharray="3 3"
          />
          <PolarAngleAxis
            dataKey="label"
            tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
            axisLine={false}
          />

          {/* Primary radar area */}
          <Radar
            name="You"
            dataKey="value"
            stroke="rgba(139,92,246,1)"
            fill="rgba(139,92,246,0.25)"
            fillOpacity={0.4}
            strokeWidth={2}
            animationDuration={1200}
            animationEasing="ease-out"
          />

          {/* Comparison overlay */}
          {comparisonData && (
            <Radar
              name="Comparison"
              dataKey="comparison"
              stroke="rgba(59,130,246,0.8)"
              fill="rgba(59,130,246,0.15)"
              fillOpacity={0.3}
              strokeWidth={2}
              strokeDasharray="4 4"
              animationDuration={1200}
              animationEasing="ease-out"
            />
          )}

          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(15,23,42,0.9)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "0.75rem",
              backdropFilter: "blur(12px)",
              padding: "8px 12px",
              fontSize: "13px",
            }}
            labelStyle={{ color: "rgba(255,255,255,0.8)", fontWeight: 600 }}
            itemStyle={{ color: "rgba(255,255,255,0.6)" }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
