import type { Resume, SkillItem } from "./resumeTypes.ts";

const STORAGE_KEY = "skillgap_resume_draft";

function getLocalStorage(): Storage | null {
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      return window.localStorage;
    }
    if (typeof localStorage !== "undefined") {
      return localStorage;
    }
  } catch {
    return null;
  }
  return null;
}

function getSessionStorage(): Storage | null {
  try {
    if (typeof window !== "undefined" && window.sessionStorage) {
      return window.sessionStorage;
    }
    if (typeof sessionStorage !== "undefined") {
      return sessionStorage;
    }
  } catch {
    return null;
  }
  return null;
}

export function createEmptyResume(): Resume {
  return {
    meta: {
      template: "classic",
      target_role: "",
    },
    basics: {
      name: "",
      email: "",
      headline: "",
      phone: "",
      location: {
        city: "",
        region_country: "",
      },
      links: [
        { platform_id: "linkedin", value: "" },
        { platform_id: "github", value: "" },
        { platform_id: "portfolio", value: "" },
      ],
    },
    summary: "",
    skills: [],
    experience: [],
    projects: [],
    education: [],
    certifications: [],
    publications: [],
    custom_sections: [],
  };
}

export function saveResumeToLocalStorage(resume: Resume): boolean {
  try {
    const storage = getLocalStorage();
    if (!storage) return false;
    storage.setItem(STORAGE_KEY, JSON.stringify(resume));
    return true;
  } catch (err) {
    console.warn("Could not save resume to localStorage:", err);
    return false;
  }
}

export function loadResumeFromLocalStorage(): Resume | null {
  try {
    const storage = getLocalStorage();
    if (!storage) return null;
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && parsed.basics) {
      return parsed as Resume;
    }
  } catch (err) {
    console.warn("Could not load resume from localStorage:", err);
  }
  return null;
}

export function clearResumeFromLocalStorage(): boolean {
  try {
    const storage = getLocalStorage();
    if (!storage) return false;
    storage.removeItem(STORAGE_KEY);
    return true;
  } catch (err) {
    console.warn("Could not clear resume from localStorage:", err);
    return false;
  }
}

export function hasAnalyzedResumeSession(): boolean {
  try {
    const storage = getSessionStorage();
    if (!storage) return false;
    const stored =
      storage.getItem("skillgap_result") ||
      storage.getItem("analysis_result");
    return Boolean(stored);
  } catch {
    return false;
  }
}

export function loadResumeFromAnalyzedSession(): Resume | null {
  try {
    const storage = getSessionStorage();
    if (!storage) return null;
    const stored =
      storage.getItem("skillgap_result") ||
      storage.getItem("analysis_result");
    if (!stored) return null;

    const data = JSON.parse(stored);
    const targetRole =
      storage.getItem("skillgap_target_role") ||
      data.target_role ||
      "";

    const extracted = data.extracted_skills || [];
    const skills: SkillItem[] = extracted.map(
      (item: { skill?: string; skill_id?: string; category?: string; name?: string }) => ({
        category_id: (item.category || "other_tools").toLowerCase().replace(/[\s&/]+/g, "_"),
        name: item.skill || item.name || item.skill_id || "Unknown Skill",
        taxonomy_id: item.skill_id || null,
        custom: false,
        pinned: false,
      })
    );

    const base = createEmptyResume();
    base.meta.target_role = targetRole;
    base.skills = skills;
    return base;
  } catch (err) {
    console.warn("Failed to load resume from analysis session:", err);
    return null;
  }
}

export function loadAnalyzedMissingSkills(): Array<{
  skill: string;
  skill_id: string;
  tier?: string;
  impact?: number;
}> {
  try {
    const storage = getSessionStorage();
    if (!storage) return [];
    const stored =
      storage.getItem("skillgap_result") ||
      storage.getItem("analysis_result");
    if (!stored) return [];
    const data = JSON.parse(stored);
    return (data.missing || []).map((m: any) => ({
      skill: m.skill || m.name || m.skill_id,
      skill_id: m.skill_id || m.id || "",
      tier: m.tier || "high",
      impact: m.gain_if_learned || m.impact || 0,
    }));
  } catch (err) {
    console.warn("Failed to load missing skills from analysis session:", err);
    return [];
  }
}
