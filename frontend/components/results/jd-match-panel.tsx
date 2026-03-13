"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Briefcase,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { matchJobDescription } from "@/services/api";
import type { JDMatchResponse } from "@/types";

interface JDMatchPanelProps {
  analysisId: string;
}

export function JDMatchPanel({ analysisId }: JDMatchPanelProps) {
  const [jdText, setJdText] = useState("");
  const [result, setResult] = useState<JDMatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (jdText.trim().length < 20) {
      setError("Please enter at least 20 characters.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = (await matchJobDescription(
        analysisId,
        jdText.trim()
      )) as JDMatchResponse;
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Match failed");
    } finally {
      setLoading(false);
    }
  };

  const matchColor =
    result && result.match_percentage >= 70
      ? "text-emerald-400"
      : result && result.match_percentage >= 40
        ? "text-amber-400"
        : "text-red-400";

  return (
    <div className="glass-card p-6 md:p-8 space-y-5">
      <div className="flex items-center gap-2">
        <Briefcase className="h-5 w-5 text-violet-400" />
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Job Description Match
        </h3>
      </div>

      <p className="text-xs text-muted-foreground">
        Paste a job description to see how well your profile matches the
        required skills.
      </p>

      <textarea
        className="w-full rounded-lg border border-foreground/[0.08] bg-foreground/[0.02] px-4 py-3 text-sm
                   text-foreground placeholder:text-muted-foreground/50 focus:outline-none
                   focus:ring-1 focus:ring-violet-500/40 resize-y min-h-[120px]"
        rows={5}
        placeholder="Paste the job description here..."
        value={jdText}
        onChange={(e) => setJdText(e.target.value)}
      />

      {error && (
        <p className="text-xs text-red-400">{error}</p>
      )}

      <Button
        variant="glass"
        size="sm"
        onClick={handleSubmit}
        disabled={loading || jdText.trim().length < 20}
        className="gap-2"
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
        {loading ? "Matching..." : "Match Skills"}
      </Button>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-4 pt-2"
          >
            {/* Score */}
            <div className="flex items-center gap-3">
              <span className={`text-3xl font-bold ${matchColor}`}>
                {result.match_percentage}%
              </span>
              <span className="text-sm text-muted-foreground">match</span>
            </div>

            <p className="text-sm text-muted-foreground leading-relaxed">
              {result.summary}
            </p>

            {/* Matched skills */}
            {result.matched_skills.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Matched ({result.matched_skills.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {result.matched_skills.map((s) => (
                    <span
                      key={s.skill}
                      className="text-[11px] px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 capitalize"
                    >
                      {s.skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Partial skills */}
            {result.partial_skills.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Needs Improvement ({result.partial_skills.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {result.partial_skills.map((s) => (
                    <span
                      key={s.skill}
                      className="text-[11px] px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 capitalize"
                    >
                      {s.skill}
                      {s.proficiency && s.required_level && (
                        <span className="ml-1 opacity-70">
                          ({s.proficiency} → {s.required_level})
                        </span>
                      )}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Missing skills */}
            {result.missing_skills.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
                  <XCircle className="h-3.5 w-3.5" />
                  Missing ({result.missing_skills.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {result.missing_skills.map((s) => (
                    <span
                      key={s.skill}
                      className="text-[11px] px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 capitalize"
                    >
                      {s.skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
