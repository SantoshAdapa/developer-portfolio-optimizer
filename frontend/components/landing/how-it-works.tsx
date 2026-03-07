"use client";

import { motion } from "framer-motion";
import {
  FileUp,
  GitBranch,
  BrainCircuit,
  BarChart3,
  Lightbulb,
  Route,
} from "lucide-react";

const steps = [
  {
    icon: FileUp,
    title: "Upload Your Resume",
    description:
      "Drop your resume and we extract skills, experience, and project history using AI.",
    color: "from-blue-500 to-cyan-500",
    shadowColor: "shadow-blue-500/20",
  },
  {
    icon: GitBranch,
    title: "Connect GitHub",
    description:
      "We analyze your repositories, languages, contributions, and open-source activity.",
    color: "from-violet-500 to-purple-500",
    shadowColor: "shadow-violet-500/20",
  },
  {
    icon: BrainCircuit,
    title: "AI Analysis",
    description:
      "Our AI cross-references your profile against industry standards and market demands.",
    color: "from-pink-500 to-rose-500",
    shadowColor: "shadow-pink-500/20",
  },
  {
    icon: BarChart3,
    title: "Developer Score",
    description:
      "Get a comprehensive score across multiple dimensions — skills, projects, and impact.",
    color: "from-amber-500 to-orange-500",
    shadowColor: "shadow-amber-500/20",
  },
  {
    icon: Lightbulb,
    title: "Smart Recommendations",
    description:
      "Receive personalized portfolio improvements and project ideas tailored to your goals.",
    color: "from-emerald-500 to-green-500",
    shadowColor: "shadow-emerald-500/20",
  },
  {
    icon: Route,
    title: "Career Roadmap",
    description:
      "Get a step-by-step plan with milestones, resources, and timelines to level up.",
    color: "from-blue-500 to-violet-500",
    shadowColor: "shadow-blue-500/20",
  },
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 },
  },
};

const item = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

export function HowItWorks() {
  return (
    <section className="relative py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            How It <span className="gradient-text">Works</span>
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
            From resume to roadmap in three simple steps — our AI handles the
            heavy lifting.
          </p>
        </motion.div>

        {/* Steps grid */}
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-50px" }}
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
        >
          {steps.map((step, i) => (
            <motion.div
              key={step.title}
              variants={item}
              className="group relative"
            >
              <div className="glass-card-hover p-6 h-full">
                {/* Step number */}
                <div className="absolute top-4 right-4 text-xs font-mono text-muted-foreground/40">
                  {String(i + 1).padStart(2, "0")}
                </div>

                {/* Icon */}
                <div
                  className={`inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${step.color} shadow-lg ${step.shadowColor} mb-4`}
                >
                  <step.icon className="h-5 w-5 text-white" />
                </div>

                {/* Content */}
                <h3 className="text-base font-semibold mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
