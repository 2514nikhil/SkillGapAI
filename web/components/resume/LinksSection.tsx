"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Resume, SocialLink, SocialPlatform } from "@/lib/resumeTypes";
import { fetchSocialPlatforms } from "@/lib/resumeApi";

interface LinksSectionProps {
  resume: Resume;
  onChange: (updated: Resume) => void;
  onServerError?: (msg: string | null) => void;
}

export default function LinksSection({
  resume,
  onChange,
  onServerError,
}: LinksSectionProps) {
  const [platforms, setPlatforms] = useState<SocialPlatform[]>([]);
  const [selectedPlatformToAdd, setSelectedPlatformToAdd] = useState<string>("");

  useEffect(() => {
    let mounted = true;
    fetchSocialPlatforms()
      .then((data) => {
        if (mounted && Array.isArray(data)) {
          setPlatforms(data);
        }
      })
      .catch((err) => {
        console.warn("Could not load social platforms:", err);
        if (onServerError) {
          onServerError("Server not responding. Editing and local auto-save continue to work.");
        }
      });
    return () => {
      mounted = false;
    };
  }, [onServerError]);

  const platformMap = useMemo(() => {
    const map = new Map<string, SocialPlatform>();
    for (const p of platforms) {
      map.set(p.id.toLowerCase(), p);
    }
    return map;
  }, [platforms]);

  const links = resume.basics.links || [];

  const updateLink = (index: number, value: string) => {
    const updated = [...links];
    updated[index] = { ...updated[index], value };
    onChange({
      ...resume,
      basics: {
        ...resume.basics,
        links: updated,
      },
    });
  };

  const removeLink = (index: number) => {
    const updated = links.filter((_, idx) => idx !== index);
    onChange({
      ...resume,
      basics: {
        ...resume.basics,
        links: updated,
      },
    });
  };

  const addPlatformLink = (platformId: string) => {
    if (!platformId) return;
    const exists = links.some((l) => l.platform_id.toLowerCase() === platformId.toLowerCase());
    if (exists) {
      alert(`You already added a link for ${platformId}.`);
      return;
    }
    const updated = [...links, { platform_id: platformId, value: "" }];
    onChange({
      ...resume,
      basics: {
        ...resume.basics,
        links: updated,
      },
    });
    setSelectedPlatformToAdd("");
  };

  // Helper to build preview URL
  const computePreviewUrl = (link: SocialLink): { url: string; isValid: boolean; warning?: string } => {
    const p = platformMap.get(link.platform_id.toLowerCase());
    const val = link.value.trim();
    if (!val) return { url: "", isValid: true };

    if (val.startsWith("http://") || val.startsWith("https://")) {
      return {
        url: val,
        isValid: true,
        warning: p && !p.resume_friendly ? "Note: This platform is generally non-resume-friendly." : undefined,
      };
    }

    if (!p) {
      return { url: val, isValid: true };
    }

    let url = p.url_template.replace("{value}", val);
    let isValid = true;
    let warning: string | undefined;

    if (p.validator) {
      try {
        const regex = new RegExp(p.validator);
        if (!regex.test(val)) {
          isValid = false;
          warning = `Value does not match expected format for ${p.label}`;
        }
      } catch {
        // Ignored
      }
    }

    if (p && !p.resume_friendly) {
      warning = warning ? `${warning}. Also, non-resume-friendly platform.` : "Note: This platform is generally non-resume-friendly.";
    }

    return { url, isValid, warning };
  };

  return (
    <section id="section-links" style={{ marginBottom: "28px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, borderBottom: "1px solid #d9d5cc", paddingBottom: "6px", marginBottom: "14px" }}>
        Links & Social Profiles
      </h2>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "16px" }}>
        {links.map((link, idx) => {
          const p = platformMap.get(link.platform_id.toLowerCase());
          const label = p ? p.label : link.platform_id;
          const placeholder = p ? p.placeholder : "username or URL";
          const { url, isValid, warning } = computePreviewUrl(link);

          return (
            <div
              key={idx}
              style={{
                border: "1px solid #d9d5cc",
                borderRadius: "4px",
                padding: "10px",
                backgroundColor: "#ffffff",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontWeight: 600, fontSize: "14px" }}>{label}</span>
                <button
                  type="button"
                  onClick={() => removeLink(idx)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#8b0000",
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  Remove
                </button>
              </div>

              <input
                type="text"
                placeholder={placeholder}
                value={link.value}
                onChange={(e) => updateLink(idx, e.target.value)}
                style={{
                  width: "100%",
                  padding: "5px 8px",
                  border: isValid ? "1px solid #d9d5cc" : "1px solid #8b0000",
                  borderRadius: "4px",
                  fontSize: "14px",
                }}
              />

              {url && (
                <div style={{ marginTop: "6px", fontSize: "12px", color: "#55534e" }}>
                  <span>Preview: </span>
                  <a href={url} target="_blank" rel="noopener noreferrer">
                    {url}
                  </a>
                </div>
              )}

              {warning && (
                <div style={{ marginTop: "4px", fontSize: "12px", color: isValid ? "#8a6d3b" : "#8b0000" }}>
                  {warning}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Add more links dropdown */}
      <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
        <select
          value={selectedPlatformToAdd}
          onChange={(e) => setSelectedPlatformToAdd(e.target.value)}
          style={{
            padding: "5px 8px",
            border: "1px solid #d9d5cc",
            borderRadius: "4px",
            fontSize: "14px",
            backgroundColor: "#ffffff",
          }}
        >
          <option value="">Select platform to add...</option>
          {platforms
            .filter((p) => !links.some((l) => l.platform_id.toLowerCase() === p.id.toLowerCase()))
            .map((p) => (
              <option key={p.id} value={p.id}>
                {p.label} {!p.resume_friendly ? "(non-resume friendly)" : ""}
              </option>
            ))}
        </select>

        <button
          type="button"
          disabled={!selectedPlatformToAdd}
          onClick={() => addPlatformLink(selectedPlatformToAdd)}
          style={{
            border: "1px solid #d9d5cc",
            backgroundColor: "#ffffff",
            padding: "5px 12px",
            borderRadius: "4px",
            fontSize: "14px",
            cursor: selectedPlatformToAdd ? "pointer" : "default",
            opacity: selectedPlatformToAdd ? 1 : 0.5,
          }}
        >
          Add link
        </button>
      </div>
    </section>
  );
}
