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
import { useTheme } from "@/lib/theme-provider";
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
  ml_ai: "ML / AI",
  testing: "Testing",
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
  const { theme } = useTheme();
  const isDark = theme === "dark";

  useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const formatted = data.map((d) => ({
    ...d,
    value: normalize(d.value),
    label: formatLabel(d.dimension),
  }));

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
            stroke={isDark ? "rgba(255,255,255,0.08)" : "rgba(100,116,139,0.2)"}
            strokeDasharray="3 3"
          />
          <PolarAngleAxis
            dataKey="label"
            tick={{ fill: isDark ? "rgba(255,255,255,0.6)" : "rgba(51,65,85,0.8)", fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fill: isDark ? "rgba(255,255,255,0.3)" : "rgba(100,116,139,0.5)", fontSize: 10 }}
            axisLine={false}
          />

          <Radar
            name="You"
            dataKey="value"
            stroke="rgba(139,92,246,1)"
            fill="rgba(139,92,246,0.25)"
            fillOpacity={isDark ? 0.4 : 0.35}
            strokeWidth={2}
            animationDuration={1200}
            animationEasing="ease-out"
          />

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
              backgroundColor: isDark ? "rgba(15,23,42,0.9)" : "rgba(255,255,255,0.95)",
              border: `1px solid ${isDark ? "rgba(255,255,255,0.1)" : "rgba(100,116,139,0.2)"}`,
              borderRadius: "0.75rem",
              backdropFilter: "blur(12px)",
              padding: "8px 12px",
              fontSize: "13px",
            }}
            labelStyle={{ color: isDark ? "rgba(255,255,255,0.8)" : "rgba(30,41,59,0.9)", fontWeight: 600 }}
            itemStyle={{ color: isDark ? "rgba(255,255,255,0.6)" : "rgba(71,85,105,0.8)" }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
