import { Sparkles } from "lucide-react";
import { siteConfig } from "@/lib/constants";

export function Footer() {
  return (
    <footer className="border-t border-border/50 bg-background/40 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="flex flex-col items-center gap-4 md:flex-row md:justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-blue-500 to-violet-600">
              <Sparkles className="h-3 w-3 text-white" />
            </div>
            <span className="text-sm font-medium text-muted-foreground">
              {siteConfig.name}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            Built with AI to help developers grow.
          </p>
        </div>
      </div>
    </footer>
  );
}
