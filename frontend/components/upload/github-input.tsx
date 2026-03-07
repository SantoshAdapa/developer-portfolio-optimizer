"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Github, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface GitHubInputProps {
  onSubmit: (username: string) => void;
  isLoading?: boolean;
  isSuccess?: boolean;
  error?: string | null;
}

function extractUsername(input: string): string {
  const trimmed = input.trim();
  // Handle full GitHub URLs
  const urlMatch = trimmed.match(
    /(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})\/?$/
  );
  if (urlMatch) return urlMatch[1];
  // Otherwise treat as plain username
  return trimmed.replace(/^@/, "");
}

export function GitHubInput({
  onSubmit,
  isLoading = false,
  isSuccess = false,
  error = null,
}: GitHubInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const username = extractUsername(value);
    if (username) {
      onSubmit(username);
    }
  };

  const username = extractUsername(value);

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="relative">
        <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2">
          {isLoading ? (
            <Loader2 className="h-4 w-4 text-muted-foreground animate-spin" />
          ) : isSuccess ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          ) : (
            <Github className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
        <Input
          type="text"
          placeholder="GitHub username or profile URL"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={isLoading}
          className={cn(
            "h-12 pl-10 pr-24 rounded-xl bg-white/[0.03] border-white/[0.08] placeholder:text-muted-foreground/50 focus:border-blue-500/40 focus:ring-blue-500/20 transition-all",
            isSuccess && "border-emerald-500/30",
            error && "border-red-500/30"
          )}
        />
        <div className="absolute right-1.5 top-1/2 -translate-y-1/2">
          <Button
            type="submit"
            variant="ghost"
            size="sm"
            disabled={!username || isLoading || isSuccess}
            className="h-9 px-3 text-xs font-medium text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
          >
            {isLoading ? "Checking..." : isSuccess ? "Connected" : "Connect"}
          </Button>
        </div>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex items-center gap-2 text-sm text-red-400"
          >
            <XCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}

        {isSuccess && username && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex items-center gap-2 text-sm text-emerald-400"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>GitHub profile found: @{username}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </form>
  );
}
