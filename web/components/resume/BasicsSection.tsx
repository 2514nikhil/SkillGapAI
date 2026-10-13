"use client";

import React, { useEffect, useState } from "react";
import { Resume } from "@/lib/resumeTypes";
import { getRoles } from "@/lib/api";
import { aiDraftSummary } from "@/lib/resumeApi";

interface BasicsSectionProps {
  resume: Resume;
  onChange: (updated: Resume) => void;
  onServerError?: (msg: string | null) => void;
}

export default function BasicsSection({
  resume,
  onChange,
  onServerError,
}: BasicsSectionProps) {
  const [availableRoles, setAvailableRoles] = useState<string[]>([]);
  const [isDraftingSummary, setIsDraftingSummary] = useState(false);
  const [summaryVariants, setSummaryVariants] = useState<string[]>([]);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    getRoles()
      .then((roles) => {
        if (mounted && Array.isArray(roles)) {
          setAvailableRoles(roles.map((r) => r.role));
        }
      })
      .catch(() => {
        // Backend roles lookup failure is non-fatal; user can still type custom role
      });
    return () => {
      mounted = false;
    };
  }, []);

  const updateBasics = (field: string, value: any) => {
    onChange({
      ...resume,
      basics: {
        ...resume.basics,
        [field]: value,
      },
    });
  };

  const updateLocation = (field: "city" | "region_country", value: string) => {
    onChange({
      ...resume,
      basics: {
        ...resume.basics,
        location: {
          ...resume.basics.location,
          [field]: value,
        },
      },
    });
  };

  const updateTargetRole = (val: string) => {
    onChange({
      ...resume,
      meta: {
        ...resume.meta,
        target_role: val,
      },
    });
  };

  const handleDraftSummary = async () => {
    setIsDraftingSummary(true);
    setSummaryError(null);
    try {
      const res = await aiDraftSummary(resume);
      if (res.variants && res.variants.length > 0) {
        setSummaryVariants(res.variants);
      } else {
        setSummaryError("Could not draft a summary from the current resume data.");
      }
    } catch (err: any) {
      setSummaryError(err.message || "Failed to generate summary with AI.");
      if (onServerError) {
        onServerError("Server not responding. Editing and local auto-save continue to work.");
      }
    } finally {
      setIsDraftingSummary(false);
    }
  };

  return (
    <section id="section-basics" style={{ marginBottom: "28px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, borderBottom: "1px solid #d9d5cc", paddingBottom: "6px", marginBottom: "14px" }}>
        Basics
      </h2>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
        <div>
          <label style={{ display: "block", fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
            Full Name <span style={{ color: "#8b0000" }}>*</span>
          </label>
          <input
            type="text"
            placeholder="Jane Doe"
            value={resume.basics.name}
            onChange={(e) => updateBasics("name", e.target.value)}
            style={{
              width: "100%",
              padding: "6px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
            Email Address <span style={{ color: "#8b0000" }}>*</span>
          </label>
          <input
            type="email"
            placeholder="jane@example.com"
            value={resume.basics.email}
            onChange={(e) => updateBasics("email", e.target.value)}
            style={{
              width: "100%",
              padding: "6px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
        <div>
          <label style={{ display: "block", fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
            Phone Number (optional)
          </label>
          <input
            type="tel"
            placeholder="+1 (555) 019-2834"
            value={resume.basics.phone || ""}
            onChange={(e) => updateBasics("phone", e.target.value)}
            style={{
              width: "100%",
              padding: "6px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
            Headline / Professional Title
          </label>
          <input
            type="text"
            placeholder="Full-Stack Software Engineer"
            value={resume.basics.headline || ""}
            onChange={(e) => updateBasics("headline", e.target.value)}
            style={{
              width: "100%",
              padding: "6px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
        <div>
          <label style={{ display: "block", fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
            City (optional)
          </label>
          <input
            type="text"
            placeholder="Bengaluru"
            value={resume.basics.location?.city || ""}
            onChange={(e) => updateLocation("city", e.target.value)}
            style={{
              width: "100%",
              padding: "6px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
            Region / Country (optional)
          </label>
          <input
            type="text"
            placeholder="India"
            value={resume.basics.location?.region_country || ""}
            onChange={(e) => updateLocation("region_country", e.target.value)}
            style={{
              width: "100%",
              padding: "6px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
        </div>
      </div>

      <div style={{ marginBottom: "14px" }}>
        <label style={{ display: "block", fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
          Target Role (optional, used for tailoring)
        </label>
        <div style={{ display: "flex", gap: "8px" }}>
          <input
            type="text"
            list="target-roles-list"
            placeholder="e.g. Backend Developer"
            value={resume.meta.target_role || ""}
            onChange={(e) => updateTargetRole(e.target.value)}
            style={{
              flex: 1,
              padding: "6px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
          <datalist id="target-roles-list">
            {availableRoles.map((r) => (
              <option key={r} value={r} />
            ))}
          </datalist>
        </div>
      </div>

      <div style={{ marginBottom: "14px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
          <label style={{ fontSize: "14px", fontWeight: 500 }}>
            Professional Summary (optional)
          </label>
          <button
            type="button"
            onClick={handleDraftSummary}
            disabled={isDraftingSummary}
            style={{
              background: "none",
              border: "none",
              color: "#2f5d50",
              textDecoration: "underline",
              fontSize: "13px",
              cursor: isDraftingSummary ? "default" : "pointer",
            }}
          >
            {isDraftingSummary ? "Drafting summary..." : "Draft summary with AI"}
          </button>
        </div>

        <textarea
          rows={3}
          placeholder="Brief 2-3 sentence overview of your background, core strengths, and goals..."
          value={resume.summary || ""}
          onChange={(e) => onChange({ ...resume, summary: e.target.value })}
          style={{
            width: "100%",
            padding: "8px",
            border: "1px solid #d9d5cc",
            borderRadius: "4px",
            fontSize: "14px",
            lineHeight: 1.4,
          }}
        />

        {summaryError && (
          <div style={{ fontSize: "13px", color: "#8b0000", marginTop: "4px" }}>
            {summaryError}
          </div>
        )}

        {summaryVariants.length > 0 && (
          <div
            style={{
              marginTop: "10px",
              padding: "10px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              backgroundColor: "#fffdf9",
            }}
          >
            <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "6px" }}>
              Suggested Summaries (Derived strictly from your resume entries):
            </div>
            {summaryVariants.map((variant, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: idx < summaryVariants.length - 1 ? "10px" : "0",
                  paddingBottom: idx < summaryVariants.length - 1 ? "8px" : "0",
                  borderBottom: idx < summaryVariants.length - 1 ? "1px dashed #d9d5cc" : "none",
                }}
              >
                <p style={{ margin: "0 0 6px 0", fontSize: "13px", lineHeight: 1.4 }}>
                  {variant}
                </p>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    type="button"
                    onClick={() => {
                      onChange({ ...resume, summary: variant });
                      setSummaryVariants([]);
                    }}
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
                    Use this
                  </button>
                  <button
                    type="button"
                    onClick={() => setSummaryVariants([])}
                    style={{
                      border: "1px solid #d9d5cc",
                      backgroundColor: "#ffffff",
                      fontSize: "12px",
                      padding: "3px 8px",
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
    </section>
  );
}
