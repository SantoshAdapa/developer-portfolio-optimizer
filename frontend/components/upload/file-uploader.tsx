"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  CheckCircle2,
  XCircle,
  Loader2,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface FileUploaderProps {
  onFileSelected: (file: File) => void;
  onRemove?: () => void;
  isUploading?: boolean;
  isSuccess?: boolean;
  error?: string | null;
  accept?: Record<string, string[]>;
  maxSize?: number;
}

export function FileUploader({
  onFileSelected,
  onRemove,
  isUploading = false,
  isSuccess = false,
  error = null,
  accept = {
    "application/pdf": [".pdf"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
      ".docx",
    ],
  },
  maxSize = 10 * 1024 * 1024, // 10MB
}: FileUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        setSelectedFile(file);
        onFileSelected(file);
      }
    },
    [onFileSelected]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } =
    useDropzone({
      onDrop,
      accept,
      maxSize,
      multiple: false,
      disabled: isUploading,
    });

  const rejectionError =
    fileRejections.length > 0
      ? fileRejections[0].errors[0]?.message || "Invalid file"
      : null;

  const displayError = error || rejectionError;

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={cn(
          "relative group cursor-pointer rounded-2xl border-2 border-dashed p-8 transition-all duration-300 text-center",
          isDragActive
            ? "border-blue-500/50 bg-blue-500/[0.08] scale-[1.02]"
            : "border-white/[0.1] bg-white/[0.02] hover:border-white/[0.2] hover:bg-white/[0.04]",
          isUploading && "pointer-events-none opacity-60",
          isSuccess && "border-emerald-500/30 bg-emerald-500/[0.05]",
          displayError && "border-red-500/30 bg-red-500/[0.05]"
        )}
      >
        <input {...getInputProps()} />

        <AnimatePresence mode="wait">
          {isUploading ? (
            <motion.div
              key="uploading"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-3"
            >
              <Loader2 className="h-10 w-10 text-blue-400 animate-spin" />
              <p className="text-sm text-muted-foreground">
                Uploading {selectedFile?.name}...
              </p>
            </motion.div>
          ) : isSuccess && selectedFile ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-3"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20">
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-emerald-400">
                  Upload complete
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {selectedFile.name} (
                  {(selectedFile.size / 1024).toFixed(1)} KB)
                </p>
              </div>
              {onRemove && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="gap-1.5 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                    onRemove();
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Remove
                </Button>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="idle"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-4"
            >
              <div
                className={cn(
                  "flex h-14 w-14 items-center justify-center rounded-2xl transition-colors duration-300",
                  isDragActive
                    ? "bg-blue-500/20"
                    : "bg-white/[0.06] group-hover:bg-white/[0.1]"
                )}
              >
                {selectedFile ? (
                  <FileText className="h-7 w-7 text-blue-400" />
                ) : (
                  <Upload
                    className={cn(
                      "h-7 w-7 transition-colors",
                      isDragActive
                        ? "text-blue-400"
                        : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                )}
              </div>

              {isDragActive ? (
                <p className="text-sm font-medium text-blue-400">
                  Drop your resume here
                </p>
              ) : selectedFile ? (
                <div>
                  <p className="text-sm font-medium">{selectedFile.name}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {(selectedFile.size / 1024).toFixed(1)} KB &middot; Click or
                    drag to replace
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-medium">
                    <span className="text-blue-400">Click to upload</span> or
                    drag and drop
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    PDF, DOC, or DOCX &middot; Max 10 MB
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Error message */}
      <AnimatePresence>
        {displayError && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex items-center gap-2 text-sm text-red-400"
          >
            <XCircle className="h-4 w-4 shrink-0" />
            <span>{displayError}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
