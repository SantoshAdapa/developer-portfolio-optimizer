"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { Skill, ProgrammingLanguageScore } from "@/types";

interface SkillAnalysisProps {
  skills: Skill[];
  programmingLanguages?: ProgrammingLanguageScore[];
}

const levelColors: Record<string, string> = {
  beginner: "bg-zinc-500/20 text-zinc-300 border-zinc-500/20",
  intermediate: "bg-blue-500/20 text-blue-300 border-blue-500/20",
  advanced: "bg-violet-500/20 text-violet-300 border-violet-500/20",
};

const categoryColors: Record<string, string> = {
  frontend: "bg-cyan-500/15 text-cyan-300 border-cyan-500/20",
  backend: "bg-amber-500/15 text-amber-300 border-amber-500/20",
  devops: "bg-orange-500/15 text-orange-300 border-orange-500/20",
  database: "bg-green-500/15 text-green-300 border-green-500/20",
  mobile: "bg-pink-500/15 text-pink-300 border-pink-500/20",
  ai: "bg-purple-500/15 text-purple-300 border-purple-500/20",
  "machine learning": "bg-purple-500/15 text-purple-300 border-purple-500/20",
  cloud: "bg-sky-500/15 text-sky-300 border-sky-500/20",
  testing: "bg-rose-500/15 text-rose-300 border-rose-500/20",
  security: "bg-red-500/15 text-red-300 border-red-500/20",
};

function getCategoryColor(cat: string): string {
  const key = cat.toLowerCase();
  for (const [k, v] of Object.entries(categoryColors)) {
    if (key.includes(k)) return v;
  }
  return "bg-white/10 text-white/70 border-white/10";
}

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.15 },
  },
};

const item = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.35 } },
};

export function SkillAnalysis({ skills, programmingLanguages }: SkillAnalysisProps) {
  const technicalSkills = skills.filter((s) => s.category !== "soft_skill");
  const softSkills = skills.filter((s) => s.category === "soft_skill");

  const sections = [
    { title: "Technical Skills", data: technicalSkills },
    { title: "Soft Skills", data: softSkills },
  ];

  return (
    <div className="glass-card p-6 md:p-8 space-y-6">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        Skill Analysis
      </h3>

      {/* Programming Languages Section */}
      {programmingLanguages && programmingLanguages.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-medium text-muted-foreground/70">
            Programming Languages
          </h4>
          <motion.div
            variants={container}
            initial="hidden"
            animate="visible"
            className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
          >
            {programmingLanguages.map((lang) => (
              <motion.div
                key={lang.name}
                variants={item}
                className="glass-card-hover px-4 py-3 !rounded-xl"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold">{lang.name}</span>
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium border",
                      levelColors[lang.proficiency] || levelColors.beginner
                    )}
                  >
                    {lang.proficiency}
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-blue-500 to-violet-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.round(lang.confidence * 100)}%` }}
                    transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
                  />
                </div>
                <p className="text-[10px] text-muted-foreground mt-1">
                  {Math.round(lang.confidence * 100)}% confidence
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      )}

      {sections.map(
        (section) =>
          section.data.length > 0 && (
            <div key={section.title} className="space-y-3">
              <h4 className="text-xs font-medium text-muted-foreground/70">
                {section.title}
              </h4>
              <motion.div
                variants={container}
                initial="hidden"
                animate="visible"
                className="flex flex-wrap gap-2"
              >
                {section.data.map((skill) => (
                  <motion.div
                    key={`${section.title}-${skill.name}`}
                    variants={item}
                    className="group"
                  >
                    <div className="glass-card-hover px-3 py-2 flex items-center gap-2 !rounded-xl">
                      <span className="text-sm font-medium">{skill.name}</span>
                      <span
                        className={cn(
                          "inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium border",
                          levelColors[skill.proficiency] || levelColors.beginner
                        )}
                      >
                        {skill.proficiency}
                      </span>
                      {skill.category && (
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium border",
                            getCategoryColor(skill.category)
                          )}
                        >
                          {skill.category}
                        </span>
                      )}
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          )
      )}
    </div>
  );
}
