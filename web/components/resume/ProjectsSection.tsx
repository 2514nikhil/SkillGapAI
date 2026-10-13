"use client";

import React, { useState } from "react";
import { ProjectItem, Resume } from "@/lib/resumeTypes";
import { aiPolishProject } from "@/lib/resumeApi";

interface ProjectsSectionProps {
  resume: Resume;
  onChange: (updated: Resume) => void;
  onServerError?: (msg: string | null) => void;
}

export default function ProjectsSection({
  resume,
  onChange,
  onServerError,
}: ProjectsSectionProps) {
  // State for AI polish modal/inline drawer keyed by projIdx
  const [activePolishIdx, setActivePolishIdx] = useState<number | null>(null);
  const [polishNotes, setPolishNotes] = useState("");
  const [isPolishing, setIsPolishing] = useState(false);
  const [polishedBullets, setPolishedBullets] = useState<string[]>([]);
  const [polishError, setPolishError] = useState<string | null>(null);

  const addProject = () => {
    const newItem: ProjectItem = {
      name: "",
      link: "",
      tech: [],
      bullets: [""],
    };
    onChange({
      ...resume,
      projects: [...resume.projects, newItem],
    });
  };

  const removeProject = (index: number) => {
    onChange({
      ...resume,
      projects: resume.projects.filter((_, idx) => idx !== index),
    });
  };

  const moveProject = (index: number, direction: "up" | "down") => {
    const newIdx = direction === "up" ? index - 1 : index + 1;
    if (newIdx < 0 || newIdx >= resume.projects.length) return;
    const items = [...resume.projects];
    const temp = items[index];
    items[index] = items[newIdx];
    items[newIdx] = temp;
    onChange({
      ...resume,
      projects: items,
    });
  };

  const updateProject = (index: number, field: keyof ProjectItem, value: any) => {
    const updated = resume.projects.map((item, idx) => {
      if (idx === index) {
        return { ...item, [field]: value };
      }
      return item;
    });
    onChange({ ...resume, projects: updated });
  };

  const addBullet = (projIndex: number) => {
    const proj = resume.projects[projIndex];
    if (proj.bullets.length >= 8) {
      alert("ATS guidelines recommend a maximum of 8 bullets per project.");
      return;
    }
    const updated = resume.projects.map((item, idx) => {
      if (idx === projIndex) {
        return { ...item, bullets: [...item.bullets, ""] };
      }
      return item;
    });
    onChange({ ...resume, projects: updated });
  };

  const updateBullet = (projIndex: number, bulletIndex: number, text: string) => {
    const updated = resume.projects.map((item, idx) => {
      if (idx === projIndex) {
        const newBullets = [...item.bullets];
        newBullets[bulletIndex] = text;
        return { ...item, bullets: newBullets };
      }
      return item;
    });
    onChange({ ...resume, projects: updated });
  };

  const removeBullet = (projIndex: number, bulletIndex: number) => {
    const updated = resume.projects.map((item, idx) => {
      if (idx === projIndex) {
        return {
          ...item,
          bullets: item.bullets.filter((_, bIdx) => bIdx !== bulletIndex),
        };
      }
      return item;
    });
    onChange({ ...resume, projects: updated });
  };

  const startPolish = (index: number) => {
    setActivePolishIdx(index);
    setPolishNotes("");
    setPolishedBullets([]);
    setPolishError(null);
  };

  const handlePolishSubmit = async (index: number) => {
    const proj = resume.projects[index];
    if (!proj.name.trim()) {
      alert("Please give your project a name first.");
      return;
    }
    if (!polishNotes.trim() || polishNotes.trim().length < 5) {
      alert("Please provide some rough notes about what you built, solved, or delivered.");
      return;
    }

    setIsPolishing(true);
    setPolishError(null);
    try {
      const res = await aiPolishProject(proj.name, proj.tech, polishNotes);
      if (res.bullets && res.bullets.length > 0) {
        setPolishedBullets(res.bullets);
      } else {
        setPolishError("Could not polish bullets from these notes.");
      }
    } catch (err: any) {
      setPolishError(err.message || "Failed to polish project notes with AI.");
      if (onServerError) {
        onServerError("Server not responding. Editing and local auto-save continue to work.");
      }
    } finally {
      setIsPolishing(false);
    }
  };

  const applyPolishedBullets = (index: number) => {
    const proj = resume.projects[index];
    const existing = proj.bullets.filter((b) => b.trim().length > 0);
    const combined = [...existing, ...polishedBullets].slice(0, 8);
    updateProject(index, "bullets", combined);
    setActivePolishIdx(null);
    setPolishedBullets([]);
  };

  return (
    <section id="section-projects" style={{ marginBottom: "28px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #d9d5cc", paddingBottom: "6px", marginBottom: "14px" }}>
        <h2 style={{ fontSize: "18px", fontWeight: 600, margin: 0 }}>
          Projects
        </h2>
        <button
          type="button"
          onClick={addProject}
          style={{
            border: "1px solid #d9d5cc",
            backgroundColor: "#ffffff",
            padding: "4px 10px",
            borderRadius: "4px",
            fontSize: "13px",
            cursor: "pointer",
          }}
        >
          Add project
        </button>
      </div>

      {resume.projects.length === 0 ? (
        <p style={{ margin: 0, fontSize: "14px", color: "#55534e" }}>
          No projects added yet. Click &quot;Add project&quot; to highlight personal, open source, or professional work.
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {resume.projects.map((proj, projIdx) => (
            <div
              key={projIdx}
              style={{
                border: "1px solid #d9d5cc",
                borderRadius: "4px",
                padding: "14px",
                backgroundColor: "#ffffff",
              }}
            >
              {/* Header and ordering */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <span style={{ fontWeight: 600, fontSize: "15px" }}>
                  Project #{projIdx + 1} {proj.name ? `— ${proj.name}` : ""}
                </span>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    type="button"
                    disabled={projIdx === 0}
                    onClick={() => moveProject(projIdx, "up")}
                    style={{
                      border: "1px solid #d9d5cc",
                      backgroundColor: "#ffffff",
                      fontSize: "12px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      cursor: projIdx === 0 ? "default" : "pointer",
                      opacity: projIdx === 0 ? 0.4 : 1,
                    }}
                  >
                    Move up
                  </button>
                  <button
                    type="button"
                    disabled={projIdx === resume.projects.length - 1}
                    onClick={() => moveProject(projIdx, "down")}
                    style={{
                      border: "1px solid #d9d5cc",
                      backgroundColor: "#ffffff",
                      fontSize: "12px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      cursor: projIdx === resume.projects.length - 1 ? "default" : "pointer",
                      opacity: projIdx === resume.projects.length - 1 ? 0.4 : 1,
                    }}
                  >
                    Move down
                  </button>
                  <button
                    type="button"
                    onClick={() => removeProject(projIdx)}
                    style={{
                      border: "1px solid #d9d5cc",
                      backgroundColor: "#ffffff",
                      color: "#8b0000",
                      fontSize: "12px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      cursor: "pointer",
                    }}
                  >
                    Remove
                  </button>
                </div>
              </div>

              {/* Fields: Name, Link, Tech */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "3px" }}>
                    Project Name <span style={{ color: "#8b0000" }}>*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Distributed Task Queue"
                    value={proj.name}
                    onChange={(e) => updateProject(projIdx, "name", e.target.value)}
                    style={{
                      width: "100%",
                      padding: "5px 8px",
                      border: "1px solid #d9d5cc",
                      borderRadius: "4px",
                      fontSize: "14px",
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "3px" }}>
                    Project Link / Repository (optional)
                  </label>
                  <input
                    type="text"
                    placeholder="https://github.com/username/project"
                    value={proj.link || ""}
                    onChange={(e) => updateProject(projIdx, "link", e.target.value)}
                    style={{
                      width: "100%",
                      padding: "5px 8px",
                      border: "1px solid #d9d5cc",
                      borderRadius: "4px",
                      fontSize: "14px",
                    }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "3px" }}>
                  Technologies Used (comma-separated, e.g. Python, Redis, FastAPI)
                </label>
                <input
                  type="text"
                  placeholder="Python, Redis, Docker, PostgreSQL"
                  value={proj.tech.join(", ")}
                  onChange={(e) => {
                    const parsed = e.target.value
                      .split(",")
                      .map((t) => t.trim())
                      .filter(Boolean);
                    updateProject(projIdx, "tech", parsed);
                  }}
                  style={{
                    width: "100%",
                    padding: "5px 8px",
                    border: "1px solid #d9d5cc",
                    borderRadius: "4px",
                    fontSize: "14px",
                  }}
                />
              </div>

              {/* Bullets */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <label style={{ fontSize: "13px", fontWeight: 600 }}>
                    Project Bullets ({proj.bullets.length}/8)
                  </label>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button
                      type="button"
                      onClick={() => startPolish(projIdx)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#2f5d50",
                        textDecoration: "underline",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      Polish project from notes
                    </button>
                    <button
                      type="button"
                      onClick={() => addBullet(projIdx)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#2f5d50",
                        textDecoration: "underline",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      Add bullet
                    </button>
                  </div>
                </div>

                {/* Polish notes drawer */}
                {activePolishIdx === projIdx && (
                  <div
                    style={{
                      marginBottom: "12px",
                      padding: "10px",
                      border: "1px solid #2f5d50",
                      borderRadius: "4px",
                      backgroundColor: "#fffdf9",
                    }}
                  >
                    <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "4px" }}>
                      Polish from your raw notes (AI will not invent tools or outcomes):
                    </div>
                    <textarea
                      rows={3}
                      placeholder="Paste your rough project notes, problem statement, key decisions, or architecture details..."
                      value={polishNotes}
                      onChange={(e) => setPolishNotes(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "6px",
                        border: "1px solid #d9d5cc",
                        borderRadius: "4px",
                        fontSize: "13px",
                        marginBottom: "6px",
                      }}
                    />
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button
                        type="button"
                        onClick={() => handlePolishSubmit(projIdx)}
                        disabled={isPolishing}
                        style={{
                          border: "1px solid #2f5d50",
                          backgroundColor: "#2f5d50",
                          color: "#ffffff",
                          fontSize: "12px",
                          padding: "3px 10px",
                          borderRadius: "3px",
                          cursor: isPolishing ? "default" : "pointer",
                        }}
                      >
                        {isPolishing ? "Polishing..." : "Generate bullets"}
                      </button>
                      <button
                        type="button"
                        onClick={() => setActivePolishIdx(null)}
                        style={{
                          border: "1px solid #d9d5cc",
                          backgroundColor: "#ffffff",
                          fontSize: "12px",
                          padding: "3px 8px",
                          borderRadius: "3px",
                          cursor: "pointer",
                        }}
                      >
                        Cancel
                      </button>
                    </div>

                    {polishError && (
                      <div style={{ fontSize: "12px", color: "#8b0000", marginTop: "4px" }}>
                        {polishError}
                      </div>
                    )}

                    {polishedBullets.length > 0 && (
                      <div style={{ marginTop: "10px", borderTop: "1px dashed #d9d5cc", paddingTop: "8px" }}>
                        <div style={{ fontSize: "12px", fontWeight: 600, marginBottom: "4px" }}>
                          Generated Bullets:
                        </div>
                        <ul style={{ margin: "0 0 8px 18px", padding: 0, fontSize: "13px" }}>
                          {polishedBullets.map((b, idx) => (
                            <li key={idx}>{b}</li>
                          ))}
                        </ul>
                        <button
                          type="button"
                          onClick={() => applyPolishedBullets(projIdx)}
                          style={{
                            border: "1px solid #2f5d50",
                            backgroundColor: "#2f5d50",
                            color: "#ffffff",
                            fontSize: "12px",
                            padding: "3px 8px",
                            borderRadius: "3px",
                            cursor: "pointer",
                          }}
                        >
                          Use these bullets
                        </button>
                      </div>
                    )}
                  </div>
                )}

                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {proj.bullets.map((bullet, bulletIdx) => {
                    const charCount = bullet.length;
                    const isOver = charCount > 300;

                    return (
                      <div key={bulletIdx} style={{ border: "1px solid #ece8e1", padding: "8px", borderRadius: "4px" }}>
                        <div style={{ display: "flex", gap: "6px" }}>
                          <textarea
                            rows={2}
                            value={bullet}
                            placeholder="e.g. Implemented raft consensus algorithm with heartbeat monitoring and automated leader reelection..."
                            onChange={(e) => updateBullet(projIdx, bulletIdx, e.target.value)}
                            style={{
                              flex: 1,
                              padding: "6px",
                              border: isOver ? "1px solid #8b0000" : "1px solid #d9d5cc",
                              borderRadius: "4px",
                              fontSize: "13px",
                              lineHeight: 1.4,
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => removeBullet(projIdx, bulletIdx)}
                            title="Remove bullet"
                            style={{
                              background: "none",
                              border: "none",
                              color: "#8b0000",
                              fontSize: "16px",
                              cursor: "pointer",
                              padding: "0 6px",
                            }}
                          >
                            &times;
                          </button>
                        </div>
                        <div style={{ fontSize: "12px", color: isOver ? "#8b0000" : "#55534e", marginTop: "4px" }}>
                          {charCount} / 300 characters {isOver ? "(exceeds ATS limit)" : ""}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
