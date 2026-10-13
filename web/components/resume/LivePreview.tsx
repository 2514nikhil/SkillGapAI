"use client";

import React, { useEffect, useState } from "react";
import { LintIssue, Resume } from "@/lib/resumeTypes";
import { downloadResume, renderHtmlPreview } from "@/lib/resumeApi";

interface LivePreviewProps {
  resume: Resume;
  pageSize: "A4" | "Letter";
  lintIssues: LintIssue[];
  onServerError?: (msg: string | null) => void;
}

export default function LivePreview({
  resume,
  pageSize,
  lintIssues,
  onServerError,
}: LivePreviewProps) {
  const [htmlContent, setHtmlContent] = useState<string>("");
  const [isRendering, setIsRendering] = useState(false);
  const [isDownloading, setIsDownloading] = useState<string | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);

  // Check if export should be disabled
  const hasErrors = lintIssues.some((i) => i.level === "error");
  const missingRequired = !resume.basics.name.trim() || !resume.basics.email.trim();
  const exportDisabled = hasErrors || missingRequired;

  const exportDisabledReason = missingRequired
    ? "Please provide your name and email to download your resume."
    : hasErrors
    ? "Please resolve the critical errors listed in the Quality Checks before downloading."
    : null;

  // Debounced render (600ms)
  useEffect(() => {
    let active = true;
    const timer = setTimeout(async () => {
      setIsRendering(true);
      setRenderError(null);
      try {
        const html = await renderHtmlPreview(
          resume,
          resume.meta.template || "classic",
          pageSize
        );
        if (active) {
          setHtmlContent(html);
        }
      } catch (err: any) {
        if (active) {
          setRenderError(err.message || "Failed to render preview.");
          if (onServerError) {
            onServerError("Server not responding. Editing and local auto-save continue to work.");
          }
        }
      } finally {
        if (active) {
          setIsRendering(false);
        }
      }
    }, 600);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [resume, pageSize, onServerError]);

  const handleDownload = async (format: "pdf" | "docx" | "md" | "txt" | "json") => {
    if (exportDisabled) return;

    setIsDownloading(format);
    try {
      const blob = await downloadResume(
        resume,
        format,
        resume.meta.template || "classic",
        pageSize
      );
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const cleanName = (resume.basics.name || "resume")
        .toLowerCase()
        .replace(/[^a-z0-9_-]/g, "_");
      a.download = `${cleanName}_resume.${format === "txt" ? "txt" : format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert(err.message || `Failed to download ${format.toUpperCase()}`);
    } finally {
      setIsDownloading(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      {/* Download Action Row */}
      <div
        style={{
          border: "1px solid #d9d5cc",
          borderRadius: "4px",
          padding: "12px",
          backgroundColor: "#ffffff",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "14px", fontWeight: 600 }}>
            Download Resume
          </span>
          {isRendering && (
            <span style={{ fontSize: "12px", color: "#55534e" }}>
              Updating preview...
            </span>
          )}
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: exportDisabled ? "6px" : 0 }}>
          <button
            type="button"
            disabled={exportDisabled || isDownloading !== null}
            onClick={() => handleDownload("pdf")}
            style={{
              border: "1px solid #2f5d50",
              backgroundColor: exportDisabled ? "#ece8e1" : "#2f5d50",
              color: exportDisabled ? "#888888" : "#ffffff",
              padding: "6px 12px",
              borderRadius: "4px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: exportDisabled ? "not-allowed" : "pointer",
            }}
          >
            {isDownloading === "pdf" ? "Exporting..." : "Download PDF"}
          </button>

          <button
            type="button"
            disabled={exportDisabled || isDownloading !== null}
            onClick={() => handleDownload("docx")}
            style={{
              border: "1px solid #d9d5cc",
              backgroundColor: exportDisabled ? "#ece8e1" : "#ffffff",
              color: exportDisabled ? "#888888" : "#1d1d1b",
              padding: "6px 12px",
              borderRadius: "4px",
              fontSize: "13px",
              cursor: exportDisabled ? "not-allowed" : "pointer",
            }}
          >
            {isDownloading === "docx" ? "Exporting..." : "Word (DOCX)"}
          </button>

          <button
            type="button"
            disabled={exportDisabled || isDownloading !== null}
            onClick={() => handleDownload("md")}
            style={{
              border: "1px solid #d9d5cc",
              backgroundColor: exportDisabled ? "#ece8e1" : "#ffffff",
              color: exportDisabled ? "#888888" : "#1d1d1b",
              padding: "6px 12px",
              borderRadius: "4px",
              fontSize: "13px",
              cursor: exportDisabled ? "not-allowed" : "pointer",
            }}
          >
            {isDownloading === "md" ? "Exporting..." : "Markdown"}
          </button>

          <button
            type="button"
            disabled={exportDisabled || isDownloading !== null}
            onClick={() => handleDownload("txt")}
            style={{
              border: "1px solid #d9d5cc",
              backgroundColor: exportDisabled ? "#ece8e1" : "#ffffff",
              color: exportDisabled ? "#888888" : "#1d1d1b",
              padding: "6px 12px",
              borderRadius: "4px",
              fontSize: "13px",
              cursor: exportDisabled ? "not-allowed" : "pointer",
            }}
          >
            {isDownloading === "txt" ? "Exporting..." : "Plain Text"}
          </button>

          <button
            type="button"
            disabled={exportDisabled || isDownloading !== null}
            onClick={() => handleDownload("json")}
            style={{
              border: "1px solid #d9d5cc",
              backgroundColor: exportDisabled ? "#ece8e1" : "#ffffff",
              color: exportDisabled ? "#888888" : "#1d1d1b",
              padding: "6px 12px",
              borderRadius: "4px",
              fontSize: "13px",
              cursor: exportDisabled ? "not-allowed" : "pointer",
            }}
          >
            {isDownloading === "json" ? "Exporting..." : "JSON"}
          </button>
        </div>

        {exportDisabledReason && (
          <div style={{ fontSize: "12px", color: "#8b0000", marginTop: "6px" }}>
            {exportDisabledReason}
          </div>
        )}
      </div>

      {/* Sandboxed iframe preview */}
      <div
        style={{
          border: "1px solid #d9d5cc",
          borderRadius: "4px",
          backgroundColor: "#ffffff",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "8px 12px",
            backgroundColor: "#fffdf9",
            borderBottom: "1px solid #d9d5cc",
            fontSize: "13px",
            fontWeight: 600,
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span>Live ATS Preview ({resume.meta.template || "classic"}, {pageSize})</span>
          <span style={{ fontSize: "11px", color: "#55534e" }}>Sandboxed renderer</span>
        </div>

        {renderError ? (
          <div style={{ padding: "24px", color: "#8b0000", fontSize: "14px" }}>
            {renderError}
          </div>
        ) : (
          <iframe
            srcDoc={htmlContent}
            sandbox="allow-same-origin allow-scripts"
            title="Resume Preview"
            style={{
              width: "100%",
              height: "820px",
              border: "none",
              backgroundColor: "#ffffff",
              display: "block",
            }}
          />
        )}
      </div>
    </div>
  );
}
