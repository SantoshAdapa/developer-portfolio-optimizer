"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles, Github, FileText, Play } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { MagneticButton } from "@/components/ui/magnetic-button";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.1 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
};

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      {/* Hero-specific gradient orbs */}
      <div className="absolute inset-0 -z-10">
        <motion.div
          animate={{ scale: [1, 1.1, 1], opacity: [0.12, 0.18, 0.12] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-[10%] left-[15%] h-[500px] w-[500px] rounded-full bg-blue-500/15 blur-[100px]"
        />
        <motion.div
          animate={{ scale: [1, 1.15, 1], opacity: [0.1, 0.15, 0.1] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          className="absolute top-[20%] right-[10%] h-[400px] w-[400px] rounded-full bg-violet-500/15 blur-[100px]"
        />
        <motion.div
          animate={{ scale: [1, 1.08, 1], opacity: [0.08, 0.12, 0.08] }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          className="absolute bottom-[10%] left-[40%] h-[350px] w-[350px] rounded-full bg-indigo-500/10 blur-[100px]"
        />
      </div>

      <div className="mx-auto max-w-7xl px-6 py-24 md:py-32 lg:py-40">
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="flex flex-col items-center text-center"
        >
          {/* Badge */}
          <motion.div variants={item}>
            <div className="inline-flex items-center gap-2 rounded-full border border-foreground/[0.08] bg-foreground/[0.03] px-4 py-1.5 text-sm text-muted-foreground backdrop-blur-xl mb-8">
              <Sparkles className="h-3.5 w-3.5 text-violet-400" />
              <span>Powered by AI</span>
              <span className="h-1 w-1 rounded-full bg-violet-400" />
              <span className="text-violet-400">Free to use</span>
            </div>
          </motion.div>

          {/* Heading */}
          <motion.h1
            variants={item}
            className="max-w-4xl text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl"
          >
            <span className="block text-foreground">Optimize Your</span>
            <span className="block gradient-text mt-1">Developer Portfolio</span>
          </motion.h1>

          {/* Tagline */}
          <motion.p
            variants={item}
            className="mt-6 max-w-2xl text-lg text-muted-foreground md:text-xl leading-relaxed"
          >
            AI that analyzes your developer profile and tells you exactly how to
            level up
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            variants={item}
            className="mt-10 flex flex-col sm:flex-row items-center gap-4"
          >
            <MagneticButton>
              <Button variant="gradient" size="xl" asChild>
                <Link href="/analyze" className="gap-2">
                  <FileText className="h-5 w-5" />
                  Upload Resume
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </MagneticButton>
            <MagneticButton>
              <Button variant="glass" size="xl" asChild>
                <Link href="/analyze" className="gap-2">
                  <Github className="h-5 w-5" />
                  Analyze GitHub
                </Link>
              </Button>
            </MagneticButton>
            <MagneticButton>
              <Button variant="glass" size="xl" asChild>
                <Link href="/analyze?demo=true" className="gap-2">
                  <Play className="h-5 w-5 text-emerald-400" />
                  Try Demo
                </Link>
              </Button>
            </MagneticButton>
          </motion.div>

          {/* Social proof */}
          <motion.p
            variants={item}
            className="mt-8 text-sm text-muted-foreground/60"
          >
            No sign-up required &middot; Results in under 60 seconds
          </motion.p>
        </motion.div>
      </div>
    </section>
  );
}
