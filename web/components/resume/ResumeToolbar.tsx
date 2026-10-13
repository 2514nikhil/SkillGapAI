"use client";

import React, { useEffect, useRef, useState } from "react";
import { Resume } from "@/lib/resumeTypes";
import {
  clearResumeFromLocalStorage,
  createEmptyResume,
  hasAnalyzedResumeSession,
  loadResumeFromAnalyzedSession,
} from "@/lib/resumeStorage";

import { importResumeFile } from "@/lib/resumeApi";

interface ResumeToolbarProps {
  resume: Resume;
  onChange: (updated: Resume) => void;
  pageSize: "A4" | "Letter";
  onPageSizeChange: (size: "A4" | "Letter") => void;
  onImportReviewNotes?: (notes: Array<{ field: string; note: string }>) => void;
}

export default function ResumeToolbar({
  resume,
  onChange,
  pageSize,
  onPageSizeChange,
  onImportReviewNotes,
}: ResumeToolbarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const docFileInputRef = useRef<HTMLInputElement>(null);
  const [isImportingDoc, setIsImportingDoc] = useState(false);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);

  useEffect(() => {
    setHasAnalyzed(hasAnalyzedResumeSession());
  }, []);

  const handleTemplateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({
      ...resume,
      meta: {
        ...resume.meta,
        template: e.target.value as "classic" | "compact" | "technical",
      },
    });
  };

  const handleClear = () => {
    if (
      typeof window !== "undefined" &&
      window.confirm("Are you sure you want to clear your entire resume draft? This cannot be undone.")
    ) {
      clearResumeFromLocalStorage();
      onChange(createEmptyResume());
    }
  };

  const handleStartFromAnalysis = () => {
    const fromSession = loadResumeFromAnalyzedSession();
    if (fromSession) {
      onChange({
        ...resume,
        meta: {
          ...resume.meta,
          target_role: fromSession.meta.target_role || resume.meta.target_role,
        },
        skills: fromSession.skills.length > 0 ? fromSession.skills : resume.skills,
      });
    }
  };

  const handleFileImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const parsed = JSON.parse(text);
        if (parsed && typeof parsed === "object" && parsed.basics) {
          onChange(parsed as Resume);
        } else {
          alert("The uploaded JSON file does not appear to be a valid SkillGap resume schema.");
        }
      } catch {
        alert("Failed to parse JSON file. Please check file format.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleDocImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsImportingDoc(true);
    try {
      const res = await importResumeFile(file);
      if (res && res.resume) {
        onChange(res.resume);
        if (onImportReviewNotes) {
          onImportReviewNotes(res.needs_review || []);
        }
      }
    } catch (err: any) {
      alert(err.message || "Failed to parse uploaded resume document.");
    } finally {
      setIsImportingDoc(false);
      e.target.value = "";
    }
  };

  return (
    <div style={{ marginBottom: "20px" }}>
      <p style={{ margin: "0 0 12px 0", color: "#55534e", fontSize: "15px" }}>
        Turn your skills and experience into a clean, ready-to-send resume.
      </p>

      {/* Section anchor shortcuts */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "12px",
          padding: "8px 0",
          borderBottom: "1px solid #d9d5cc",
          marginBottom: "16px",
          fontSize: "14px",
        }}
      >
        <span style={{ fontWeight: 600, color: "#1d1d1b" }}>Jump to:</span>
        <a href="#section-basics">Basics</a>
        <a href="#section-skills">Skills</a>
        <a href="#section-experience">Experience</a>
        <a href="#section-projects">Projects</a>
        <a href="#section-education">Education</a>
        <a href="#section-more">More</a>
        <a href="#section-links">Links</a>
      </div>

      {/* Action controls row */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "10px",
          fontSize: "14px",
        }}
      >
        <label style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
          <span>Template:</span>
          <select
            value={resume.meta.template || "classic"}
            onChange={handleTemplateChange}
            style={{
              padding: "4px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              backgroundColor: "#ffffff",
              fontSize: "14px",
            }}
          >
            <option value="classic">Classic (Serif, ATS-safe)</option>
            <option value="compact">Compact (Sans, 1-page tight)</option>
            <option value="technical">Technical (Skills on top)</option>
          </select>
        </label>

        <label style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
          <span>Paper:</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(e.target.value as "A4" | "Letter")}
            style={{
              padding: "4px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              backgroundColor: "#ffffff",
              fontSize: "14px",
            }}
          >
            <option value="A4">A4</option>
            <option value="Letter">Letter</option>
          </select>
        </label>

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: "1px solid #d9d5cc",
            backgroundColor: "#ffffff",
            padding: "4px 10px",
            borderRadius: "4px",
            fontSize: "14px",
            cursor: "pointer",
          }}
        >
          Load from JSON
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,application/json"
          onChange={handleFileImport}
          style={{ display: "none" }}
        />

        <button
          type="button"
          disabled={isImportingDoc}
          onClick={() => docFileInputRef.current?.click()}
          style={{
            border: "1px solid #d9d5cc",
            backgroundColor: "#ffffff",
            padding: "4px 10px",
            borderRadius: "4px",
            fontSize: "14px",
            cursor: isImportingDoc ? "default" : "pointer",
          }}
        >
          {isImportingDoc ? "Importing document..." : "Start from my uploaded resume"}
        </button>
        <input
          ref={docFileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleDocImport}
          style={{ display: "none" }}
        />

        {hasAnalyzed && (
          <button
            type="button"
            onClick={handleStartFromAnalysis}
            style={{
              border: "1px solid #d9d5cc",
              backgroundColor: "#ffffff",
              padding: "4px 10px",
              borderRadius: "4px",
              fontSize: "14px",
              cursor: "pointer",
            }}
          >
            Start from my analyzed resume
          </button>
        )}

        <button
          type="button"
          onClick={handleClear}
          style={{
            border: "1px solid #d9d5cc",
            backgroundColor: "#ffffff",
            color: "#8b0000",
            padding: "4px 10px",
            borderRadius: "4px",
            fontSize: "14px",
            cursor: "pointer",
            marginLeft: "auto",
          }}
        >
          Clear everything
        </button>
      </div>

      <div
        style={{
          marginTop: "10px",
          fontSize: "12px",
          color: "#55534e",
        }}
      >
        Your resume is saved only in this browser. Clear it any time. Nothing is sent to the server except for processing requests.
      </div>
    </div>
  );
}
