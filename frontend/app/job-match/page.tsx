"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Briefcase,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  Zap,
  User,
  FileText,
  Star,
  BarChart3,
  Upload,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  matchResumeJobDescription,
  matchResumeByRole,
  matchResumeByLevel,
  getRoleTemplates,
  getExperienceLevels,
} from "@/services/api";
import type {
  JDMatchResponse,
  RoleTemplateInfo,
  ExperienceLevelInfo,
} from "@/types";

type MatchMode = "jd" | "role" | "level";

const DOMAIN_COLORS: Record<string, string> = {
  "ML/AI": "from-violet-500 to-purple-600",
  Backend: "from-blue-500 to-cyan-600",
  Frontend: "from-emerald-500 to-teal-600",
  DevOps: "from-orange-500 to-amber-600",
  Data: "from-rose-500 to-pink-600",
  Testing: "from-indigo-500 to-blue-600",
  Other: "from-slate-500 to-gray-600",
};

export default function JobMatchPage() {
  const [mode, setMode] = useState<MatchMode>("jd");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [selectedRole, setSelectedRole] = useState("");
  const [selectedLevel, setSelectedLevel] = useState("");
  const [roles, setRoles] = useState<RoleTemplateInfo[]>([]);
  const [levels, setLevels] = useState<ExperienceLevelInfo[]>([]);
  const [result, setResult] = useState<JDMatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingMeta, setLoadingMeta] = useState(true);

  useEffect(() => {
    Promise.all([getRoleTemplates(), getExperienceLevels()])
      .then(([r, l]) => {
        setRoles(r as RoleTemplateInfo[]);
        setLevels(l as ExperienceLevelInfo[]);
        if ((r as RoleTemplateInfo[]).length > 0) {
          setSelectedRole((r as RoleTemplateInfo[])[0].key);
        }
        if ((l as ExperienceLevelInfo[]).length > 0) {
          setSelectedLevel((l as ExperienceLevelInfo[])[0].key);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingMeta(false));
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== "application/pdf") {
        setError("Please upload a PDF file.");
        return;
      }
      setResumeFile(file);
      setError(null);
    }
  }, []);

  const handleRemoveResume = useCallback(() => {
    setResumeFile(null);
  }, []);

  const canSubmit = () => {
    if (!resumeFile) return false;
    if (mode === "jd") return jdText.trim().length >= 20;
    if (mode === "role") return !!selectedRole;
    if (mode === "level") return !!selectedLevel;
    return false;
  };

  const handleSubmit = async () => {
    if (!resumeFile) {
      setError("Please upload your resume first.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      let res: JDMatchResponse;
      if (mode === "jd") {
        res = (await matchResumeJobDescription(resumeFile, jdText.trim())) as JDMatchResponse;
      } else if (mode === "role") {
        res = (await matchResumeByRole(resumeFile, selectedRole)) as JDMatchResponse;
      } else {
        res = (await matchResumeByLevel(resumeFile, selectedLevel)) as JDMatchResponse;
      }
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Match failed. Please try again.");
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

  const confidenceBadge = {
    high: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    medium: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    low: "bg-red-500/10 text-red-400 border-red-500/20",
  };

  return (
    <div className="mx-auto max-w-4xl px-6 py-12 md:py-20">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-10"
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 shadow-lg shadow-violet-500/25">
            <Briefcase className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            Job <span className="gradient-text">Match</span>
          </h1>
        </div>
        <p className="text-muted-foreground">
          Upload your resume and compare it against a job description, role template, or experience
          level using semantic AI matching.
        </p>
      </motion.div>

      {/* Resume Upload */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.05 }}
        className="glass-card p-6 mb-5"
      >
        <div className="flex items-center gap-2 mb-3">
          <Upload className="h-4 w-4 text-blue-400" />
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Upload Resume
          </label>
          {resumeFile && (
            <span className="ml-auto text-xs text-emerald-400 font-medium flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" /> Ready
            </span>
          )}
        </div>

        {resumeFile ? (
          <div className="flex items-center justify-between gap-3 rounded-lg border border-foreground/[0.08] bg-foreground/[0.02] px-4 py-3">
            <div className="flex items-center gap-2 min-w-0">
              <FileText className="h-4 w-4 text-blue-400 flex-shrink-0" />
              <span className="text-sm text-foreground truncate">{resumeFile.name}</span>
              <span className="text-xs text-muted-foreground/60 flex-shrink-0">
                ({(resumeFile.size / 1024).toFixed(0)} KB)
              </span>
            </div>
            <button
              onClick={handleRemoveResume}
              className="text-xs text-muted-foreground hover:text-red-400 transition-colors flex-shrink-0"
            >
              Remove
            </button>
          </div>
        ) : (
          <label className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-foreground/[0.08] bg-foreground/[0.01] px-4 py-8 cursor-pointer hover:border-violet-500/30 hover:bg-violet-500/[0.02] transition-all">
            <Upload className="h-6 w-6 text-muted-foreground/50" />
            <span className="text-sm text-muted-foreground">
              Click to upload your resume (PDF)
            </span>
            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
        )}
      </motion.div>

      {/* Mode selector */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="glass-card p-6 mb-5"
      >
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
          Choose Matching Mode
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {(
            [
              {
                key: "jd",
                icon: FileText,
                label: "Job Description",
                desc: "Paste a full JD",
              },
              {
                key: "role",
                icon: Briefcase,
                label: "Role Template",
                desc: "Select a job role",
              },
              {
                key: "level",
                icon: User,
                label: "Experience Level",
                desc: "Select seniority tier",
              },
            ] as const
          ).map(({ key, icon: Icon, label, desc }) => (
            <button
              key={key}
              onClick={() => setMode(key)}
              className={`flex flex-col items-start gap-1.5 rounded-xl border p-4 text-left transition-all ${
                mode === key
                  ? "border-violet-500/50 bg-violet-500/10 text-foreground"
                  : "border-foreground/[0.08] bg-foreground/[0.02] text-muted-foreground hover:border-foreground/20 hover:text-foreground"
              }`}
            >
              <Icon className={`h-5 w-5 ${mode === key ? "text-violet-400" : ""}`} />
              <span className="text-sm font-semibold">{label}</span>
              <span className="text-xs opacity-70">{desc}</span>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Mode-specific inputs */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.15 }}
        className="glass-card p-6 mb-5"
      >
        <AnimatePresence mode="wait">
          {mode === "jd" && (
            <motion.div
              key="jd"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 block">
                Job Description
              </label>
              <textarea
                className="w-full rounded-lg border border-foreground/[0.08] bg-foreground/[0.02] px-4 py-3 text-sm
                           text-foreground placeholder:text-muted-foreground/50 focus:outline-none
                           focus:ring-1 focus:ring-violet-500/40 resize-y min-h-[160px]"
                rows={7}
                placeholder="Paste the full job description here..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1.5">
                {jdText.length} characters (min 20)
              </p>
            </motion.div>
          )}

          {mode === "role" && (
            <motion.div
              key="role"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                Select Role Template
              </label>
              {loadingMeta ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Loading roles...
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {roles.map((r) => (
                    <button
                      key={r.key}
                      onClick={() => setSelectedRole(r.key)}
                      className={`flex flex-col items-start gap-1 rounded-xl border p-4 text-left transition-all ${
                        selectedRole === r.key
                          ? "border-violet-500/50 bg-violet-500/10"
                          : "border-foreground/[0.08] bg-foreground/[0.02] hover:border-foreground/20"
                      }`}
                    >
                      <span
                        className={`text-sm font-semibold ${selectedRole === r.key ? "text-foreground" : "text-muted-foreground"}`}
                      >
                        {r.label}
                      </span>
                      <span className="text-xs text-muted-foreground/60">
                        {r.required_skills.slice(0, 3).join(", ")}
                        {r.required_skills.length > 3 ? " +" + (r.required_skills.length - 3) + " more" : ""}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {mode === "level" && (
            <motion.div
              key="level"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                Select Experience Level
              </label>
              {loadingMeta ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Loading levels...
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {levels.map((l) => (
                    <button
                      key={l.key}
                      onClick={() => setSelectedLevel(l.key)}
                      className={`flex flex-col items-start gap-1.5 rounded-xl border p-4 text-left transition-all ${
                        selectedLevel === l.key
                          ? "border-violet-500/50 bg-violet-500/10"
                          : "border-foreground/[0.08] bg-foreground/[0.02] hover:border-foreground/20"
                      }`}
                    >
                      <span
                        className={`text-sm font-semibold ${selectedLevel === l.key ? "text-foreground" : "text-muted-foreground"}`}
                      >
                        {l.label}
                      </span>
                      <span className="text-xs text-muted-foreground/60">{l.description}</span>
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Submit */}
      {error && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-xs text-red-400 mb-3"
        >
          {error}
        </motion.p>
      )}

      <Button
        variant="gradient"
        size="lg"
        onClick={handleSubmit}
        disabled={loading || !canSubmit()}
        className="w-full gap-2 mb-8"
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Zap className="h-4 w-4" />
        )}
        {loading ? "Matching..." : "Run Semantic Match"}
      </Button>

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-5"
          >
            {/* Score header */}
            <div className="glass-card p-6">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                    {result.label || "Match Score"}
                  </p>
                  <div className="flex items-end gap-3">
                    <span className={`text-5xl font-bold ${matchColor}`}>
                      {result.match_percentage}%
                    </span>
                    <span className="text-base text-muted-foreground mb-1">match</span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full border font-semibold capitalize ${
                      confidenceBadge[result.confidence] || confidenceBadge.medium
                    }`}
                  >
                    {result.confidence} confidence
                  </span>
                </div>
              </div>

              {/* Score bar */}
              <div className="mt-4 h-2 rounded-full overflow-hidden" style={{ background: "var(--bar-track)" }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${result.match_percentage}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  className={`h-full rounded-full ${
                    result.match_percentage >= 70
                      ? "bg-emerald-500"
                      : result.match_percentage >= 40
                        ? "bg-amber-500"
                        : "bg-red-500"
                  }`}
                />
              </div>

              <p className="mt-4 text-sm text-muted-foreground leading-relaxed">
                {result.summary}
              </p>
            </div>

            {/* Skill breakdown */}
            <div className="glass-card p-6 space-y-5">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-violet-400" />
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                  Skill Breakdown
                </h3>
              </div>

              {/* Matched */}
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
                        title={s.match_type === "semantic" ? "Semantic match" : ""}
                        className="text-[11px] px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      >
                        {s.skill}
                        {s.match_type === "semantic" && (
                          <span className="ml-1 opacity-60">~</span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Preferred matched */}
              {result.preferred_matched && result.preferred_matched.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Star className="h-3.5 w-3.5" />
                    Preferred Skills Matched ({result.preferred_matched.length})
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.preferred_matched.map((s) => (
                      <span
                        key={s.skill}
                        className="text-[11px] px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                      >
                        {s.skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Partial */}
              {result.partial_skills.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Needs Leveling Up ({result.partial_skills.length})
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.partial_skills.map((s) => (
                      <span
                        key={s.skill}
                        className="text-[11px] px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      >
                        {s.skill}
                        {s.proficiency && s.required_level && (
                          <span className="ml-1 opacity-60">
                            {s.proficiency} → {s.required_level}
                          </span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Missing */}
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
                        className="text-[11px] px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20"
                      >
                        {s.skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Recommended Skills to Learn */}
            {result.recommended_skills && result.recommended_skills.length > 0 && (
              <div className="glass-card p-6 space-y-4">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-blue-400" />
                  <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                    Recommended Skills to Learn
                  </h3>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {result.recommended_skills.map((skill) => (
                    <span
                      key={skill}
                      className="text-[11px] px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Domain distribution */}
            {result.domain_distribution &&
              Object.keys(result.domain_distribution).length > 0 && (
                <div className="glass-card p-6 space-y-4">
                  <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                    Your Skill Domain Distribution
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(result.domain_distribution)
                      .sort(([, a], [, b]) => b - a)
                      .map(([domain, pct]) => (
                        <div key={domain}>
                          <div className="flex justify-between mb-1">
                            <span className="text-xs text-muted-foreground">{domain}</span>
                            <span className="text-xs font-semibold tabular-nums">{pct}%</span>
                          </div>
                          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--bar-track)" }}>
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${pct}%` }}
                              transition={{ duration: 0.6, ease: "easeOut" }}
                              className={`h-full rounded-full bg-gradient-to-r ${
                                DOMAIN_COLORS[domain] || DOMAIN_COLORS.Other
                              }`}
                            />
                          </div>
                        </div>
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
