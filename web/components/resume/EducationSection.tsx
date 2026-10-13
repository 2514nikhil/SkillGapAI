"use client";

import React from "react";
import { EducationItem, Resume } from "@/lib/resumeTypes";

interface EducationSectionProps {
  resume: Resume;
  onChange: (updated: Resume) => void;
}

export default function EducationSection({
  resume,
  onChange,
}: EducationSectionProps) {
  const addEducation = () => {
    const newItem: EducationItem = {
      school: "",
      degree: "",
      field: "",
      start: "",
      end: "",
      score: "",
      details: [],
    };
    onChange({
      ...resume,
      education: [...resume.education, newItem],
    });
  };

  const removeEducation = (index: number) => {
    onChange({
      ...resume,
      education: resume.education.filter((_, idx) => idx !== index),
    });
  };

  const moveEducation = (index: number, direction: "up" | "down") => {
    const newIdx = direction === "up" ? index - 1 : index + 1;
    if (newIdx < 0 || newIdx >= resume.education.length) return;
    const items = [...resume.education];
    const temp = items[index];
    items[index] = items[newIdx];
    items[newIdx] = temp;
    onChange({
      ...resume,
      education: items,
    });
  };

  const updateEducation = (index: number, field: keyof EducationItem, value: any) => {
    const updated = resume.education.map((item, idx) => {
      if (idx === index) {
        return { ...item, [field]: value };
      }
      return item;
    });
    onChange({ ...resume, education: updated });
  };

  return (
    <section id="section-education" style={{ marginBottom: "28px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #d9d5cc", paddingBottom: "6px", marginBottom: "14px" }}>
        <h2 style={{ fontSize: "18px", fontWeight: 600, margin: 0 }}>
          Education
        </h2>
        <button
          type="button"
          onClick={addEducation}
          style={{
            border: "1px solid #d9d5cc",
            backgroundColor: "#ffffff",
            padding: "4px 10px",
            borderRadius: "4px",
            fontSize: "13px",
            cursor: "pointer",
          }}
        >
          Add education
        </button>
      </div>

      {resume.education.length === 0 ? (
        <p style={{ margin: 0, fontSize: "14px", color: "#55534e" }}>
          No education added yet. Click &quot;Add education&quot; to include university degrees or diplomas.
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {resume.education.map((edu, eduIdx) => (
            <div
              key={eduIdx}
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
                  School #{eduIdx + 1} {edu.school ? `— ${edu.school}` : ""}
                </span>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    type="button"
                    disabled={eduIdx === 0}
                    onClick={() => moveEducation(eduIdx, "up")}
                    style={{
                      border: "1px solid #d9d5cc",
                      backgroundColor: "#ffffff",
                      fontSize: "12px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      cursor: eduIdx === 0 ? "default" : "pointer",
                      opacity: eduIdx === 0 ? 0.4 : 1,
                    }}
                  >
                    Move up
                  </button>
                  <button
                    type="button"
                    disabled={eduIdx === resume.education.length - 1}
                    onClick={() => moveEducation(eduIdx, "down")}
                    style={{
                      border: "1px solid #d9d5cc",
                      backgroundColor: "#ffffff",
                      fontSize: "12px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      cursor: eduIdx === resume.education.length - 1 ? "default" : "pointer",
                      opacity: eduIdx === resume.education.length - 1 ? 0.4 : 1,
                    }}
                  >
                    Move down
                  </button>
                  <button
                    type="button"
                    onClick={() => removeEducation(eduIdx)}
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

              {/* Institution and Degree */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "3px" }}>
                    Institution / University <span style={{ color: "#8b0000" }}>*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="University of California, Berkeley"
                    value={edu.school}
                    onChange={(e) => updateEducation(eduIdx, "school", e.target.value)}
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
                    Degree
                  </label>
                  <input
                    type="text"
                    placeholder="Bachelor of Science"
                    value={edu.degree || ""}
                    onChange={(e) => updateEducation(eduIdx, "degree", e.target.value)}
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

              {/* Field, Start, End, Score */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "10px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "3px" }}>
                    Field of Study
                  </label>
                  <input
                    type="text"
                    placeholder="Computer Science"
                    value={edu.field || ""}
                    onChange={(e) => updateEducation(eduIdx, "field", e.target.value)}
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
                    Start (YYYY)
                  </label>
                  <input
                    type="text"
                    placeholder="2018"
                    value={edu.start || ""}
                    onChange={(e) => updateEducation(eduIdx, "start", e.target.value)}
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
                    End (YYYY)
                  </label>
                  <input
                    type="text"
                    placeholder="2022"
                    value={edu.end || ""}
                    onChange={(e) => updateEducation(eduIdx, "end", e.target.value)}
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
                    GPA / Score (optional)
                  </label>
                  <input
                    type="text"
                    placeholder="3.8 / 4.0"
                    value={edu.score || ""}
                    onChange={(e) => updateEducation(eduIdx, "score", e.target.value)}
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
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
