"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { ChevronDown, Clock, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ProjectIdea as ProjectIdeaType } from "@/types";

interface ProjectIdeasProps {
  ideas: ProjectIdeaType[];
}

const difficultyStyles: Record<string, string> = {
  beginner: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/20",
  intermediate: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/20",
  advanced: "bg-red-500/15 text-red-700 dark:text-red-300 border-red-500/20",
  easy: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/20",
  hard: "bg-red-500/15 text-red-700 dark:text-red-300 border-red-500/20",
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

function ProjectCard({ idea }: { idea: ProjectIdeaType }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="glass-card-hover p-5 h-full">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="text-sm font-semibold">{idea.title}</h4>
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium border shrink-0",
            difficultyStyles[idea.difficulty] || difficultyStyles.beginner
          )}
        >
          {idea.difficulty}
        </span>
      </div>

      <p className="text-sm text-muted-foreground leading-relaxed mb-3">
        {idea.description}
      </p>

      {/* Meta row */}
      <div className="flex items-center gap-4 mb-3 text-xs text-muted-foreground/70">
        {idea.estimated_time && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {idea.estimated_time}
          </span>
        )}
      </div>

      {/* Tech tags */}
      {idea.tech_stack.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {idea.tech_stack.map((tech) => (
            <Badge key={tech} variant="gradient" className="text-[10px]">
              {tech}
            </Badge>
          ))}
        </div>
      )}

      {/* Expandable details */}
      {idea.skills_developed.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            <ChevronDown
              className={cn(
                "h-3 w-3 transition-transform duration-200",
                expanded && "rotate-180"
              )}
            />
            {expanded ? "Hide" : "Show"} skills developed
          </button>

          <AnimatePresence>
            {expanded && (
              <motion.ul
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden mt-2 space-y-1 pl-1"
              >
                {idea.skills_developed.map((outcome, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-xs text-muted-foreground/80"
                  >
                    <span className="mt-1.5 h-1 w-1 rounded-full bg-blue-400/60 shrink-0" />
                    <span>{outcome}</span>
                  </li>
                ))}
              </motion.ul>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
}

export function ProjectIdeas({ ideas }: ProjectIdeasProps) {
  if (!ideas.length) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        Recommended Projects
      </h3>

      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        className="grid gap-4 sm:grid-cols-2"
      >
        {ideas.map((idea, i) => (
          <motion.div key={`${idea.title}-${i}`} variants={item}>
            <ProjectCard idea={idea} />
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
