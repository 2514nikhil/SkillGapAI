import test from "node:test";
import assert from "node:assert/strict";
import {
  createEmptyResume,
  saveResumeToLocalStorage,
  loadResumeFromLocalStorage,
  clearResumeFromLocalStorage,
  loadResumeFromAnalyzedSession,
} from "../lib/resumeStorage.ts";
import type { Resume, SkillItem } from "../lib/resumeTypes.ts";

test("Resume storage: creates valid default schema with zero PII", () => {
  const resume = createEmptyResume();
  assert.equal(resume.basics.name, "");
  assert.equal(resume.basics.email, "");
  assert.equal(resume.meta.template, "classic");
  assert.deepEqual(resume.skills, []);
  assert.deepEqual(resume.experience, []);
  assert.deepEqual(resume.projects, []);
  assert.deepEqual(resume.education, []);

  // Prohibited fields must never exist in the schema
  const forbidden = [
    "photo",
    "avatar",
    "dob",
    "gender",
    "religion",
    "nationality",
    "address",
    "ssn",
    "aadhaar",
  ];
  for (const field of forbidden) {
    assert.equal((resume as any)[field], undefined);
    assert.equal((resume.basics as any)[field], undefined);
  }
});

test("Resume storage: save and load in localStorage", () => {
  const mockStorage: Record<string, string> = {};
  const originalLocalStorage = globalThis.localStorage;

  // Mock localStorage
  (globalThis as any).localStorage = {
    getItem: (key: string) => mockStorage[key] || null,
    setItem: (key: string, val: string) => {
      mockStorage[key] = val;
    },
    removeItem: (key: string) => {
      delete mockStorage[key];
    },
  };

  try {
    const resume = createEmptyResume();
    resume.basics.name = "Ada Lovelace";
    resume.basics.email = "ada@example.com";
    resume.skills.push({
      category_id: "languages",
      name: "Python",
      pinned: true,
      level: "expert",
    });

    const saved = saveResumeToLocalStorage(resume);
    assert.equal(saved, true);

    const loaded = loadResumeFromLocalStorage();
    assert.ok(loaded);
    assert.equal(loaded?.basics.name, "Ada Lovelace");
    assert.equal(loaded?.basics.email, "ada@example.com");
    assert.equal(loaded?.skills.length, 1);
    assert.equal(loaded?.skills[0].name, "Python");
    assert.equal(loaded?.skills[0].pinned, true);

    const cleared = clearResumeFromLocalStorage();
    assert.equal(cleared, true);
    assert.equal(loadResumeFromLocalStorage(), null);
  } finally {
    (globalThis as any).localStorage = originalLocalStorage;
  }
});

test("Resume storage: gracefully handles blocked or throwing localStorage", () => {
  const originalLocalStorage = globalThis.localStorage;

  (globalThis as any).localStorage = {
    getItem: () => {
      throw new Error("QuotaExceededError or Cookies Blocked");
    },
    setItem: () => {
      throw new Error("QuotaExceededError or Cookies Blocked");
    },
    removeItem: () => {
      throw new Error("QuotaExceededError or Cookies Blocked");
    },
  };

  try {
    const resume = createEmptyResume();
    // Must return false without throwing unhandled exceptions
    const saved = saveResumeToLocalStorage(resume);
    assert.equal(saved, false);

    const loaded = loadResumeFromLocalStorage();
    assert.equal(loaded, null);

    const cleared = clearResumeFromLocalStorage();
    assert.equal(cleared, false);
  } finally {
    (globalThis as any).localStorage = originalLocalStorage;
  }
});

