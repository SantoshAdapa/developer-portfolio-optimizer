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
import type { DeveloperScore, Skill, GitHubSummary } from "@/types";

interface AiExplanationProps {
  score: DeveloperScore;
  skills: Skill[];
  github: GitHubSummary | null;
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
  skills: Skill[],
  github: GitHubSummary | null
): InsightItem[] {
  const items: InsightItem[] = [];

  // Strength 1 — highest scoring category
  const sorted = Object.entries(score.categories).sort(([, a], [, b]) => b - a);
  if (sorted.length > 0) {
    const [name, value] = sorted[0];
    items.push({
      icon: Zap,
      iconBg: "bg-emerald-500/15",
      iconColor: "text-emerald-400",
      label: "Top Dimension",
      text: `Your strongest area is ${name.replace(/_/g, " ")} (${value}/100), placing you well above average in this dimension.`,
    });
  }

  // Strength 2 — technical skill breadth
  const techSkills = skills.filter((s) => s.category !== "soft_skill");
  if (techSkills.length > 0) {
    const advancedCount = techSkills.filter(
      (s) => s.proficiency === "advanced"
    ).length;
    items.push({
      icon: Lightbulb,
      iconBg: "bg-blue-500/15",
      iconColor: "text-blue-400",
      label: "Skill Breadth",
      text: `You demonstrate ${techSkills.length} technical skills with ${advancedCount} at advanced level — a strong indicator of engineering depth.`,
    });
  }

  // Strength 3 — GitHub presence
  if (github && github.total_stars > 10) {
    const langs = Object.keys(github.top_languages).slice(0, 3).join(", ");
    items.push({
      icon: TrendingUp,
      iconBg: "bg-violet-500/15",
      iconColor: "text-violet-400",
      label: "Collaboration",
      text: `Your ${github.total_stars} total stars and ${github.followers} followers signal active community participation across ${langs || "multiple languages"}.`,
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
  skills: Skill[]
): InsightItem[] {
  const items: InsightItem[] = [];

  // Improvement 1 — lowest scoring category
  const sorted = Object.entries(score.categories).sort(([, a], [, b]) => a - b);
  if (sorted.length > 0) {
    const [name, value] = sorted[0];
    items.push({
      icon: AlertCircle,
      iconBg: "bg-amber-500/15",
      iconColor: "text-amber-400",
      label: "Growth Area",
      text: `${name.replace(/_/g, " ")} scored ${value}/100. Focusing here could raise your overall score the most.`,
    });
  }

  // Improvement 2 — beginner-level skills
  const beginnerSkills = skills.filter((s) => s.proficiency === "beginner");
  if (beginnerSkills.length > 0) {
    const top3 = beginnerSkills.slice(0, 3).map((s) => s.name);
    items.push({
      icon: Target,
      iconBg: "bg-rose-500/15",
      iconColor: "text-rose-400",
      label: "Skill Gaps",
      text: `Consider leveling up ${top3.join(", ")} to strengthen your portfolio and unlock new career paths.`,
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
  skills: Skill[]
): InsightItem {
  const techCategories = skills.filter((s) => s.category !== "soft_skill").map((s) => s.category);
  const hasML = techCategories.some((c) => c === "database" || c === "tool");
  const hasCloud = techCategories.some((c) => c === "cloud");

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
                className="flex items-start gap-3 p-3 rounded-xl bg-foreground/[0.02] border border-foreground/[0.06] hover:bg-foreground/[0.04] transition-colors duration-200"
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
