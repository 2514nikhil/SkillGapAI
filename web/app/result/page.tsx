"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { compareRoles, searchSkills, simulateWhatIf } from "@/lib/api";
import {
  AnalyzeResponse,
  CompareResponse,
  ExtractedSkillItem,
  MissingSkillItem,
  SkillItem,
  WhatIfResponse,
} from "@/lib/types";
import Tour from "@/components/Tour";
import Hint from "@/components/Hint";
import { TourStep } from "@/lib/tourUtils";

const resultTourSteps: TourStep[] = [
  {
    target: '[data-tour="score"]',
    title: "Score",
    body: "This is how much of the role's skill demand your resume covers. It is a guide, not a verdict.",
    placement: "bottom",
  },
  {
    target: '[data-tour="skills-found"]',
    title: "Skills we found",
    body: "Check this list. If we missed a skill or found a wrong one, remove it or add your own, then press Recalculate.",
    placement: "top",
  },
  {
    target: '[data-tour="skills-needed"]',
    title: "Skills the role needs",
    body: "The bar shows how many postings for this role ask for the skill. Missing skills with long bars matter most.",
    placement: "top",
  },
  {
    target: '[data-tour="what-to-learn"]',
    title: "What to learn first",
    body: "Courses in a sensible order. The points show how much your score should rise after each one.",
    placement: "top",
  },
  {
    target: '[data-tour="try-it"]',
    title: "Try it",
    body: "Tick a skill you plan to learn to see how your score would change.",
    placement: "top",
  },
  {
    target: '[data-tour="compare-roles"]',
    title: "Compare with other roles",
    body: "See how the same resume scores against other roles.",
    placement: "top",
  },
];

interface RoleRequirementRow {
  skill: string;
  skill_id: string;
  weight: number;
  haveIt: "Yes" | "Partly" | "No";
  pointsText: string;
  sortPriority: number;
  sortImpact: number;
}

