"use client";

import React, { useMemo, useState } from "react";
import { LintIssue } from "@/lib/resumeTypes";

interface LintPanelProps {
  issues: LintIssue[];
  isLoading: boolean;
}

export default function LintPanel({ issues, isLoading }: LintPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  const { errors, warnings, tips } = useMemo(() => {
    const errs: LintIssue[] = [];
    const warns: LintIssue[] = [];
    const tps: LintIssue[] = [];
    for (const issue of issues) {
      if (issue.level === "error") errs.push(issue);
      else if (issue.level === "warning") warns.push(issue);
      else tps.push(issue);
    }
    return { errors: errs, warnings: warns, tips: tps };
  }, [issues]);

  const scrollToSection = (section: string) => {
    const sec = section.toLowerCase();
    let targetId = "section-basics";
    if (sec.includes("skill")) targetId = "section-skills";
    else if (sec.includes("experience")) targetId = "section-experience";
    else if (sec.includes("project")) targetId = "section-projects";
    else if (sec.includes("education")) targetId = "section-education";
    else if (sec.includes("link")) targetId = "section-links";
    else if (sec.includes("more") || sec.includes("cert") || sec.includes("publication")) targetId = "section-more";

    const el = document.getElementById(targetId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div
      style={{
        border: "1px solid #d9d5cc",
        borderRadius: "4px",
        backgroundColor: "#ffffff",
        marginBottom: "16px",
      }}
    >
      <div
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 14px",
          cursor: "pointer",
          backgroundColor: "#fffdf9",
          borderBottom: isOpen ? "1px solid #d9d5cc" : "none",
        }}
      >
        <span style={{ fontSize: "14px", fontWeight: 600 }}>
          Resume Quality & ATS Checks ({issues.length} {issues.length === 1 ? "note" : "notes"})
          {isLoading && <span style={{ fontSize: "12px", color: "#55534e", marginLeft: "6px" }}>(checking...)</span>}
        </span>
        <span style={{ fontSize: "13px", color: "#55534e" }}>
          {errors.length > 0 && <span style={{ color: "#8b0000", fontWeight: 600, marginRight: "8px" }}>{errors.length} errors</span>}
          {warnings.length > 0 && <span style={{ color: "#8a6d3b", marginRight: "8px" }}>{warnings.length} warnings</span>}
          {tips.length > 0 && <span style={{ color: "#2f5d50" }}>{tips.length} tips</span>}
          <span style={{ marginLeft: "8px" }}>{isOpen ? "[Hide]" : "[Show]"}</span>
        </span>
      </div>

      {isOpen && (
        <div style={{ padding: "12px 14px", fontSize: "13px" }}>
          {issues.length === 0 ? (
            <div style={{ color: "#2f5d50" }}>
              All ATS checks passed! Your resume structure is clean and standard.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {/* Errors */}
              {errors.map((err, idx) => (
                <div
                  key={`err-${idx}`}
                  onClick={() => scrollToSection(err.section)}
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    gap: "6px",
                    cursor: "pointer",
                    color: "#8b0000",
                  }}
                >
                  <strong style={{ textTransform: "uppercase", fontSize: "11px", border: "1px solid #8b0000", padding: "1px 4px", borderRadius: "2px" }}>
                    Error
                  </strong>
                  <span>{err.message}</span>
                  <span style={{ textDecoration: "underline", fontSize: "11px", color: "#55534e" }}>
                    (go to {err.section})
                  </span>
                </div>
              ))}

              {/* Warnings */}
              {warnings.map((warn, idx) => (
                <div
                  key={`warn-${idx}`}
                  onClick={() => scrollToSection(warn.section)}
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    gap: "6px",
                    cursor: "pointer",
                    color: "#8a6d3b",
                  }}
                >
                  <strong style={{ textTransform: "uppercase", fontSize: "11px", border: "1px solid #8a6d3b", padding: "1px 4px", borderRadius: "2px" }}>
                    Warning
                  </strong>
                  <span>{warn.message}</span>
                  <span style={{ textDecoration: "underline", fontSize: "11px", color: "#55534e" }}>
                    (go to {warn.section})
                  </span>
                </div>
              ))}

              {/* Tips */}
              {tips.map((tip, idx) => (
                <div
                  key={`tip-${idx}`}
                  onClick={() => scrollToSection(tip.section)}
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    gap: "6px",
                    cursor: "pointer",
                    color: "#2f5d50",
                  }}
                >
                  <strong style={{ textTransform: "uppercase", fontSize: "11px", border: "1px solid #2f5d50", padding: "1px 4px", borderRadius: "2px" }}>
                    Tip
                  </strong>
                  <span>{tip.message}</span>
                  <span style={{ textDecoration: "underline", fontSize: "11px", color: "#55534e" }}>
                    (go to {tip.section})
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
