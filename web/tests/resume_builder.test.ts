import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

test("Resume builder page: shows 'Under construction' message when feature flag is false", async () => {
  const pagePath = path.resolve("app/resume-builder/page.tsx");
  const content = fs.readFileSync(pagePath, "utf-8");

  // Verify feature flag check exists
  assert.match(
    content,
    /process\.env\.NEXT_PUBLIC_RESUME_BUILDER_ENABLED\s*===\s*["']true["']/,
    "Page should check NEXT_PUBLIC_RESUME_BUILDER_ENABLED"
  );

  // Verify placeholder message
  assert.ok(
    content.includes("This capability is actively in development as part of our next major platform release."),
    "Must include upcoming release notice"
  );

  // Verify 'What it will do' heading and 3 bullet points
  assert.ok(content.includes("What it will do"), "Must include heading 'What it will do'");
  assert.ok(
    content.includes("Turn your skills and experience into a clean, ready-to-send resume."),
    "Must include bullet 1"
  );
  assert.ok(
    content.includes("Use the gaps found in your analysis to suggest what to add."),
    "Must include bullet 2"
  );
  assert.ok(
    content.includes("Let you edit everything before you download it."),
    "Must include bullet 3"
  );

  // Verify 'Go to the analyzer' link
  assert.ok(
    content.includes("Go to the analyzer"),
    "Must include 'Go to the analyzer' link text"
  );
  assert.match(
    content,
    /<Link\s+href=["']\/["']>Go to the analyzer<\/Link>/,
    "Link must point to /"
  );

  // Verify robots noindex metadata
  assert.match(
    content,
    /robots:\s*{\s*index:\s*false/m,
    "Metadata must set robots index to false (noindex)"
  );

  // Verify TODO comment exists for mounting real builder
  assert.ok(
    content.includes("// TODO: When NEXT_PUBLIC_RESUME_BUILDER_ENABLED is true"),
    "Must include TODO comment for mounting real builder"
  );
});

test("Navigation links: Header, Result page, and Help page link to /resume-builder", () => {
  // 1. Header
  const headerPath = path.resolve("components/Header.tsx");
  const headerContent = fs.readFileSync(headerPath, "utf-8");
  assert.match(
    headerContent,
    /<Link\s+href=["']\/resume-builder["']>Resume builder<\/Link>/,
    "Header must contain link to /resume-builder labeled 'Resume builder'"
  );

  // 2. Result page
  const resultPath = path.resolve("app/result/page.tsx");
  const resultContent = fs.readFileSync(resultPath, "utf-8");
  assert.match(
    resultContent,
    /Build an updated resume/i,
    "Result page must contain action labeled 'Build an updated resume'"
  );

  // 3. Help page
  const helpPath = path.resolve("app/help/page.tsx");
  const helpContent = fs.readFileSync(helpPath, "utf-8");
  assert.match(
    helpContent,
    /<Link\s+href=["']\/resume-builder["']>Resume builder page<\/Link>/,
    "Help page must contain link to /resume-builder labeled 'Resume builder page'"
  );
});

test("UI Rules check: No prohibited elements in /resume-builder", () => {
  const pagePath = path.resolve("app/resume-builder/page.tsx");
  const content = fs.readFileSync(pagePath, "utf-8");

  // Check no form, email signup, countdown, icons, animation
  assert.ok(!content.includes("<form"), "No form element allowed");
  assert.ok(!content.includes("<input"), "No input element allowed");
  assert.ok(!content.includes("notify me"), "No notify me button allowed");
  assert.ok(!content.includes("countdown"), "No countdown allowed");
  assert.ok(!content.includes("box-shadow"), "No box-shadow allowed");
});
