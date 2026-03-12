"use client";

import { Suspense, useState, useCallback, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, ArrowRight, FileText, Github, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FileUploader } from "@/components/upload/file-uploader";
import { GitHubInput } from "@/components/upload/github-input";
import { AnalysisPanel } from "@/components/analysis/analysis-panel";
import { useTimelineProgress } from "@/components/analysis/analysis-timeline";
import {
  useUploadResume,
  useAnalyzeGitHub,
  useRunAnalysis,
} from "@/hooks/use-analysis";
import { usePersistedState } from "@/hooks/use-persisted-state";
import { demoProfiles } from "@/lib/demo-profiles";

type Stage = "idle" | "processing" | "complete" | "error";

function AnalyzePageContent() {
  const router = useRouter();

  // ── Input state ──────────────────────────────────────────
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = usePersistedState<string | null>("analyze_resumeId", null);
  const [resumeMeta, setResumeMeta] = usePersistedState<{ name: string; size: number } | null>("analyze_resumeMeta", null);
  const [githubUsername, setGithubUsername] = usePersistedState<string | null>("analyze_github", null);
  const [stage, setStage] = useState<Stage>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [score, setScore] = useState<number | undefined>(undefined);

  // ── Mutations ────────────────────────────────────────────
  const uploadResume = useUploadResume();
  const analyzeGitHub = useAnalyzeGitHub();
  const runAnalysis = useRunAnalysis();

  // ── Timeline ─────────────────────────────────────────────
  const { steps, completeAll } = useTimelineProgress(stage === "processing");

  // ── Demo mode ────────────────────────────────────────────
  const searchParams = useSearchParams();
  const isDemo = searchParams.get("demo") === "true";

  const handleTryDemo = useCallback(() => {
    const profile = demoProfiles[0]; // Andrew Ng
    setStage("processing");
    setErrorMsg(null);

    // Simulate processing, then navigate to demo results
    setTimeout(() => {
      completeAll();
      setScore(profile.analysis.developer_score.overall);
      setStage("complete");

      setTimeout(() => {
        router.push(`/results/${profile.analysis.analysis_id}`);
      }, 1500);
    }, 2000);
  }, [completeAll, router]);

  useEffect(() => {
    if (isDemo && stage === "idle") {
      handleTryDemo();
    }
  }, [isDemo, stage, handleTryDemo]);

  // ── Handlers ─────────────────────────────────────────────
  const handleFileSelected = useCallback(
    (file: File) => {
      setResumeFile(file);
      setResumeMeta({ name: file.name, size: file.size });
      setErrorMsg(null);
      uploadResume.mutate(file, {
        onSuccess: (data: any) => {
          setResumeId(data.analysis_id);
        },
        onError: (err: Error) => {
          setErrorMsg(err.message || "Failed to upload resume");
        },
      });
    },
    [uploadResume, setResumeMeta, setResumeId]
  );

  const handleRemoveResume = useCallback(() => {
    setResumeFile(null);
    setResumeId(null);
    setResumeMeta(null);
    uploadResume.reset();
  }, [uploadResume, setResumeId, setResumeMeta]);

  const handleGitHubSubmit = useCallback(
    (username: string) => {
      setErrorMsg(null);
      analyzeGitHub.mutate(username, {
        onSuccess: () => {
          setGithubUsername(username);
        },
        onError: (err: Error) => {
          setErrorMsg(err.message || "Failed to analyze GitHub profile");
        },
      });
    },
    [analyzeGitHub]
  );

  const canAnalyze =
    (resumeFile || githubUsername) &&
    stage !== "processing" &&
    !uploadResume.isPending;

  const handleAnalyze = useCallback(() => {
    if (!canAnalyze) return;

    setStage("processing");
    setErrorMsg(null);

    runAnalysis.mutate(
      {
        file: resumeFile ?? undefined,
        github_username: githubUsername ?? undefined,
      },
      {
        onSuccess: (data: any) => {
          completeAll();
          setScore(data.developer_score?.overall ?? 0);
          setStage("complete");

          // Redirect after showing score briefly
          setTimeout(() => {
            router.push(`/results/${data.analysis_id}`);
          }, 2200);
        },
        onError: (err: Error) => {
          setStage("error");
          setErrorMsg(err.message || "Analysis failed. Please try again.");
        },
      }
    );
  }, [canAnalyze, resumeFile, githubUsername, runAnalysis, completeAll, router]);

  // ── Render ───────────────────────────────────────────────
  return (
    <div className="mx-auto max-w-7xl px-6 py-12 md:py-20">
      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-12"
      >
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Analyze Your <span className="gradient-text">Profile</span>
        </h1>
        <p className="mt-3 text-muted-foreground max-w-lg mx-auto">
          Upload your resume and connect your GitHub to get a comprehensive
          AI-powered analysis.
        </p>
      </motion.div>

      {/* Two-panel layout */}
      <div className="grid gap-8 lg:grid-cols-2 lg:items-start">
        {/* ── Left Panel: Inputs ────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div className="glass-card p-6 md:p-8 space-y-8">
            {/* Resume Upload */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-400" />
                <h2 className="text-sm font-semibold">Resume</h2>
                {resumeId && (
                  <span className="ml-auto text-xs text-emerald-400 font-medium">
                    Ready
                  </span>
                )}
              </div>
              <FileUploader
                onFileSelected={handleFileSelected}
                onRemove={handleRemoveResume}
                isUploading={uploadResume.isPending}
                isSuccess={!!resumeId}
                restoredFile={!resumeFile && resumeMeta ? resumeMeta : null}
                error={
                  uploadResume.isError
                    ? uploadResume.error?.message || "Upload failed"
                    : null
                }
              />
            </div>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/[0.06]" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-card px-3 text-muted-foreground/50 uppercase tracking-wider">
                  and / or
                </span>
              </div>
            </div>

            {/* GitHub Input */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Github className="h-4 w-4 text-violet-400" />
                <h2 className="text-sm font-semibold">GitHub Profile</h2>
                {githubUsername && (
                  <span className="ml-auto text-xs text-emerald-400 font-medium">
                    @{githubUsername}
                  </span>
                )}
              </div>
              <GitHubInput
                onSubmit={handleGitHubSubmit}
                isLoading={analyzeGitHub.isPending}
                isSuccess={!!githubUsername}
                error={
                  analyzeGitHub.isError
                    ? analyzeGitHub.error?.message || "GitHub analysis failed"
                    : null
                }
              />
            </div>

            {/* Analyze Button */}
            <div className="pt-2 space-y-3">
              <Button
                variant="gradient"
                size="lg"
                className="w-full gap-2"
                disabled={!canAnalyze}
                onClick={handleAnalyze}
              >
                {stage === "processing" ? (
                  <>
                    <Sparkles className="h-4 w-4 animate-pulse" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Analyze Profile
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>

              {stage === "idle" && !resumeId && !githubUsername && (
                <Button
                  variant="glass"
                  size="lg"
                  className="w-full gap-2"
                  onClick={handleTryDemo}
                >
                  <Play className="h-4 w-4 text-emerald-400" />
                  Try Demo Instead
                </Button>
              )}
            </div>

            {/* Error message at form level */}
            {errorMsg && stage === "error" && (
              <motion.p
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-red-400 text-center"
              >
                {errorMsg}
              </motion.p>
            )}
          </div>
        </motion.div>

        {/* ── Right Panel: AI Status ───────────────────── */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <AnalysisPanel
            state={stage}
            timelineSteps={steps}
            score={score}
            error={errorMsg}
          />
        </motion.div>
      </div>
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-7xl px-6 py-12 md:py-20 text-center text-muted-foreground">
          Loading...
        </div>
      }
    >
      <AnalyzePageContent />
    </Suspense>
  );
}
