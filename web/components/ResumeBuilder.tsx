"use client";

import React, { useEffect, useState } from "react";
import { LintIssue, Resume } from "@/lib/resumeTypes";
import { lintResume } from "@/lib/resumeApi";
import {
  createEmptyResume,
  loadAnalyzedMissingSkills,
  loadResumeFromAnalyzedSession,
  loadResumeFromLocalStorage,
  saveResumeToLocalStorage,
} from "@/lib/resumeStorage";
import Tour from "@/components/Tour";
import { TourStep } from "@/lib/tourUtils";
import ResumeToolbar from "./resume/ResumeToolbar";
import BasicsSection from "./resume/BasicsSection";
import SkillsSection from "./resume/SkillsSection";
import ExperienceSection from "./resume/ExperienceSection";
import ProjectsSection from "./resume/ProjectsSection";
import EducationSection from "./resume/EducationSection";
import MoreSection from "./resume/MoreSection";
import LinksSection from "./resume/LinksSection";
import LivePreview from "./resume/LivePreview";
import LintPanel from "./resume/LintPanel";
import RoleFitPanel from "./resume/RoleFitPanel";

const builderTourSteps: TourStep[] = [
  {
    target: '[data-tour="builder-basics"]',
    title: "Basics & Contact Info",
    body: "Enter your name and email (the only required fields). Photos, dates of birth, and sensitive personal identifiers are strictly forbidden.",
    placement: "bottom",
  },
  {
    target: '[data-tour="builder-skills"]',
    title: "Skills Catalog & Custom Tags",
    body: "Search across 15 technical categories, pin up to 8 core strengths to the top, add proficiency levels, or extract skills directly from your bullet text.",
    placement: "top",
  },
  {
    target: '[data-tour="builder-improve-ai"]',
    title: "Honest AI Bullet Improver",
    body: "Rewrite bullets with strong action verbs. The AI assistant is forbidden from inventing facts, dates, tools, or percentages.",
    placement: "top",
  },
  {
    target: '[data-tour="builder-links"]',
    title: "Links & Online Profiles",
    body: "Add your LinkedIn, GitHub, or portfolio. Preview live URLs and verify handle formats with zero social media icons.",
    placement: "top",
  },
  {
    target: '[data-tour="builder-checks"]',
    title: "Live Quality & ATS Linting",
    body: "Catch weak phrasing, bullet length issues, and missing fields before applying. Click any check to scroll directly to the field.",
    placement: "top",
  },
  {
    target: '[data-tour="builder-role-fit"]',
    title: "Role Fit & Gap Suggestions",
    body: "Evaluate your resume against target roles. See matching scores and discover high-impact skills with 'I have this' buttons.",
    placement: "top",
  },
  {
    target: '[data-tour="builder-download"]',
    title: "Multi-Format Export",
    body: "Export your finished resume directly as PDF, DOCX, Markdown, Text, or JSON. Exports are gated until required fields and errors are resolved.",
    placement: "top",
  },
];

