"use client";

import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";

/** Reusable loading skeleton for any dashboard section. */
export function SectionSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="glass-card p-6 md:p-8 space-y-4"
    >
      <Skeleton className="h-5 w-1/3" />
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    </motion.div>
  );
}

export function ScoreSkeleton() {
  return (
    <div className="glass-card p-6 md:p-8">
      <div className="flex flex-col md:flex-row items-center gap-8 md:gap-12">
        <Skeleton className="h-[200px] w-[200px] rounded-full shrink-0" />
        <div className="flex-1 w-full space-y-5">
          <Skeleton className="h-4 w-1/4" />
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="space-y-1.5">
              <div className="flex justify-between">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-10" />
              </div>
              <Skeleton className="h-2.5 w-full rounded-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