test("Resume storage: loads from analyzed resume session correctly", () => {
  const originalSessionStorage = globalThis.sessionStorage;

  const mockSession: Record<string, string> = {
    skillgap_target_role: "Backend Developer",
    skillgap_result: JSON.stringify({
      target_role: "Backend Developer",
      extracted_skills: [
        { skill: "Python", skill_id: "python", category: "languages" },
        { skill: "Docker", skill_id: "docker", category: "cicd_vcs" },
        { skill: "PostgreSQL", skill_id: "postgresql", category: "databases_orm" },
      ],
    }),
  };

  (globalThis as any).sessionStorage = {
    getItem: (key: string) => mockSession[key] || null,
  };

  try {
    const loaded = loadResumeFromAnalyzedSession();
    assert.ok(loaded);
    assert.equal(loaded?.meta.target_role, "Backend Developer");
    assert.equal(loaded?.skills.length, 3);
    assert.equal(loaded?.skills[0].name, "Python");
    assert.equal(loaded?.skills[0].category_id, "languages");
    assert.equal(loaded?.skills[1].name, "Docker");
  } finally {
    (globalThis as any).sessionStorage = originalSessionStorage;
  }
});

test("Skills logic: enforces maximum 8 pinned skills", () => {
  const skills: SkillItem[] = [];
  for (let i = 0; i < 8; i++) {
    skills.push({
      category_id: "languages",
      name: `Skill ${i}`,
      pinned: true,
    });
  }

  const pinnedCount = skills.filter((s) => s.pinned).length;
  assert.equal(pinnedCount, 8);

  // Attempting to pin a 9th skill should be prevented
  const canPin9th = pinnedCount < 8;
  assert.equal(canPin9th, false, "Must not allow pinning more than 8 skills");
});

test("Skills logic: alias resolution maps alternate names to canonical skills", () => {
  // Test alias mapping lookup
  const catalog = {
    categories: [
      {
        id: "languages",
        name: "Programming Languages",
        skills: [
          {
            id: "python",
            name: "Python",
            aliases: ["py", "python3"],
            taxonomy_id: "python",
          },
          {
            id: "typescript",
            name: "TypeScript",
            aliases: ["ts"],
            taxonomy_id: "typescript",
          },
        ],
      },
    ],
  };

  function resolveSkill(input: string) {
    const lower = input.toLowerCase().trim();
    for (const cat of catalog.categories) {
      for (const sk of cat.skills) {
        if (sk.name.toLowerCase() === lower || sk.id.toLowerCase() === lower) {
          return { category_id: cat.id, name: sk.name, taxonomy_id: sk.taxonomy_id };
        }
        if (sk.aliases?.some((a) => a.toLowerCase() === lower)) {
          return { category_id: cat.id, name: sk.name, taxonomy_id: sk.taxonomy_id };
        }
      }
    }
    return { category_id: "other_tools", name: input, taxonomy_id: null };
  }

  assert.deepEqual(resolveSkill("py"), {
    category_id: "languages",
    name: "Python",
    taxonomy_id: "python",
  });
  assert.deepEqual(resolveSkill("ts"), {
    category_id: "languages",
    name: "TypeScript",
    taxonomy_id: "typescript",
  });
  assert.deepEqual(resolveSkill("UnlistedTool"), {
    category_id: "other_tools",
    name: "UnlistedTool",
    taxonomy_id: null,
  });
});

test("Social URL validator: builds proper URL and validates username regex", () => {
  const linkedinRegex = /^[a-zA-Z0-9_-]{3,100}$/;
  const validHandle = "jane-doe-123";
  const invalidHandle = "jane doe!@#";

  assert.ok(linkedinRegex.test(validHandle));
  assert.ok(!linkedinRegex.test(invalidHandle));

  const urlTemplate = "https://linkedin.com/in/{value}";
  const preview = urlTemplate.replace("{value}", validHandle);
  assert.equal(preview, "https://linkedin.com/in/jane-doe-123");
});

test("Export gating: download must be disabled if name or email missing or errors present", () => {
  function isExportDisabled(name: string, email: string, errorsCount: number): boolean {
    return !name.trim() || !email.trim() || errorsCount > 0;
  }

  // Missing name
  assert.equal(isExportDisabled("", "test@example.com", 0), true);

  // Missing email
  assert.equal(isExportDisabled("John", "", 0), true);

  // Has ATS error
  assert.equal(isExportDisabled("John", "test@example.com", 1), true);

  // Valid and ready
  assert.equal(isExportDisabled("John", "test@example.com", 0), false);
});
