"use client";

import React, { useState } from "react";
import {
  CertificationItem,
  CustomSectionItem,
  PublicationItem,
  Resume,
} from "@/lib/resumeTypes";

interface MoreSectionProps {
  resume: Resume;
  onChange: (updated: Resume) => void;
}

export default function MoreSection({ resume, onChange }: MoreSectionProps) {
  // Local visibility toggles
  const [showCerts, setShowCerts] = useState(
    (resume.certifications && resume.certifications.length > 0) || false
  );
  const [showPubs, setShowPubs] = useState(
    (resume.publications && resume.publications.length > 0) || false
  );
  const [showAchievements, setShowAchievements] = useState(
    (resume.achievements && resume.achievements.length > 0) || false
  );
  const [showCustom, setShowCustom] = useState(
    (resume.custom_sections && resume.custom_sections.length > 0) || false
  );

  // Certifications handlers
  const addCert = () => {
    const certs = resume.certifications || [];
    onChange({
      ...resume,
      certifications: [...certs, { name: "", issuer: "", date: "" }],
    });
  };

  const updateCert = (idx: number, field: keyof CertificationItem, val: string) => {
    const certs = [...(resume.certifications || [])];
    certs[idx] = { ...certs[idx], [field]: val };
    onChange({ ...resume, certifications: certs });
  };

  const removeCert = (idx: number) => {
    const certs = (resume.certifications || []).filter((_, i) => i !== idx);
    onChange({ ...resume, certifications: certs });
  };

  // Publications handlers
  const addPub = () => {
    const pubs = resume.publications || [];
    onChange({
      ...resume,
      publications: [...pubs, { title: "", venue: "", year: "", link: "" }],
    });
  };

  const updatePub = (idx: number, field: keyof PublicationItem, val: string) => {
    const pubs = [...(resume.publications || [])];
    pubs[idx] = { ...pubs[idx], [field]: val };
    onChange({ ...resume, publications: pubs });
  };

  const removePub = (idx: number) => {
    const pubs = (resume.publications || []).filter((_, i) => i !== idx);
    onChange({ ...resume, publications: pubs });
  };

  // Achievements handlers
  const addAchievement = () => {
    const achs = resume.achievements || [];
    onChange({
      ...resume,
      achievements: [...achs, ""],
    });
  };

  const updateAchievement = (idx: number, val: string) => {
    const achs = [...(resume.achievements || [])];
    achs[idx] = val;
    onChange({ ...resume, achievements: achs });
  };

  const removeAchievement = (idx: number) => {
    const achs = (resume.achievements || []).filter((_, i) => i !== idx);
    onChange({ ...resume, achievements: achs });
  };

  // Custom sections handlers
  const addCustomSection = () => {
    const customs = resume.custom_sections || [];
    onChange({
      ...resume,
      custom_sections: [...customs, { title: "Leadership & Activities", bullets: [""] }],
    });
  };

  const updateCustomSectionTitle = (idx: number, title: string) => {
    const customs = [...(resume.custom_sections || [])];
    customs[idx] = { ...customs[idx], title };
    onChange({ ...resume, custom_sections: customs });
  };

  const addCustomBullet = (secIdx: number) => {
    const customs = [...(resume.custom_sections || [])];
    customs[secIdx] = {
      ...customs[secIdx],
      bullets: [...customs[secIdx].bullets, ""],
    };
    onChange({ ...resume, custom_sections: customs });
  };

  const updateCustomBullet = (secIdx: number, bulletIdx: number, val: string) => {
    const customs = [...(resume.custom_sections || [])];
    const b = [...customs[secIdx].bullets];
    b[bulletIdx] = val;
    customs[secIdx] = { ...customs[secIdx], bullets: b };
    onChange({ ...resume, custom_sections: customs });
  };

  const removeCustomBullet = (secIdx: number, bulletIdx: number) => {
    const customs = [...(resume.custom_sections || [])];
    customs[secIdx] = {
      ...customs[secIdx],
      bullets: customs[secIdx].bullets.filter((_, i) => i !== bulletIdx),
    };
    onChange({ ...resume, custom_sections: customs });
  };

  const removeCustomSection = (idx: number) => {
    const customs = (resume.custom_sections || []).filter((_, i) => i !== idx);
    onChange({ ...resume, custom_sections: customs });
  };

  return (
    <section id="section-more" style={{ marginBottom: "28px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, borderBottom: "1px solid #d9d5cc", paddingBottom: "6px", marginBottom: "14px" }}>
        More Sections
      </h2>

      {/* Section visibility checkboxes */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "16px", marginBottom: "16px", fontSize: "14px" }}>
        <label style={{ display: "inline-flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={showCerts}
            onChange={(e) => {
              setShowCerts(e.target.checked);
              if (e.target.checked && (!resume.certifications || resume.certifications.length === 0)) {
                addCert();
              }
            }}
          />
          <span>Certifications</span>
        </label>

        <label style={{ display: "inline-flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={showPubs}
            onChange={(e) => {
              setShowPubs(e.target.checked);
              if (e.target.checked && (!resume.publications || resume.publications.length === 0)) {
                addPub();
              }
            }}
          />
          <span>Publications</span>
        </label>

        <label style={{ display: "inline-flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={showAchievements}
            onChange={(e) => {
              setShowAchievements(e.target.checked);
              if (e.target.checked && (!resume.achievements || resume.achievements.length === 0)) {
                addAchievement();
              }
            }}
          />
          <span>Achievements</span>
        </label>

        <label style={{ display: "inline-flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={showCustom}
            onChange={(e) => {
              setShowCustom(e.target.checked);
              if (e.target.checked && (!resume.custom_sections || resume.custom_sections.length === 0)) {
                addCustomSection();
              }
            }}
          />
          <span>Custom Section</span>
        </label>
      </div>

      {/* Certifications Block */}
      {showCerts && (
        <div style={{ border: "1px solid #d9d5cc", padding: "12px", borderRadius: "4px", marginBottom: "14px", backgroundColor: "#ffffff" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontWeight: 600, fontSize: "14px" }}>Certifications</span>
            <button
              type="button"
              onClick={addCert}
              style={{
                background: "none",
                border: "none",
                color: "#2f5d50",
                textDecoration: "underline",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Add certification
            </button>
          </div>

          {(resume.certifications || []).map((cert, cIdx) => (
            <div key={cIdx} style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr auto", gap: "8px", marginBottom: "8px", alignItems: "center" }}>
              <input
                type="text"
                placeholder="AWS Certified Solutions Architect"
                value={cert.name}
                onChange={(e) => updateCert(cIdx, "name", e.target.value)}
                style={{ padding: "5px 8px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
              />
              <input
                type="text"
                placeholder="Amazon Web Services"
                value={cert.issuer || ""}
                onChange={(e) => updateCert(cIdx, "issuer", e.target.value)}
                style={{ padding: "5px 8px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
              />
              <input
                type="text"
                placeholder="2023-08"
                value={cert.date || ""}
                onChange={(e) => updateCert(cIdx, "date", e.target.value)}
                style={{ padding: "5px 8px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
              />
              <button
                type="button"
                onClick={() => removeCert(cIdx)}
                style={{ background: "none", border: "none", color: "#8b0000", fontSize: "14px", cursor: "pointer" }}
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Publications Block */}
      {showPubs && (
        <div style={{ border: "1px solid #d9d5cc", padding: "12px", borderRadius: "4px", marginBottom: "14px", backgroundColor: "#ffffff" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontWeight: 600, fontSize: "14px" }}>Publications</span>
            <button
              type="button"
              onClick={addPub}
              style={{
                background: "none",
                border: "none",
                color: "#2f5d50",
                textDecoration: "underline",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Add publication
            </button>
          </div>

          {(resume.publications || []).map((pub, pIdx) => (
            <div key={pIdx} style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 0.6fr 1fr auto", gap: "8px", marginBottom: "8px", alignItems: "center" }}>
              <input
                type="text"
                placeholder="Paper / Article Title"
                value={pub.title}
                onChange={(e) => updatePub(pIdx, "title", e.target.value)}
                style={{ padding: "5px 8px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
              />
              <input
                type="text"
                placeholder="Journal / Conference"
                value={pub.venue || ""}
                onChange={(e) => updatePub(pIdx, "venue", e.target.value)}
                style={{ padding: "5px 8px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
              />
              <input
                type="text"
                placeholder="2023"
                value={pub.year || ""}
                onChange={(e) => updatePub(pIdx, "year", e.target.value)}
                style={{ padding: "5px 8px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
              />
              <input
                type="text"
                placeholder="https://doi.org/..."
                value={pub.link || ""}
                onChange={(e) => updatePub(pIdx, "link", e.target.value)}
                style={{ padding: "5px 8px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
              />
              <button
                type="button"
                onClick={() => removePub(pIdx)}
                style={{ background: "none", border: "none", color: "#8b0000", fontSize: "14px", cursor: "pointer" }}
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Achievements Block */}
      {showAchievements && (
        <div style={{ border: "1px solid #d9d5cc", padding: "12px", borderRadius: "4px", marginBottom: "14px", backgroundColor: "#ffffff" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontWeight: 600, fontSize: "14px" }}>Achievements & Awards</span>
            <button
              type="button"
              onClick={addAchievement}
              style={{
                background: "none",
                border: "none",
                color: "#2f5d50",
                textDecoration: "underline",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Add achievement
            </button>
          </div>

          {(resume.achievements || []).map((ach, aIdx) => (
            <div key={aIdx} style={{ display: "flex", gap: "8px", marginBottom: "6px", alignItems: "center" }}>
              <input
                type="text"
                placeholder="1st Place Hackathon Winner among 150+ teams nationwide..."
                value={ach}
                onChange={(e) => updateAchievement(aIdx, e.target.value)}
                style={{ flex: 1, padding: "5px 8px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
              />
              <button
                type="button"
                onClick={() => removeAchievement(aIdx)}
                style={{ background: "none", border: "none", color: "#8b0000", fontSize: "14px", cursor: "pointer" }}
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Custom Sections Block */}
      {showCustom && (
        <div style={{ border: "1px solid #d9d5cc", padding: "12px", borderRadius: "4px", backgroundColor: "#ffffff" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontWeight: 600, fontSize: "14px" }}>Custom Sections</span>
            <button
              type="button"
              onClick={addCustomSection}
              style={{
                background: "none",
                border: "none",
                color: "#2f5d50",
                textDecoration: "underline",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Add section
            </button>
          </div>

          {(resume.custom_sections || []).map((sec, sIdx) => (
            <div key={sIdx} style={{ border: "1px solid #ece8e1", padding: "10px", borderRadius: "4px", marginBottom: "10px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <input
                  type="text"
                  placeholder="Section Title (e.g. Leadership)"
                  value={sec.title}
                  onChange={(e) => updateCustomSectionTitle(sIdx, e.target.value)}
                  style={{ width: "250px", fontWeight: 600, padding: "4px 8px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
                />
                <button
                  type="button"
                  onClick={() => removeCustomSection(sIdx)}
                  style={{ background: "none", border: "none", color: "#8b0000", fontSize: "12px", cursor: "pointer" }}
                >
                  Remove section
                </button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {sec.bullets.map((b, bIdx) => (
                  <div key={bIdx} style={{ display: "flex", gap: "6px" }}>
                    <input
                      type="text"
                      placeholder="Bullet point..."
                      value={b}
                      onChange={(e) => updateCustomBullet(sIdx, bIdx, e.target.value)}
                      style={{ flex: 1, padding: "4px 6px", border: "1px solid #d9d5cc", borderRadius: "4px", fontSize: "13px" }}
                    />
                    <button
                      type="button"
                      onClick={() => removeCustomBullet(sIdx, bIdx)}
                      style={{ background: "none", border: "none", color: "#8b0000", fontSize: "14px", cursor: "pointer" }}
                    >
                      &times;
                    </button>
                  </div>
                ))}
                <div>
                  <button
                    type="button"
                    onClick={() => addCustomBullet(sIdx)}
                    style={{ background: "none", border: "none", color: "#2f5d50", textDecoration: "underline", fontSize: "12px", cursor: "pointer" }}
                  >
                    Add bullet
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
