"use client";

import React, { useState } from "react";
import {
  AIImproveBulletResponse,
  ExperienceItem,
  Resume,
} from "@/lib/resumeTypes";
import { aiImproveBullet } from "@/lib/resumeApi";

interface ExperienceSectionProps {
  resume: Resume;
  onChange: (updated: Resume) => void;
  onServerError?: (msg: string | null) => void;
}

export default function ExperienceSection({
  resume,
  onChange,
  onServerError,
}: ExperienceSectionProps) {
  // Keyed state for AI improve popovers: `${expIdx}-${bulletIdx}`
  const [improvingKey, setImprovingKey] = useState<string | null>(null);
  const [variantsByKey, setVariantsByKey] = useState<Record<string, AIImproveBulletResponse>>({});
  const [errorByKey, setErrorByKey] = useState<Record<string, string>>({});

  const addPosition = () => {
    const newItem: ExperienceItem = {
      company: "",
      title: "",
      location: "",
      start: "",
      end: "",
      current: false,
      bullets: [""],
    };
    onChange({
      ...resume,
      experience: [...resume.experience, newItem],
    });
  };

  const removePosition = (index: number) => {
    onChange({
      ...resume,
      experience: resume.experience.filter((_, idx) => idx !== index),
    });
  };

  const movePosition = (index: number, direction: "up" | "down") => {
    const newIdx = direction === "up" ? index - 1 : index + 1;
    if (newIdx < 0 || newIdx >= resume.experience.length) return;
    const items = [...resume.experience];
    const temp = items[index];
    items[index] = items[newIdx];
    items[newIdx] = temp;
    onChange({
      ...resume,
      experience: items,
    });
  };

  const updatePosition = (index: number, field: keyof ExperienceItem, value: any) => {
    const updated = resume.experience.map((item, idx) => {
      if (idx === index) {
        return { ...item, [field]: value };
      }
      return item;
    });
    onChange({ ...resume, experience: updated });
  };

  const addBullet = (expIndex: number) => {
    const exp = resume.experience[expIndex];
    if (exp.bullets.length >= 8) {
      alert("ATS guidelines recommend a maximum of 8 bullets per role.");
      return;
    }
    const updated = resume.experience.map((item, idx) => {
      if (idx === expIndex) {
        return { ...item, bullets: [...item.bullets, ""] };
      }
      return item;
    });
    onChange({ ...resume, experience: updated });
  };

  const updateBullet = (expIndex: number, bulletIndex: number, text: string) => {
    const updated = resume.experience.map((item, idx) => {
      if (idx === expIndex) {
        const newBullets = [...item.bullets];
        newBullets[bulletIndex] = text;
        return { ...item, bullets: newBullets };
      }
      return item;
    });
    onChange({ ...resume, experience: updated });
  };

  const removeBullet = (expIndex: number, bulletIndex: number) => {
    const updated = resume.experience.map((item, idx) => {
      if (idx === expIndex) {
        return {
          ...item,
          bullets: item.bullets.filter((_, bIdx) => bIdx !== bulletIndex),
        };
      }
      return item;
    });
    onChange({ ...resume, experience: updated });
  };

  const handleImproveBullet = async (expIndex: number, bulletIndex: number) => {
    const exp = resume.experience[expIndex];
    const text = exp.bullets[bulletIndex]?.trim();
    if (!text || text.length < 5) {
      alert("Please write at least a few words before improving with AI.");
      return;
    }

    const key = `${expIndex}-${bulletIndex}`;
    setImprovingKey(key);
    setErrorByKey((prev) => ({ ...prev, [key]: "" }));

    try {
      const skillsContext = resume.skills.map((s) => s.name);
      const res = await aiImproveBullet(text, {
        role: exp.title,
        company: exp.company,
        skills: skillsContext,
      });
      setVariantsByKey((prev) => ({ ...prev, [key]: res }));
    } catch (err: any) {
      setErrorByKey((prev) => ({
        ...prev,
        [key]: err.message || "Failed to generate AI variants.",
      }));
      if (onServerError) {
        onServerError("Server not responding. Editing and local auto-save continue to work.");
      }
    } finally {
      setImprovingKey(null);
    }
  };

  const applyVariant = (expIndex: number, bulletIndex: number, variantText: string) => {
    updateBullet(expIndex, bulletIndex, variantText);
    const key = `${expIndex}-${bulletIndex}`;
    setVariantsByKey((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const dismissVariants = (expIndex: number, bulletIndex: number) => {
    const key = `${expIndex}-${bulletIndex}`;
    setVariantsByKey((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  return (
    <section id="section-experience" style={{ marginBottom: "28px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #d9d5cc", paddingBottom: "6px", marginBottom: "14px" }}>
        <h2 style={{ fontSize: "18px", fontWeight: 600, margin: 0 }}>
          Work Experience
        </h2>
        <button
          type="button"
          onClick={addPosition}
          style={{
            border: "1px solid #d9d5cc",
            backgroundColor: "#ffffff",
            padding: "4px 10px",
            borderRadius: "4px",
            fontSize: "13px",
            cursor: "pointer",
          }}
        >
          Add position
        </button>
      </div>

      {resume.experience.length === 0 ? (
        <p style={{ margin: 0, fontSize: "14px", color: "#55534e" }}>
          No work experience added yet. Click &quot;Add position&quot; above to add your employment history.
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {resume.experience.map((exp, expIdx) => (
            <div
              key={expIdx}
              style={{
                border: "1px solid #d9d5cc",
                borderRadius: "4px",
                padding: "14px",
                backgroundColor: "#ffffff",
              }}
            >
              {/* Header and ordering actions */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <span style={{ fontWeight: 600, fontSize: "15px" }}>
                  Position #{expIdx + 1} {exp.title ? `— ${exp.title}` : ""}
                </span>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    type="button"
                    disabled={expIdx === 0}
                    onClick={() => movePosition(expIdx, "up")}
                    style={{
                      border: "1px solid #d9d5cc",
                      backgroundColor: "#ffffff",
                      fontSize: "12px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      cursor: expIdx === 0 ? "default" : "pointer",
                      opacity: expIdx === 0 ? 0.4 : 1,
                    }}
                  >
                    Move up
                  </button>
                  <button
                    type="button"
                    disabled={expIdx === resume.experience.length - 1}
                    onClick={() => movePosition(expIdx, "down")}
                    style={{
                      border: "1px solid #d9d5cc",
                      backgroundColor: "#ffffff",
                      fontSize: "12px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      cursor: expIdx === resume.experience.length - 1 ? "default" : "pointer",
                      opacity: expIdx === resume.experience.length - 1 ? 0.4 : 1,
                    }}
                  >
                    Move down
                  </button>
                  <button
                    type="button"
                    onClick={() => removePosition(expIdx)}
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

              {/* Main Fields */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "3px" }}>
                    Company Name <span style={{ color: "#8b0000" }}>*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Acme Corp"
                    value={exp.company}
                    onChange={(e) => updatePosition(expIdx, "company", e.target.value)}
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
                    Job Title <span style={{ color: "#8b0000" }}>*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Software Engineer"
                    value={exp.title}
                    onChange={(e) => updatePosition(expIdx, "title", e.target.value)}
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

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", marginBottom: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "3px" }}>
                    Location
                  </label>
                  <input
                    type="text"
                    placeholder="San Francisco, CA"
                    value={exp.location || ""}
                    onChange={(e) => updatePosition(expIdx, "location", e.target.value)}
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
                    Start Date (YYYY-MM)
                  </label>
                  <input
                    type="text"
                    placeholder="2021-06"
                    value={exp.start || ""}
                    onChange={(e) => updatePosition(expIdx, "start", e.target.value)}
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
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "3px" }}>
                    <label style={{ fontSize: "13px", fontWeight: 500 }}>
                      End Date
                    </label>
                    <label style={{ fontSize: "12px", display: "inline-flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
                      <input
                        type="checkbox"
                        checked={exp.current || false}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          updatePosition(expIdx, "current", checked);
                          if (checked) {
                            updatePosition(expIdx, "end", "Present");
                          } else if (exp.end === "Present") {
                            updatePosition(expIdx, "end", "");
                          }
                        }}
                      />
                      <span>Current</span>
                    </label>
                  </div>
                  <input
                    type="text"
                    placeholder="Present or 2024-01"
                    disabled={exp.current}
                    value={exp.end || ""}
                    onChange={(e) => updatePosition(expIdx, "end", e.target.value)}
                    style={{
                      width: "100%",
                      padding: "5px 8px",
                      border: "1px solid #d9d5cc",
                      borderRadius: "4px",
                      fontSize: "14px",
                      backgroundColor: exp.current ? "#f5f5f5" : "#ffffff",
                    }}
                  />
                </div>
              </div>

              {/* Bullets */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <label style={{ fontSize: "13px", fontWeight: 600 }}>
                    Accomplishment Bullets ({exp.bullets.length}/8)
                  </label>
                  <button
                    type="button"
                    onClick={() => addBullet(expIdx)}
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

                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {exp.bullets.map((bullet, bulletIdx) => {
                    const charCount = bullet.length;
                    const isOver = charCount > 300;
                    const key = `${expIdx}-${bulletIdx}`;
                    const isImproving = improvingKey === key;
                    const variantData = variantsByKey[key];
                    const error = errorByKey[key];

                    return (
                      <div key={bulletIdx} style={{ border: "1px solid #ece8e1", padding: "8px", borderRadius: "4px" }}>
                        <div style={{ display: "flex", gap: "6px" }}>
                          <textarea
                            rows={2}
                            value={bullet}
                            placeholder="e.g. Architected streaming pipeline reducing data ingestion latency by 45% using Kafka and Go..."
                            onChange={(e) => updateBullet(expIdx, bulletIdx, e.target.value)}
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
                            onClick={() => removeBullet(expIdx, bulletIdx)}
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

                        {/* Counter and AI improve button row */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "4px" }}>
                          <span style={{ fontSize: "12px", color: isOver ? "#8b0000" : "#55534e", fontWeight: isOver ? 600 : 400 }}>
                            {charCount} / 300 characters {isOver ? "(exceeds ATS limit)" : ""}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleImproveBullet(expIdx, bulletIdx)}
                            disabled={isImproving}
                            style={{
                              background: "none",
                              border: "none",
                              color: "#2f5d50",
                              textDecoration: "underline",
                              fontSize: "12px",
                              cursor: isImproving ? "default" : "pointer",
                            }}
                          >
                            {isImproving ? "Improving bullet..." : "Improve with AI"}
                          </button>
                        </div>

                        {error && (
                          <div style={{ fontSize: "12px", color: "#8b0000", marginTop: "4px" }}>
                            {error}
                          </div>
                        )}

                        {/* Inline AI Variants */}
                        {variantData && variantData.variants && variantData.variants.length > 0 && (
                          <div
                            style={{
                              marginTop: "8px",
                              padding: "8px",
                              backgroundColor: "#fffdf9",
                              border: "1px solid #d9d5cc",
                              borderRadius: "4px",
                            }}
                          >
                            <div style={{ fontSize: "12px", fontWeight: 600, marginBottom: "6px" }}>
                              Suggested ATS Variations (Source: {variantData.source}):
                            </div>
                            {variantData.variants.map((v, vIdx) => (
                              <div
                                key={vIdx}
                                style={{
                                  marginBottom: vIdx < variantData.variants.length - 1 ? "8px" : "0",
                                  paddingBottom: vIdx < variantData.variants.length - 1 ? "6px" : "0",
                                  borderBottom: vIdx < variantData.variants.length - 1 ? "1px dashed #d9d5cc" : "none",
                                }}
                              >
                                <p style={{ margin: "0 0 4px 0", fontSize: "13px" }}>
                                  {v.text}
                                </p>
                                {v.changes && v.changes.length > 0 && (
                                  <div style={{ fontSize: "11px", color: "#55534e", marginBottom: "4px" }}>
                                    <em>What changed: {v.changes.join("; ")}</em>
                                  </div>
                                )}
                                <div style={{ display: "flex", gap: "6px" }}>
                                  <button
                                    type="button"
                                    onClick={() => applyVariant(expIdx, bulletIdx, v.text)}
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
                                    Use this
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => dismissVariants(expIdx, bulletIdx)}
                                    style={{
                                      border: "1px solid #d9d5cc",
                                      backgroundColor: "#ffffff",
                                      fontSize: "11px",
                                      padding: "2px 6px",
                                      borderRadius: "3px",
                                      cursor: "pointer",
                                    }}
                                  >
                                    Dismiss
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
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
