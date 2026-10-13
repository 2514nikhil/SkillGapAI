"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  AISkillSuggestion,
  CatalogCategory,
  CatalogSkill,
  Resume,
  SkillItem,
  SkillLevel,
  TechCatalog,
} from "@/lib/resumeTypes";
import { aiSuggestSkills, fetchTechCatalog } from "@/lib/resumeApi";

interface SkillsSectionProps {
  resume: Resume;
  onChange: (updated: Resume) => void;
  onServerError?: (msg: string | null) => void;
}

export default function SkillsSection({
  resume,
  onChange,
  onServerError,
}: SkillsSectionProps) {
  const [catalog, setCatalog] = useState<TechCatalog | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [customInput, setCustomInput] = useState("");
  const [showLevels, setShowLevels] = useState(false);

  // AI suggestions state
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [suggestedSkills, setSuggestedSkills] = useState<AISkillSuggestion[]>([]);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchTechCatalog()
      .then((cat) => {
        if (mounted && cat?.categories) {
          setCatalog(cat);
        }
      })
      .catch((err) => {
        console.warn("Could not load catalog from server:", err);
        if (onServerError) {
          onServerError("Server not responding. Editing and local auto-save continue to work.");
        }
      });
    return () => {
      mounted = false;
    };
  }, [onServerError]);

  // Selected skills lookup by lowercase name
  const selectedMap = useMemo(() => {
    const map = new Map<string, SkillItem>();
    for (const s of resume.skills) {
      map.set(s.name.toLowerCase().trim(), s);
    }
    return map;
  }, [resume.skills]);

  // Count pinned skills
  const pinnedCount = useMemo(() => {
    return resume.skills.filter((s) => s.pinned).length;
  }, [resume.skills]);

  const toggleSkill = (
    skillName: string,
    categoryId: string,
    taxonomyId?: string | null,
    custom: boolean = false
  ) => {
    const key = skillName.toLowerCase().trim();
    if (selectedMap.has(key)) {
      // Remove
      onChange({
        ...resume,
        skills: resume.skills.filter((s) => s.name.toLowerCase().trim() !== key),
      });
    } else {
      // Add
      const newSkill: SkillItem = {
        category_id: categoryId,
        name: skillName,
        taxonomy_id: taxonomyId || null,
        custom,
        pinned: false,
        level: showLevels ? "intermediate" : null,
      };
      onChange({
        ...resume,
        skills: [...resume.skills, newSkill],
      });
    }
  };

  const removeSkill = (skillName: string) => {
    const key = skillName.toLowerCase().trim();
    onChange({
      ...resume,
      skills: resume.skills.filter((s) => s.name.toLowerCase().trim() !== key),
    });
  };

  const togglePin = (skillName: string) => {
    const key = skillName.toLowerCase().trim();
    const current = selectedMap.get(key);
    if (!current) return;

    if (!current.pinned && pinnedCount >= 8) {
      alert("You can pin a maximum of 8 skills to the top of your resume.");
      return;
    }

    onChange({
      ...resume,
      skills: resume.skills.map((s) => {
        if (s.name.toLowerCase().trim() === key) {
          return { ...s, pinned: !s.pinned };
        }
        return s;
      }),
    });
  };

  const updateLevel = (skillName: string, level: SkillLevel) => {
    const key = skillName.toLowerCase().trim();
    onChange({
      ...resume,
      skills: resume.skills.map((s) => {
        if (s.name.toLowerCase().trim() === key) {
          return { ...s, level };
        }
        return s;
      }),
    });
  };

  // Add custom skill or match alias
  const handleAddCustom = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = customInput.trim();
    if (!trimmed) return;

    const lower = trimmed.toLowerCase();
    // Check if already selected
    if (selectedMap.has(lower)) {
      setCustomInput("");
      return;
    }

    // Check if matches any catalog skill or alias
    let matchedCat = "other_tools";
    let canonicalName = trimmed;
    let taxonomyId: string | null = null;

    if (catalog) {
      for (const cat of catalog.categories) {
        for (const sk of cat.skills) {
          if (sk.name.toLowerCase() === lower || sk.id.toLowerCase() === lower) {
            matchedCat = cat.id;
            canonicalName = sk.name;
            taxonomyId = sk.taxonomy_id || sk.id;
            break;
          }
          if (sk.aliases && sk.aliases.some((a) => a.toLowerCase() === lower)) {
            matchedCat = cat.id;
            canonicalName = sk.name;
            taxonomyId = sk.taxonomy_id || sk.id;
            break;
          }
        }
      }
    }

    toggleSkill(canonicalName, matchedCat, taxonomyId, matchedCat === "other_tools");
    setCustomInput("");
  };

  // Filter categories and skills based on search query
  const filteredCategories = useMemo(() => {
    if (!catalog?.categories) return [];
    const q = searchQuery.toLowerCase().trim();
    if (!q) return catalog.categories;

    const filtered: CatalogCategory[] = [];
    for (const cat of catalog.categories) {
      const matchingSkills = cat.skills.filter(
        (sk) =>
          sk.name.toLowerCase().includes(q) ||
          sk.id.toLowerCase().includes(q) ||
          sk.aliases?.some((a) => a.toLowerCase().includes(q))
      );
      if (matchingSkills.length > 0) {
        filtered.push({
          ...cat,
          skills: matchingSkills,
        });
      }
    }
    return filtered;
  }, [catalog, searchQuery]);

  const handleSuggestSkills = async () => {
    setIsSuggesting(true);
    setSuggestionError(null);
    try {
      const res = await aiSuggestSkills(resume);
      if (res.suggestions && res.suggestions.length > 0) {
        setSuggestedSkills(res.suggestions);
      } else {
        setSuggestionError("No unlisted skills detected in your current resume text.");
      }
    } catch (err: any) {
      setSuggestionError(err.message || "Failed to analyze skills from text.");
      if (onServerError) {
        onServerError("Server not responding. Editing and local auto-save continue to work.");
      }
    } finally {
      setIsSuggesting(false);
    }
  };

  return (
    <section id="section-skills" style={{ marginBottom: "28px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, borderBottom: "1px solid #d9d5cc", paddingBottom: "6px", marginBottom: "14px" }}>
        Skills
      </h2>

      {/* Your skills tray */}
      <div
        style={{
          border: "1px solid #d9d5cc",
          borderRadius: "4px",
          backgroundColor: "#fffdf9",
          padding: "12px",
          marginBottom: "16px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "14px", fontWeight: 600 }}>
            Your selected skills ({resume.skills.length})
          </span>
          <label style={{ fontSize: "13px", display: "inline-flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={showLevels}
              onChange={(e) => {
                const checked = e.target.checked;
                setShowLevels(checked);
                if (checked) {
                  // Default any skills with null level to intermediate
                  onChange({
                    ...resume,
                    skills: resume.skills.map((s) => ({
                      ...s,
                      level: s.level || "intermediate",
                    })),
                  });
                }
              }}
            />
            <span>Add proficiency levels</span>
          </label>
        </div>

        {resume.skills.length === 0 ? (
          <p style={{ margin: 0, fontSize: "13px", color: "#55534e" }}>
            No skills selected yet. Click skills below, search the catalog, or use &quot;Suggest skills from my text&quot;.
          </p>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {resume.skills.map((skill) => (
              <div
                key={skill.name}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  border: "1px solid #2f5d50",
                  backgroundColor: skill.pinned ? "#24493e" : "#2f5d50",
                  color: "#ffffff",
                  borderRadius: "4px",
                  padding: "4px 8px",
                  fontSize: "13px",
                }}
              >
                <span>{skill.name}</span>

                {showLevels && (
                  <select
                    value={skill.level || "intermediate"}
                    onChange={(e) => updateLevel(skill.name, e.target.value as SkillLevel)}
                    style={{
                      fontSize: "11px",
                      padding: "1px 4px",
                      border: "1px solid #ffffff",
                      borderRadius: "3px",
                      backgroundColor: "#2f5d50",
                      color: "#ffffff",
                    }}
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                    <option value="expert">Expert</option>
                  </select>
                )}

                <button
                  type="button"
                  onClick={() => togglePin(skill.name)}
                  title={skill.pinned ? "Unpin skill" : "Pin skill to top"}
                  style={{
                    background: "none",
                    border: "none",
                    color: skill.pinned ? "#ffea75" : "#ffffff",
                    fontSize: "11px",
                    cursor: "pointer",
                    padding: "0 2px",
                    fontWeight: skill.pinned ? 700 : 400,
                  }}
                >
                  {skill.pinned ? "[Pinned]" : "[Pin]"}
                </button>

                <button
                  type="button"
                  onClick={() => removeSkill(skill.name)}
                  title="Remove skill"
                  style={{
                    background: "none",
                    border: "none",
                    color: "#ffffff",
                    fontSize: "13px",
                    cursor: "pointer",
                    padding: "0 2px",
                    lineHeight: 1,
                  }}
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Controls row: Search + Add Custom + Suggest from text */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "12px" }}>
        <div>
          <input
            type="text"
            placeholder="Search skills (e.g. Python, Docker, AWS)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: "100%",
              padding: "6px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
        </div>

        <form onSubmit={handleAddCustom} style={{ display: "flex", gap: "6px" }}>
          <input
            type="text"
            placeholder="Add your own skill..."
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            style={{
              flex: 1,
              padding: "6px 8px",
              border: "1px solid #d9d5cc",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
          <button
            type="submit"
            style={{
              border: "1px solid #d9d5cc",
              backgroundColor: "#ffffff",
              padding: "6px 12px",
              borderRadius: "4px",
              fontSize: "14px",
              cursor: "pointer",
            }}
          >
            Add
          </button>
        </form>
      </div>

      {/* Suggest skills from text action */}
      <div style={{ marginBottom: "16px" }}>
        <button
          type="button"
          onClick={handleSuggestSkills}
          disabled={isSuggesting}
          style={{
            border: "1px solid #2f5d50",
            backgroundColor: "#ffffff",
            color: "#2f5d50",
            padding: "5px 12px",
            borderRadius: "4px",
            fontSize: "13px",
            cursor: isSuggesting ? "default" : "pointer",
          }}
        >
          {isSuggesting ? "Analyzing text for skills..." : "Suggest skills from my text"}
        </button>

        {suggestionError && (
          <div style={{ fontSize: "13px", color: "#8b0000", marginTop: "4px" }}>
            {suggestionError}
          </div>
        )}

        {suggestedSkills.length > 0 && (
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
              Discovered skills from your experience & projects:
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {suggestedSkills.map((sug, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    fontSize: "13px",
                    padding: "4px 0",
                    borderBottom: idx < suggestedSkills.length - 1 ? "1px dashed #d9d5cc" : "none",
                  }}
                >
                  <div>
                    <strong>{sug.name}</strong>
                    <span style={{ color: "#55534e", marginLeft: "6px", fontSize: "12px" }}>
                      (found in: &quot;{sug.source_sentence.slice(0, 70)}...&quot;)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      toggleSkill(sug.name, sug.category_id, sug.taxonomy_id);
                      setSuggestedSkills((prev) => prev.filter((_, i) => i !== idx));
                    }}
                    style={{
                      border: "1px solid #2f5d50",
                      backgroundColor: "#2f5d50",
                      color: "#ffffff",
                      fontSize: "12px",
                      padding: "2px 8px",
                      borderRadius: "3px",
                      cursor: "pointer",
                    }}
                  >
                    Add
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Categories and Skill Chips */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {filteredCategories.map((category) => {
          const isExpanded = expandedCategories[category.id] || false;
          const displaySkills = isExpanded
            ? category.skills
            : category.skills.slice(0, 24);
          const hasMore = category.skills.length > 24;

          return (
            <div key={category.id}>
              <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "8px", color: "#1d1d1b" }}>
                {category.name} ({category.skills.length})
              </div>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {displaySkills.map((skill: CatalogSkill) => {
                  const isSelected = selectedMap.has(skill.name.toLowerCase().trim());
                  return (
                    <button
                      key={skill.id}
                      type="button"
                      aria-pressed={isSelected}
                      onClick={() =>
                        toggleSkill(skill.name, category.id, skill.taxonomy_id || skill.id)
                      }
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          toggleSkill(skill.name, category.id, skill.taxonomy_id || skill.id);
                        }
                      }}
                      style={{
                        border: isSelected ? "1px solid #2f5d50" : "1px solid #d9d5cc",
                        backgroundColor: isSelected ? "#2f5d50" : "#ffffff",
                        color: isSelected ? "#ffffff" : "#1d1d1b",
                        fontSize: "14px",
                        borderRadius: "4px",
                        padding: "4px 10px",
                        cursor: "pointer",
                      }}
                    >
                      {skill.name}
                    </button>
                  );
                })}
              </div>

              {hasMore && (
                <div style={{ marginTop: "6px" }}>
                  <button
                    type="button"
                    onClick={() =>
                      setExpandedCategories((prev) => ({
                        ...prev,
                        [category.id]: !isExpanded,
                      }))
                    }
                    style={{
                      background: "none",
                      border: "none",
                      color: "#2f5d50",
                      textDecoration: "underline",
                      fontSize: "13px",
                      cursor: "pointer",
                      padding: 0,
                    }}
                  >
                    {isExpanded ? "Show fewer" : `Show all ${category.skills.length}`}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
