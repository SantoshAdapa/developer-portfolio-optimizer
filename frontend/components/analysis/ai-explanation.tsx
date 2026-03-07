"use client";

import { motion } from "framer-motion";
import {
  Zap,
  TrendingUp,
  Target,
  Lightbulb,
  AlertCircle,
  Compass,
} from "lucide-react";
import type { DeveloperScore, SkillAnalysis, GitHubInsights } from "@/types";

interface AiExplanationProps {
  score: DeveloperScore;
  skills: SkillAnalysis;
  github: GitHubInsights | null;
}

interface InsightItem {
  icon: typeof Zap;
  iconBg: string;
  iconColor: string;
  label: string;
  text: string;
}

function deriveStrengths(
  score: DeveloperScore,
  skills: SkillAnalysis,
  github: GitHubInsights | null
): InsightItem[] {
  const items: InsightItem[] = [];

  // Strength 1 — highest scoring category
  const sorted = [...score.categories].sort((a, b) => b.score - a.score);
  if (sorted.length > 0) {
    items.push({
      icon: Zap,
      iconBg: "bg-emerald-500/15",
      iconColor: "text-emerald-400",
      label: "Top Dimension",
      text: `Your strongest area is ${sorted[0].name} (${sorted[0].score}/${sorted[0].max_score}), placing you well above average in this dimension.`,
    });
  }

  // Strength 2 — technical skill breadth
  const techCount = skills.technical_skills.length;
  if (techCount > 0) {
    const advancedCount = skills.technical_skills.filter(
      (s) => s.level === "advanced" || s.level === "expert"
    ).length;
    items.push({
      icon: Lightbulb,
      iconBg: "bg-blue-500/15",
      iconColor: "text-blue-400",
      label: "Skill Breadth",
      text: `You demonstrate ${techCount} technical skills with ${advancedCount} at advanced level or above — a strong indicator of engineering depth.`,
    });
  }

  // Strength 3 — GitHub collaboration
  if (github && github.collaboration_score > 50) {
    items.push({
      icon: TrendingUp,
      iconBg: "bg-violet-500/15",
      iconColor: "text-violet-400",
      label: "Collaboration",
      text: `Your collaboration score of ${github.collaboration_score} signals active community participation across ${github.top_languages.slice(0, 3).join(", ") || "multiple languages"}.`,
    });
  } else {
    items.push({
      icon: TrendingUp,
      iconBg: "bg-violet-500/15",
      iconColor: "text-violet-400",
      label: "Overall Performance",
      text: `With an overall score of ${score.overall}/100 you're demonstrating solid developer fundamentals across multiple evaluation dimensions.`,
    });
  }

  return items.slice(0, 3);
}

function deriveImprovements(
  score: DeveloperScore,
  skills: SkillAnalysis
): InsightItem[] {
  const items: InsightItem[] = [];

  // Improvement 1 — lowest scoring category
  const sorted = [...score.categories].sort((a, b) => a.score - b.score);
  if (sorted.length > 0) {
    items.push({
      icon: AlertCircle,
      iconBg: "bg-amber-500/15",
      iconColor: "text-amber-400",
      label: "Growth Area",
      text: `${sorted[0].name} scored ${sorted[0].score}/${sorted[0].max_score}. Focusing here could raise your overall score the most.`,
    });
  }

  // Improvement 2 — missing skills
  if (skills.missing_skills.length > 0) {
    const top3 = skills.missing_skills.slice(0, 3).map((s) => s.name);
    items.push({
      icon: Target,
      iconBg: "bg-rose-500/15",
      iconColor: "text-rose-400",
      label: "Skill Gaps",
      text: `Consider adding ${top3.join(", ")} to strengthen your portfolio and unlock new career paths.`,
    });
  } else {
    items.push({
      icon: Target,
      iconBg: "bg-rose-500/15",
      iconColor: "text-rose-400",
      label: "Portfolio Depth",
      text: "Adding more project variety and documentation would strengthen your overall profile visibility.",
    });
  }

  return items.slice(0, 2);
}

function deriveCareerSuggestion(
  score: DeveloperScore,
  skills: SkillAnalysis
): InsightItem {
  const techSkills = skills.technical_skills.map((s) => s.category.toLowerCase());
  const hasML = techSkills.some((c) => c.includes("data") || c.includes("ml"));
  const hasCloud = techSkills.some((c) => c.includes("cloud") || c.includes("devops"));

  let text: string;
  if (score.overall >= 75) {
    text = hasML
      ? "Your profile is strong for ML Engineer or Data Engineering leadership roles. Consider publishing research or open-source ML tools."
      : "You're well-positioned for Senior / Staff-level roles. Consider mentoring, leading architecture decisions, or speaking at conferences.";
  } else if (score.overall >= 50) {
    text = hasCloud
      ? "Growing your cloud certifications and infrastructure-as-code experience could fast-track a DevOps or Platform Engineer career."
      : "Focus on deepening one specialty area and building 2-3 showcase projects to make the jump to senior-level roles.";
  } else {
    text =
      "Build a strong foundation by contributing to open-source projects, completing structured courses, and publishing small personal projects.";
  }

  return {
    icon: Compass,
    iconBg: "bg-indigo-500/15",
    iconColor: "text-indigo-400",
    label: "Career Suggestion",
    text,
  };
}

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.15 },
  },
};

const item = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

export function AiExplanation({ score, skills, github }: AiExplanationProps) {
  const strengths = deriveStrengths(score, skills, github);
  const improvements = deriveImprovements(score, skills);
  const career = deriveCareerSuggestion(score, skills);

  const sections: { heading: string; items: InsightItem[] }[] = [
    { heading: "Strengths", items: strengths },
    { heading: "Improvement Opportunities", items: improvements },
    { heading: "Career Direction", items: [career] },
  ];

  return (
    <div className="glass-card p-6 md:p-8 space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-bold tracking-tight">
          AI <span className="gradient-text">Score Explanation</span>
        </h3>
        <p className="text-xs text-muted-foreground mt-1">
          Why the AI rated your portfolio {score.overall}/100
        </p>
      </div>

      <motion.div variants={container} initial="hidden" animate="visible" className="space-y-5">
        {sections.map((section) => (
          <div key={section.heading} className="space-y-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
              {section.heading}
            </p>
            {section.items.map((entry) => (
              <motion.div
                key={entry.label}
                variants={item}
                className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04] transition-colors duration-200"
              >
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${entry.iconBg}`}
                >
                  <entry.icon className={`h-4 w-4 ${entry.iconColor}`} />
                </div>
                <div>
                  <p className="text-sm font-semibold mb-0.5">{entry.label}</p>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {entry.text}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        ))}
      </motion.div>
    </div>
  );
}
