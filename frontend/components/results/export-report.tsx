"use client";

import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ExportReportProps {
  data: Record<string, unknown>;
}

export function ExportReport({ data }: ExportReportProps) {
  const handleExport = () => {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "developer-portfolio-report.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Button
      variant="glass"
      size="sm"
      onClick={handleExport}
      className="gap-2"
    >
      <Download className="h-4 w-4" />
      Export AI Report
    </Button>
  );
}