export default function ResumeBuilder() {
  const [resume, setResume] = useState<Resume>(() => createEmptyResume());
  const [isLoaded, setIsLoaded] = useState(false);
  const [pageSize, setPageSize] = useState<"A4" | "Letter">("A4");
  const [lintIssues, setLintIssues] = useState<LintIssue[]>([]);
  const [isLinting, setIsLinting] = useState(false);
  const [serverNotice, setServerNotice] = useState<string | null>(null);

  // Analysis integration: missing skills from sessionStorage
  const [missingSkillsFromAnalysis, setMissingSkillsFromAnalysis] = useState<
    Array<{ skill: string; skill_id: string; tier?: string; impact?: number }>
  >([]);
  const [importReviewNotes, setImportReviewNotes] = useState<
    Array<{ field: string; note: string }>
  >([]);

  // Responsive mobile view toggle: 'editor' | 'preview'
  const [mobileView, setMobileView] = useState<"editor" | "preview">("editor");

  // Read URL params or analysis session on mount, or load from localStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const isFromAnalysis = urlParams.get("from") === "analysis";
      if (isFromAnalysis) {
        const fromSession = loadResumeFromAnalyzedSession();
        if (fromSession) {
          setResume(fromSession);
        }
        const missing = loadAnalyzedMissingSkills();
        setMissingSkillsFromAnalysis(missing);
      } else {
        const saved = loadResumeFromLocalStorage();
        if (saved) {
          setResume(saved);
        }
      }
      setIsLoaded(true);
    }
  }, []);

  // Autosave to localStorage only after initial client load
  useEffect(() => {
    if (isLoaded) {
      saveResumeToLocalStorage(resume);
    }
  }, [resume, isLoaded]);

  // Debounced linting (400ms)
  useEffect(() => {
    let active = true;
    const timer = setTimeout(async () => {
      setIsLinting(true);
      try {
        const issues = await lintResume(resume);
        if (active && Array.isArray(issues)) {
          setLintIssues(issues);
          setServerNotice(null);
        }
      } catch (err: any) {
        if (active) {
          setServerNotice("Server not responding. Editing and local auto-save continue to work.");
        }
      } finally {
        if (active) {
          setIsLinting(false);
        }
      }
    }, 400);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [resume]);

  // Expand page container on mount for widescreen 2-column layout
  useEffect(() => {
    const mainEl = document.querySelector("main.container");
    if (mainEl) {
      mainEl.classList.add("container-wide");
      return () => {
        mainEl.classList.remove("container-wide");
      };
    }
  }, []);

  return (
    <div className="resume-builder-root" style={{ width: "100%", margin: "0 auto" }}>
      <Tour steps={builderTourSteps} storageKey="skillgap_tour_builder_v1" />

      {/* Server Offline / Downtime notice */}
      {serverNotice && (
        <div
          style={{
            border: "1px solid #d9d5cc",
            backgroundColor: "#fffdf9",
            color: "#8b0000",
            padding: "8px 12px",
            borderRadius: "4px",
            marginBottom: "16px",
            fontSize: "13px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>{serverNotice}</span>
          <button
            type="button"
            onClick={() => setServerNotice(null)}
            style={{
              background: "none",
              border: "none",
              color: "#55534e",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            &times;
          </button>
        </div>
      )}

      {/* Top Toolbar */}
      <ResumeToolbar
        resume={resume}
        onChange={setResume}
        pageSize={pageSize}
        onPageSizeChange={setPageSize}
        onImportReviewNotes={setImportReviewNotes}
      />

      {/* Review Notes from Uploaded Resume Import */}
      {importReviewNotes.length > 0 && (
        <div
          style={{
            border: "1px solid #d9d5cc",
            backgroundColor: "#fffdf9",
            borderRadius: "4px",
            padding: "12px 14px",
            marginBottom: "16px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
            <span style={{ fontSize: "14px", fontWeight: 600 }}>
              Resume imported. Please review the following notes:
            </span>
            <button
              type="button"
              onClick={() => setImportReviewNotes([])}
              style={{
                background: "none",
                border: "none",
                fontSize: "12px",
                color: "#55534e",
                cursor: "pointer",
              }}
            >
              &times; Dismiss
            </button>
          </div>
          <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "13px", color: "#55534e" }}>
            {importReviewNotes.map((note, idx) => (
              <li key={idx}>
                <strong>{note.field}</strong>: {note.note}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing Skills from Analyzer Box */}
      {missingSkillsFromAnalysis.length > 0 && (
        <div
          style={{
            border: "1px solid #2f5d50",
            backgroundColor: "#fffdf9",
            borderRadius: "4px",
            padding: "14px",
            marginBottom: "20px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontSize: "14px", fontWeight: 600, color: "#2f5d50" }}>
              Skills the role asks for. Add only the ones you really have ({missingSkillsFromAnalysis.length}):
            </span>
            <button
              type="button"
              onClick={() => setMissingSkillsFromAnalysis([])}
              style={{
                background: "none",
                border: "none",
                fontSize: "12px",
                color: "#55534e",
                cursor: "pointer",
                textDecoration: "underline",
              }}
            >
              Dismiss
            </button>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {missingSkillsFromAnalysis.map((m) => (
              <div
                key={m.skill_id || m.skill}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  border: "1px solid #d9d5cc",
                  backgroundColor: "#ffffff",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontSize: "13px",
                }}
              >
                <span>{m.skill}</span>
                <button
                  type="button"
                  onClick={() => {
                    const exists = resume.skills.some(
                      (s) => s.name.toLowerCase() === m.skill.toLowerCase()
                    );
                    if (!exists) {
                      const newSkill = {
                        category_id: "other_tools",
                        name: m.skill,
                        taxonomy_id: m.skill_id || null,
                        custom: false,
                        pinned: false,
                      };
                      setResume((prev) => ({
                        ...prev,
                        skills: [...prev.skills, newSkill],
                      }));
                    }
                    setMissingSkillsFromAnalysis((prev) =>
                      prev.filter(
                        (item) => (item.skill_id || item.skill) !== (m.skill_id || m.skill)
                      )
                    );
                  }}
                  style={{
                    border: "1px solid #2f5d50",
                    backgroundColor: "#2f5d50",
                    color: "#ffffff",
                    fontSize: "11px",
                    padding: "2px 6px",
                    borderRadius: "3px",
                    cursor: "pointer",
                  }}
                >
                  I have this
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Narrow screen view switcher (< 1100px) */}
      <div className="resume-builder-mobile-toggle" style={{ marginBottom: "16px" }}>
        <button
          type="button"
          onClick={() => setMobileView(mobileView === "editor" ? "preview" : "editor")}
          style={{
            border: "1px solid #2f5d50",
            backgroundColor: "#ffffff",
            color: "#2f5d50",
            padding: "6px 14px",
            borderRadius: "4px",
            fontSize: "14px",
            cursor: "pointer",
            fontWeight: 500,
          }}
        >
          {mobileView === "editor" ? "Show preview" : "Back to editing"}
        </button>
      </div>

      {/* Main 2-column or 1-column layout */}
      <div className="resume-builder-grid">
        {/* Left Form Column */}
        <div
          className={`resume-builder-form ${mobileView === "preview" ? "mobile-hidden" : ""}`}
        >
          <div data-tour="builder-basics">
            <BasicsSection
              resume={resume}
              onChange={setResume}
              onServerError={setServerNotice}
            />
          </div>
          <div data-tour="builder-skills">
            <SkillsSection
              resume={resume}
              onChange={setResume}
              onServerError={setServerNotice}
            />
          </div>
          <div data-tour="builder-improve-ai">
            <ExperienceSection
              resume={resume}
              onChange={setResume}
              onServerError={setServerNotice}
            />
          </div>
          <ProjectsSection
            resume={resume}
            onChange={setResume}
            onServerError={setServerNotice}
          />
          <EducationSection
            resume={resume}
            onChange={setResume}
          />
          <MoreSection
            resume={resume}
            onChange={setResume}
          />
          <div data-tour="builder-links">
            <LinksSection
              resume={resume}
              onChange={setResume}
              onServerError={setServerNotice}
            />
          </div>
        </div>

        {/* Right Sticky Preview & Quality Column */}
        <div
          className={`resume-builder-preview ${mobileView === "editor" ? "mobile-hidden" : ""}`}
        >
          <div data-tour="builder-checks">
            <LintPanel issues={lintIssues} isLoading={isLinting} />
          </div>
          <div data-tour="builder-role-fit">
            <RoleFitPanel
              resume={resume}
              onChange={setResume}
              onServerError={setServerNotice}
            />
          </div>
          <div data-tour="builder-download">
            <LivePreview
              resume={resume}
              pageSize={pageSize}
              lintIssues={lintIssues}
              onServerError={setServerNotice}
            />
          </div>
        </div>
      </div>

      <style jsx>{`
        .resume-builder-grid {
          display: grid;
          grid-template-columns: minmax(0, 600px) minmax(440px, 1fr);
          gap: 32px;
          align-items: start;
        }
        .resume-builder-form {
          max-width: 600px;
          width: 100%;
        }
        .resume-builder-preview {
          width: 100%;
          position: sticky;
          top: 16px;
          max-height: calc(100vh - 32px);
          overflow-y: auto;
          padding-right: 4px;
        }
        .resume-builder-mobile-toggle {
          display: none;
        }
        @media (max-width: 1099px) {
          .resume-builder-grid {
            display: block;
          }
          .resume-builder-form {
            max-width: 100%;
          }
          .resume-builder-preview {
            position: static;
            max-height: none;
            overflow-y: visible;
            padding-right: 0;
            margin-top: 16px;
          }
          .resume-builder-mobile-toggle {
            display: block;
          }
          .mobile-hidden {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
