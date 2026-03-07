"use client";

import { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, AlertCircle, GitCompareArrows, Loader2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ComparisonPanel,
  INITIAL_STATE,
  type DeveloperInputState,
} from "@/components/comparison/comparison-panel";
import { ComparisonResults } from "@/components/comparison/comparison-results";
import {
  uploadResume,
  analyzeGitHub,
  runAnalysis,
  getAnalysisResults,
  compareProfiles,
} from "@/services/api";
import type {
  AnalysisResponse,
  CompareResponse,
  ResumeUploadResponse,
} from "@/types";

type DevKey = "a" | "b";
type FlowStatus = "idle" | "analyzingA" | "analyzingB" | "comparing" | "complete" | "error";

export default function ComparePage() {
  const [stateA, setStateA] = useState<DeveloperInputState>({
    ...INITIAL_STATE,
  });
  const [stateB, setStateB] = useState<DeveloperInputState>({
    ...INITIAL_STATE,
  });

  const [analysisDataA, setAnalysisDataA] = useState<AnalysisResponse | null>(
    null
  );
  const [analysisDataB, setAnalysisDataB] = useState<AnalysisResponse | null>(
    null
  );

  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);
  const [flowStatus, setFlowStatus] = useState<FlowStatus>("idle");
  const hasCompared = useRef(false);

  // Helpers to update nested state
  const update = useCallback(
    (key: DevKey, patch: Partial<DeveloperInputState>) => {
      if (key === "a") setStateA((s) => ({ ...s, ...patch }));
      else setStateB((s) => ({ ...s, ...patch }));
    },
    []
  );

  // ── File handlers ──────────────────────────────────────
  const handleFile = useCallback(
    async (key: DevKey, file: File) => {
      update(key, {
        resumeFile: file,
        isUploadingResume: true,
        uploadError: null,
        isUploadSuccess: false,
      });
      try {
        const res = (await uploadResume(file)) as ResumeUploadResponse;
        update(key, {
          resumeId: res.resume_id,
          isUploadingResume: false,
          isUploadSuccess: true,
        });
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Upload failed";
        update(key, {
          isUploadingResume: false,
          uploadError: message,
        });
      }
    },
    [update]
  );

  // ── GitHub handlers ────────────────────────────────────
  const handleGitHub = useCallback(
    async (key: DevKey, username: string) => {
      update(key, {
        githubUsername: username,
        isAnalyzingGithub: true,
        githubError: null,
        isGithubSuccess: false,
      });
      try {
        await analyzeGitHub(username);
        update(key, { isAnalyzingGithub: false, isGithubSuccess: true });
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "GitHub analysis failed";
        update(key, { isAnalyzingGithub: false, githubError: message });
      }
    },
    [update]
  );

  // ── Analyze handler ────────────────────────────────────
  const handleAnalyze = useCallback(
    async (key: DevKey) => {
      const st = key === "a" ? stateA : stateB;
      update(key, {
        isRunningAnalysis: true,
        analysisError: null,
      });
      setFlowStatus(key === "a" ? "analyzingA" : "analyzingB");
      try {
        const res = (await runAnalysis({
          resume_id: st.resumeId ?? undefined,
          github_username: st.githubUsername || undefined,
        })) as AnalysisResponse;

        update(key, {
          analysisId: res.analysis_id,
          isRunningAnalysis: false,
          analysisComplete: true,
        });

        // Fetch full analysis data
        const full = (await getAnalysisResults(
          res.analysis_id
        )) as AnalysisResponse;
        if (key === "a") setAnalysisDataA(full);
        else setAnalysisDataB(full);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Analysis failed";
        update(key, { isRunningAnalysis: false, analysisError: message });
        setFlowStatus("error");
      }
    },
    [stateA, stateB, update]
  );

  // ── Compare handler ────────────────────────────────────
  const handleCompare = useCallback(async () => {
    if (!stateA.analysisId || !stateB.analysisId) return;
    setIsComparing(true);
    setCompareError(null);
    setFlowStatus("comparing");
    try {
      const res = (await compareProfiles(
        stateA.analysisId,
        stateB.analysisId
      )) as CompareResponse;
      setComparison(res);
      setFlowStatus("complete");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Comparison failed";
      setCompareError(message);
      setFlowStatus("error");
    } finally {
      setIsComparing(false);
    }
  }, [stateA.analysisId, stateB.analysisId]);

  // Auto-trigger comparison exactly once when both analyses finish
  const bothDone = stateA.analysisComplete && stateB.analysisComplete;

  if (
    bothDone &&
    !hasCompared.current &&
    stateA.analysisId &&
    stateB.analysisId
  ) {
    hasCompared.current = true;
    handleCompare();
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12 md:py-20">
      {/* ── Header ──────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-10"
      >
        <Button
          variant="ghost"
          size="sm"
          className="mb-2 -ml-3 text-muted-foreground"
          asChild
        >
          <Link href="/">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Home
          </Link>
        </Button>
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/20 to-blue-500/20 border border-white/[0.08]">
            <GitCompareArrows className="h-5 w-5 text-violet-400" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            Compare Two{" "}
            <span className="gradient-text">Developer Profiles</span>
          </h1>
        </div>
        <p className="text-sm text-muted-foreground max-w-lg">
          Upload two resumes or GitHub profiles to compare developer
          capabilities using AI.
        </p>
      </motion.div>

      {/* ── Two-column input panels ──────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        <ComparisonPanel
          label="Developer A"
          color="violet"
          state={stateA}
          onFileSelected={(f) => handleFile("a", f)}
          onGitHubSubmit={(u) => handleGitHub("a", u)}
          onAnalyze={() => handleAnalyze("a")}
        />
        <ComparisonPanel
          label="Developer B"
          color="blue"
          state={stateB}
          onFileSelected={(f) => handleFile("b", f)}
          onGitHubSubmit={(u) => handleGitHub("b", u)}
          onAnalyze={() => handleAnalyze("b")}
        />
      </div>

      {/* ── Flow status banner ──────────────────────── */}
      <AnimatePresence>
        {flowStatus !== "idle" && flowStatus !== "complete" && !comparison && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-4 mb-10"
          >
            {flowStatus === "analyzingA" && (
              <div className="glass-card px-8 py-6 flex items-center gap-3">
                <Loader2 className="h-5 w-5 text-violet-400 animate-spin" />
                <span className="text-sm font-medium text-muted-foreground">
                  Analyzing Developer A...
                </span>
              </div>
            )}
            {flowStatus === "analyzingB" && (
              <div className="glass-card px-8 py-6 flex items-center gap-3">
                <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
                <span className="text-sm font-medium text-muted-foreground">
                  Analyzing Developer B...
                </span>
              </div>
            )}
            {flowStatus === "comparing" && (
              <div className="glass-card px-8 py-6 flex items-center gap-3">
                <Loader2 className="h-5 w-5 text-violet-400 animate-spin" />
                <span className="text-sm font-medium text-muted-foreground">
                  Running comparison...
                </span>
              </div>
            )}
            {flowStatus === "error" && (
              <div className="glass-card px-8 py-6 text-center space-y-3">
                <div className="flex items-center justify-center gap-2 text-red-400">
                  <AlertCircle className="h-4 w-4" />
                  <p className="text-sm">{compareError || "Something went wrong."}</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    hasCompared.current = false;
                    setFlowStatus("idle");
                    handleCompare();
                  }}
                  className="text-blue-400"
                >
                  Retry
                </Button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Results ──────────────────────────────────── */}
      <AnimatePresence>
        {comparison && analysisDataA && analysisDataB && (
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            <ComparisonResults
              comparison={comparison}
              analysisA={analysisDataA}
              analysisB={analysisDataB}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
