"use client";

import React, { useState } from "react";
import { Resume, SkillItem, TailorResponse } from "@/lib/resumeTypes";
import { aiTailor } from "@/lib/resumeApi";

interface RoleFitPanelProps {
  resume: Resume;
  onChange: (updated: Resume) => void;
  onServerError?: (msg: string | null) => void;
}

export default function RoleFitPanel({
  resume,
  onChange,
  onServerError,
}: RoleFitPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [targetInput, setTargetInput] = useState(resume.meta.target_role || "");
  const [isLoading, setIsLoading] = useState(false);
  const [tailorResult, setTailorResult] = useState<TailorResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCheckFit = async () => {
    const role = targetInput.trim() || resume.meta.target_role?.trim();
    if (!role) {
      alert("Please enter a target role name to analyze fit against.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const res = await aiTailor(resume, role);
      setTailorResult(res);
      setIsOpen(true);
    } catch (err: any) {
      setError(err.message || "Failed to analyze role fit.");
      if (onServerError) {
        onServerError("Server not responding. Editing and local auto-save continue to work.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddMissingSkill = (name: string, taxonomyId: string) => {
    const exists = resume.skills.some((s) => s.name.toLowerCase() === name.toLowerCase());
    if (exists) return;

    const newSkill: SkillItem = {
      category_id: "other_tools",
      name,
      taxonomy_id: taxonomyId || null,
      custom: false,
      pinned: false,
    };

    onChange({
      ...resume,
      skills: [...resume.skills, newSkill],
    });

    if (tailorResult) {
      setTailorResult({
        ...tailorResult,
        missing: tailorResult.missing.filter((m) => m.name.toLowerCase() !== name.toLowerCase()),
        covered: [
          ...tailorResult.covered,
          { name, taxonomy_id: taxonomyId, importance: "required" },
        ],
      });
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
          Role Fit Analyzer
          {tailorResult && (
            <span style={{ marginLeft: "8px", color: "#2f5d50" }}>
              (Score: {tailorResult.score}%)
            </span>
          )}
        </span>
        <span style={{ fontSize: "13px", color: "#55534e" }}>
          {isOpen ? "[Hide]" : "[Show]"}
        </span>
      </div>

      {isOpen && (
        <div style={{ padding: "12px 14px", fontSize: "13px" }}>
          <p style={{ margin: "0 0 10px 0", color: "#55534e" }}>
            Compare your resume against a target job role. See covered skills and high-impact missing requirements.
          </p>

          <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
            <input
              type="text"
              placeholder="e.g. Backend Developer"
              value={targetInput}
              onChange={(e) => setTargetInput(e.target.value)}
              style={{
                flex: 1,
                padding: "5px 8px",
                border: "1px solid #d9d5cc",
                borderRadius: "4px",
                fontSize: "14px",
              }}
            />
            <button
              type="button"
              onClick={handleCheckFit}
              disabled={isLoading}
              style={{
                border: "1px solid #2f5d50",
                backgroundColor: "#2f5d50",
                color: "#ffffff",
                padding: "5px 12px",
                borderRadius: "4px",
                fontSize: "13px",
                cursor: isLoading ? "default" : "pointer",
              }}
            >
              {isLoading ? "Checking fit..." : "Check fit"}
            </button>
          </div>

          {error && (
            <div style={{ color: "#8b0000", marginBottom: "8px" }}>
              {error}
            </div>
          )}

          {tailorResult && (
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  gap: "10px",
                  padding: "8px",
                  backgroundColor: "#faf8f4",
                  borderRadius: "4px",
                  marginBottom: "12px",
                }}
              >
                <div style={{ fontSize: "20px", fontWeight: 700, color: "#2f5d50" }}>
                  {tailorResult.score}%
                </div>
                <div style={{ color: "#55534e" }}>
                  Estimated match for <strong>{tailorResult.target_role}</strong>.
                  {tailorResult.suggest_only && " Suggestions are preview only; no changes are made automatically."}
                </div>
              </div>

              {/* Missing skills */}
              <div style={{ marginBottom: "12px" }}>
                <div style={{ fontWeight: 600, marginBottom: "6px" }}>
                  Missing High-Impact Skills ({tailorResult.missing.length}):
                </div>
                {tailorResult.missing.length === 0 ? (
                  <div style={{ color: "#2f5d50" }}>No major skill gaps found!</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    {tailorResult.missing.map((sk) => (
                      <div
                        key={sk.name}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          padding: "4px 0",
                          borderBottom: "1px dashed #ece8e1",
                        }}
                      >
                        <div>
                          <strong>{sk.name}</strong>
                          <span style={{ fontSize: "11px", color: "#8b0000", marginLeft: "6px" }}>
                            [{sk.tier} impact, +{sk.impact}pts]
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleAddMissingSkill(sk.name, sk.taxonomy_id)}
                          style={{
                            border: "1px solid #2f5d50",
                            backgroundColor: "#ffffff",
                            color: "#2f5d50",
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
                )}
              </div>

              {/* Covered skills */}
              <div>
                <div style={{ fontWeight: 600, marginBottom: "4px" }}>
                  Covered Skills ({tailorResult.covered.length}):
                </div>
                <div style={{ color: "#55534e", fontSize: "12px" }}>
                  {tailorResult.covered.map((c) => c.name).join(", ") || "None"}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
