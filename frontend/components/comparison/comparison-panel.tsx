"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  Circle,
  Loader2,
  User,
} from "lucide-react";
import { FileUploader } from "@/components/upload/file-uploader";
import { GitHubInput } from "@/components/upload/github-input";
import { Button } from "@/components/ui/button";

export interface DeveloperInputState {
  resumeFile: File | null;
  githubUsername: string;
  resumeId: string | null;
  analysisId: string | null;
  isUploadingResume: boolean;
  isUploadSuccess: boolean;
  uploadError: string | null;
  isAnalyzingGithub: boolean;
  isGithubSuccess: boolean;
  githubError: string | null;
  isRunningAnalysis: boolean;
  analysisComplete: boolean;
  analysisError: string | null;
}

export const INITIAL_STATE: DeveloperInputState = {
  resumeFile: null,
  githubUsername: "",
  resumeId: null,
  analysisId: null,
  isUploadingResume: false,
  isUploadSuccess: false,
  uploadError: null,
  isAnalyzingGithub: false,
  isGithubSuccess: false,
  githubError: null,
  isRunningAnalysis: false,
  analysisComplete: false,
  analysisError: null,
};

interface ComparisonPanelProps {
  label: string;
  color: "violet" | "blue";
  state: DeveloperInputState;
  onFileSelected: (file: File) => void;
  onRemoveFile?: () => void;
  onGitHubSubmit: (username: string) => void;
  onAnalyze: () => void;
  disabled?: boolean;
}

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

const colorMap = {
  violet: {
    badge: "bg-violet-500/15 text-violet-400 border-violet-500/25",
    check: "text-violet-400",
    btnGradient: "from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500",
  },
  blue: {
    badge: "bg-blue-500/15 text-blue-400 border-blue-500/25",
    check: "text-blue-400",
    btnGradient: "from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500",
  },
};

function StatusDot({
  done,
  label,
  color,
}: {
  done: boolean;
  label: string;
  color: "violet" | "blue";
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      {done ? (
        <CheckCircle2 className={`h-4 w-4 ${colorMap[color].check}`} />
      ) : (
        <Circle className="h-4 w-4 text-muted-foreground/30" />
      )}
      <span
        className={
          done ? "text-foreground font-medium" : "text-muted-foreground"
        }
      >
        {label}
      </span>
    </div>
  );
}

export function ComparisonPanel({
  label,
  color,
  state,
  onFileSelected,
  onRemoveFile,
  onGitHubSubmit,
  onAnalyze,
  disabled = false,
}: ComparisonPanelProps) {
  const colors = colorMap[color];
  const canAnalyze =
    (state.isUploadSuccess || state.isGithubSuccess) &&
    !state.isRunningAnalysis &&
    !state.analysisComplete;

  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className="glass-card p-6 md:p-8 space-y-5"
    >
      {/* Header badge */}
      <div className="flex items-center gap-3">
        <div
          className={`flex h-9 w-9 items-center justify-center rounded-xl border ${colors.badge}`}
        >
          <User className="h-4 w-4" />
        </div>
        <h3 className="text-base font-bold tracking-tight">{label}</h3>
      </div>

      {/* Resume upload */}
      <div className="space-y-1.5">
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
          Resume
        </p>
        <FileUploader
          onFileSelected={onFileSelected}
          onRemove={onRemoveFile}
          isUploading={state.isUploadingResume}
          isSuccess={state.isUploadSuccess}
          error={state.uploadError}
        />
      </div>

      {/* GitHub input */}
      <div className="space-y-1.5">
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
          GitHub Profile
        </p>
        <GitHubInput
          onSubmit={onGitHubSubmit}
          isLoading={state.isAnalyzingGithub}
          isSuccess={state.isGithubSuccess}
          error={state.githubError}
        />
      </div>

      {/* Status indicators */}
      <div className="flex items-center gap-4">
        <StatusDot
          done={state.isUploadSuccess}
          label="Resume uploaded"
          color={color}
        />
        <StatusDot
          done={state.isGithubSuccess}
          label="GitHub connected"
          color={color}
        />
      </div>

      {/* Analyze button */}
      <AnimatePresence>
        {state.analysisComplete ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20"
          >
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span className="text-sm font-medium text-emerald-400">
              Analysis complete
            </span>
          </motion.div>
        ) : (
          <Button
            onClick={onAnalyze}
            disabled={!canAnalyze || disabled}
            className={`w-full h-11 rounded-xl font-semibold bg-gradient-to-r ${colors.btnGradient} text-white shadow-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed`}
          >
            {state.isRunningAnalysis ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              "Analyze"
            )}
          </Button>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {state.analysisError && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="text-sm text-red-400"
          >
            {state.analysisError}
          </motion.p>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