export default function ResultPage() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [targetRole, setTargetRole] = useState<string>("Target Role");

  // Editable skills state
  const [currentSkills, setCurrentSkills] = useState<ExtractedSkillItem[]>([]);
  const [hasSkillEdits, setHasSkillEdits] = useState<boolean>(false);
  const [isRecalculating, setIsRecalculating] = useState<boolean>(false);

  // Taxonomy skill search for manual addition
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchResults, setSearchResults] = useState<SkillItem[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  // What-If state
  const [selectedWhatIfSkills, setSelectedWhatIfSkills] = useState<string[]>([]);
  const [whatIfData, setWhatIfData] = useState<WhatIfResponse | null>(null);
  const [isWhatIfLoading, setIsWhatIfLoading] = useState<boolean>(false);

  // Compare roles state
  const [compareData, setCompareData] = useState<CompareResponse | null>(null);
  const [isComparing, setIsComparing] = useState<boolean>(false);

  // Error message box
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = sessionStorage.getItem("skillgap_result");
      const role = sessionStorage.getItem("skillgap_target_role");
      if (stored) {
        try {
          const parsed: AnalyzeResponse = JSON.parse(stored);
          setResult(parsed);
          setCurrentSkills(parsed.extracted_skills);
        } catch {
          setApiError("Could not read analysis results from session.");
        }
      } else {
        setApiError("No analysis session found. Please upload a resume first.");
      }
      if (role) {
        setTargetRole(role);
      }
    }
  }, []);

  // Search taxonomy when user types
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(() => {
      setIsSearching(true);
      searchSkills(searchQuery)
        .then((items) => {
          setSearchResults(items);
          setIsSearching(false);
        })
        .catch(() => {
          setIsSearching(false);
        });
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleRemoveSkill = (skillId: string) => {
    setCurrentSkills((prev) => prev.filter((s) => s.skill_id !== skillId));
    setHasSkillEdits(true);
  };

  const handleAddSkill = (skill: SkillItem) => {
    if (currentSkills.some((s) => s.skill_id === skill.skill_id)) {
      setSearchQuery("");
      setSearchResults([]);
      return;
    }
    const newSkill: ExtractedSkillItem = {
      skill: skill.name,
      skill_id: skill.skill_id,
      category: skill.category,
      confidence: 1.0,
      source: "manual",
      evidence: "Manually added by candidate",
    };
    setCurrentSkills((prev) => [...prev, newSkill]);
    setHasSkillEdits(true);
    setSearchQuery("");
    setSearchResults([]);
  };

  const handleRecalculate = async () => {
    if (!result) return;
    setIsRecalculating(true);
    setApiError(null);

    try {
      const skillIds = currentSkills.map((s) => s.skill_id);
      const res = await simulateWhatIf({
        skills: skillIds,
        role: targetRole,
        add: [],
      });

      // Update current result scores
      setResult((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          score: {
            ...prev.score,
            final: res.new_score,
            coverage: res.new_coverage,
          },
        };
      });
      setHasSkillEdits(false);
      setIsRecalculating(false);
    } catch (err: unknown) {
      setIsRecalculating(false);
      if (err instanceof Error) {
        setApiError(err.message);
      } else {
        setApiError("Failed to recalculate scores.");
      }
    }
  };

  const handleWhatIfToggle = async (skillId: string) => {
    const updated = selectedWhatIfSkills.includes(skillId)
      ? selectedWhatIfSkills.filter((id) => id !== skillId)
      : [...selectedWhatIfSkills, skillId];

    setSelectedWhatIfSkills(updated);

    if (updated.length === 0) {
      setWhatIfData(null);
      return;
    }

    setIsWhatIfLoading(true);
    setApiError(null);

    try {
      const skillIds = currentSkills.map((s) => s.skill_id);
      const res = await simulateWhatIf({
        analysis_id: result?.analysis_id,
        skills: skillIds,
        role: targetRole,
        add: updated,
      });
      setWhatIfData(res);
      setIsWhatIfLoading(false);
    } catch (err: unknown) {
      setIsWhatIfLoading(false);
      if (err instanceof Error) {
        setApiError(err.message);
      }
    }
  };

  const handleLoadComparisons = async () => {
    setIsComparing(true);
    setApiError(null);

    try {
      const skillIds = currentSkills.map((s) => s.skill_id);
      const res = await compareRoles({
        analysis_id: result?.analysis_id,
        skills: skillIds,
      });
      setCompareData(res);
      setIsComparing(false);
    } catch (err: unknown) {
      setIsComparing(false);
      if (err instanceof Error) {
        setApiError(err.message);
      } else {
        setApiError("Could not load role comparisons.");
      }
    }
  };

  if (!result) {
    return (
      <div>
        <h1>SkillGap</h1>
        {apiError ? (
          <div className="error-box">{apiError}</div>
        ) : (
          <p>Loading analysis...</p>
        )}
        <p>
          <Link href="/">Upload your resume</Link>
        </p>
      </div>
    );
  }

  // Combine role demands into a single list with missing skills sorted first by gain/weight
  const candidateSkillIdSet = new Set(currentSkills.map((s) => s.skill_id));

  const roleRows: RoleRequirementRow[] = [];

  // 1. Missing skills
  for (const ms of result.missing) {
    const isNowPresent = candidateSkillIdSet.has(ms.skill_id);
    if (!isNowPresent) {
      roleRows.push({
        skill: ms.skill,
        skill_id: ms.skill_id,
        weight: ms.weight,
        haveIt: "No",
        pointsText: `Adds ${Math.round(ms.gain_if_learned)} pts`,
        sortPriority: 1,
        sortImpact: ms.gain_if_learned,
      });
    } else {
      roleRows.push({
        skill: ms.skill,
        skill_id: ms.skill_id,
        weight: ms.weight,
        haveIt: "Yes",
        pointsText: "Earned",
        sortPriority: 3,
        sortImpact: 0,
      });
    }
  }

  // 2. Partial skills
  for (const ps of result.partial) {
    if (!roleRows.some((r) => r.skill_id === ps.skill_id)) {
      roleRows.push({
        skill: ps.skill,
        skill_id: ps.skill_id,
        weight: 0.5,
        haveIt: "Partly",
        pointsText: `Covered by ${ps.covered_by}`,
        sortPriority: 2,
        sortImpact: 1,
      });
    }
  }

  // 3. Covered skills
  for (const cs of result.covered) {
    if (!roleRows.some((r) => r.skill_id === cs.skill_id)) {
      roleRows.push({
        skill: cs.skill,
        skill_id: cs.skill_id,
        weight: cs.weight,
        haveIt: "Yes",
        pointsText: "Earned",
        sortPriority: 3,
        sortImpact: 0,
      });
    }
  }

  // Sort missing skills first by impact descending
  roleRows.sort((a, b) => {
    if (a.sortPriority !== b.sortPriority) {
      return a.sortPriority - b.sortPriority;
    }
    return b.sortImpact - a.sortImpact;
  });

  return (
    <div>
      <Tour steps={resultTourSteps} storageKey="skillgap_tour_result_v1" />

      <div style={{ marginBottom: "16px" }}>
        <Link href="/">Upload another resume</Link>
      </div>

      {apiError && <div className="error-box">{apiError}</div>}

      {/* a. Score Heading */}
      <section data-tour="score">
        <div style={{ display: "flex", alignItems: "baseline", flexWrap: "wrap", gap: "8px" }}>
          <h1 style={{ margin: 0 }}>
            Match for {targetRole}: {Math.round(result.score.final)}%
          </h1>
          <Hint label="How is this calculated?">
            Coverage of the role&rsquo;s skills weighted by how common each is in postings, plus a small text-similarity part.
          </Hint>
        </div>
        <p style={{ fontSize: "14px", color: "var(--muted)", margin: "6px 0 10px 0" }}>
          Coverage score: {Math.round(result.score.coverage)}% | Semantic text alignment:{" "}
          {Math.round(result.score.semantic)}%
        </p>
        <p style={{ marginTop: "8px" }}>{result.summary_text}</p>
      </section>

      {/* b. Skills we found in your resume */}
      <section data-tour="skills-found">
        <h2>Skills we found in your resume</h2>
        {currentSkills.length === 0 ? (
          <p>No skills detected yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th style={{ width: "25%" }}>Skill</th>
                <th style={{ width: "20%" }}>Category</th>
                <th style={{ width: "45%" }}>Where found</th>
                <th style={{ width: "10%" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {currentSkills.map((s) => (
                <tr key={s.skill_id}>
                  <td>
                    <strong>{s.skill}</strong>
                  </td>
                  <td>{s.category}</td>
                  <td style={{ fontSize: "14px", color: "var(--muted)" }}>
                    {s.evidence || "Resume excerpt"}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="link-button"
                      onClick={() => handleRemoveSkill(s.skill_id)}
                      aria-label={`Remove ${s.skill}`}
                    >
                      remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div style={{ marginTop: "12px", marginBottom: "16px" }}>
          <label htmlFor="search-skill-input">Add a skill the extractor missed</label>
          <div style={{ display: "flex", gap: "8px", maxWidth: "480px" }}>
            <input
              id="search-skill-input"
              type="text"
              placeholder="Search taxonomy (e.g. Docker, Python)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {isSearching && (
            <p style={{ fontSize: "14px", color: "var(--muted)", marginTop: "4px" }}>
              Searching taxonomy...
            </p>
          )}

          {searchResults.length > 0 && (
            <div
              style={{
                border: "1px solid var(--border)",
                backgroundColor: "#fff",
                borderRadius: "3px",
                maxWidth: "480px",
                marginTop: "4px",
                maxHeight: "180px",
                overflowY: "auto",
              }}
            >
              {searchResults.map((item) => (
                <div
                  key={item.skill_id}
                  style={{
                    padding: "6px 10px",
                    borderBottom: "1px solid #f0eee8",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span>
                    {item.name}{" "}
                    <span style={{ fontSize: "12px", color: "var(--muted)" }}>
                      ({item.category})
                    </span>
                  </span>
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => handleAddSkill(item)}
                  >
                    add
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {hasSkillEdits && (
          <div style={{ marginTop: "14px", marginBottom: "20px" }}>
            <button
              type="button"
              onClick={handleRecalculate}
              disabled={isRecalculating}
            >
              {isRecalculating ? "Recalculating..." : "Recalculate"}
            </button>
          </div>
        )}
      </section>

      {/* c. Skills the role needs */}
      <section data-tour="skills-needed">
        <h2>Skills the role needs</h2>
        <table>
          <thead>
            <tr>
              <th style={{ width: "25%" }}>Skill</th>
              <th style={{ width: "35%" }}>How common in postings</th>
              <th style={{ width: "20%" }}>You have it</th>
              <th style={{ width: "20%" }}>Points</th>
            </tr>
          </thead>
          <tbody>
            {roleRows.map((row) => {
              const pct = Math.min(100, Math.max(5, Math.round(row.weight * 100)));
              return (
                <tr key={row.skill_id}>
                  <td>
                    <strong>{row.skill}</strong>
                  </td>
                  <td>
                    <span style={{ minWidth: "36px", display: "inline-block" }}>
                      {pct}%
                    </span>
                    <div className="bar-container" aria-hidden="true">
                      <div className="bar-fill" style={{ width: `${pct}%` }} />
                    </div>
                  </td>
                  <td>
                    {row.haveIt === "Partly" ? (
                      <span>
                        Partly
                        <Hint label="What's this?">
                          We count a skill as partly covered when you list a closely related one, such as PyTorch for TensorFlow.
                        </Hint>
                      </span>
                    ) : (
                      row.haveIt
                    )}
                  </td>
                  <td>{row.pointsText}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      {/* d. What to learn first */}
      <section data-tour="what-to-learn">
        <h2>What to learn first</h2>
        {result.learning_path.length === 0 ? (
          <p>No missing skills required for this role.</p>
        ) : (
          <ol>
            {result.learning_path.map((step) => (
              <li key={step.step_number}>
                <strong>{step.primary_skill_name}</strong>:{" "}
                <a href={step.course.url} target="_blank" rel="noopener noreferrer">
                  {step.course.title}
                </a>{" "}
                ({step.course.platform}, {Math.round(step.course.duration_hours)} hours).{" "}
                {step.why_chosen} Adds about {Math.round(step.score_gain)} points.
              </li>
            ))}
          </ol>
        )}
        <div style={{ marginTop: "16px" }}>
          <button
            type="button"
            onClick={() => {
              if (typeof window !== "undefined") {
                try {
                  sessionStorage.setItem("skillgap_target_role", targetRole);
                  sessionStorage.setItem(
                    "skillgap_result",
                    JSON.stringify({
                      target_role: targetRole,
                      extracted_skills: currentSkills,
                      missing: result.missing,
                    })
                  );
                } catch (e) {
                  console.warn("Could not save analysis result to sessionStorage:", e);
                }
                window.location.href = "/resume-builder?from=analysis";
              }
            }}
            style={{
              border: "1px solid var(--accent)",
              backgroundColor: "var(--accent)",
              color: "#ffffff",
              padding: "8px 16px",
              borderRadius: "4px",
              fontSize: "14px",
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Build an updated resume
          </button>
        </div>
      </section>

      {/* e. Try it (What-if simulation) */}
      <section data-tour="try-it">
        <h2>Try it</h2>
        <p>Select skills you plan to learn to see your updated score:</p>
        <div style={{ display: "flex", gap: "24px", flexWrap: "wrap", alignItems: "flex-start" }}>
          <div style={{ flex: "1 1 300px" }}>
            {result.missing.length === 0 ? (
              <p>You already possess all required skills for this role.</p>
            ) : (
              result.missing.map((ms: MissingSkillItem) => (
                <div key={ms.skill_id} style={{ marginBottom: "8px" }}>
                  <label style={{ display: "inline-flex", alignItems: "center", cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={selectedWhatIfSkills.includes(ms.skill_id)}
                      onChange={() => handleWhatIfToggle(ms.skill_id)}
                      style={{ marginRight: "8px", width: "auto" }}
                    />
                    <span>
                      {ms.skill} (+{Math.round(ms.gain_if_learned)} pts)
                    </span>
                  </label>
                </div>
              ))
            )}
          </div>

          <div
            style={{
              flex: "1 1 240px",
              padding: "14px 16px",
              border: "1px solid var(--border)",
              borderRadius: "4px",
              backgroundColor: "#fff",
            }}
          >
            {isWhatIfLoading ? (
              <p style={{ margin: 0, color: "var(--muted)" }}>Calculating new score...</p>
            ) : whatIfData ? (
              <div>
                <div style={{ fontSize: "18px", fontWeight: 600 }}>
                  New score: {Math.round(whatIfData.new_score)}% (+
                  {Math.round(whatIfData.delta_final)})
                </div>
                <div style={{ fontSize: "14px", color: "var(--muted)", marginTop: "4px" }}>
                  Coverage: {Math.round(whatIfData.new_coverage)}% (+
                  {Math.round(whatIfData.delta_coverage)})
                </div>
              </div>
            ) : (
              <p style={{ margin: 0, color: "var(--muted)", fontSize: "14px" }}>
                Check any skill to simulate your score improvement.
              </p>
            )}
          </div>
        </div>
      </section>

      {/* f. Compare with other roles */}
      <section data-tour="compare-roles">
        <h2>Compare with other roles</h2>
        {!compareData ? (
          <div>
            <button
              type="button"
              onClick={handleLoadComparisons}
              disabled={isComparing}
            >
              {isComparing ? "Loading comparisons..." : "Load role comparisons"}
            </button>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th style={{ width: "35%" }}>Role</th>
                <th style={{ width: "20%" }}>Match score</th>
                <th style={{ width: "20%" }}>Coverage</th>
                <th style={{ width: "25%" }}>Missing skills</th>
              </tr>
            </thead>
            <tbody>
              {compareData.ranked_roles.map((item) => (
                <tr key={item.role}>
                  <td>
                    <strong>{item.role}</strong>
                  </td>
                  <td>{Math.round(item.final_score)}%</td>
                  <td>{Math.round(item.coverage_score)}%</td>
                  <td>{item.missing_skills_count} skills</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* Honest Footnote */}
      <div className="footnote">
        Scores come from skill demand in job postings. Use them as a guide, not a verdict.
      </div>
    </div>
  );
}
