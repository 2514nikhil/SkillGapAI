"use client";

import React from "react";
import Link from "next/link";
import Tour from "@/components/Tour";
import { TourStep } from "@/lib/tourUtils";
import { COPY } from "@/lib/copy";

const helpTourSteps: TourStep[] = [
  {
    target: '[data-tour="help-intro"]',
    title: "Help & Troubleshooting",
    body: "Find clear answers to common questions about parsing, matching scores, and privacy.",
    placement: "bottom",
  },
  {
    target: '[data-tour="help-faq"]',
    title: "Common Questions",
    body: "Each topic covers a specific issue. No chatbots or complicated settings.",
    placement: "top",
  },
];

export default function HelpPage() {
  const handleReplayTour = (e: React.MouseEvent) => {
    e.preventDefault();
    window.dispatchEvent(new CustomEvent("skillgap-start-tour"));
  };

  return (
    <div>
      <Tour steps={helpTourSteps} storageKey="skillgap_tour_help_v1" />

      <div style={{ marginBottom: "16px" }}>
        <Link href="/">Back to analyzer</Link>
      </div>

      <div data-tour="help-intro">
        <h1>Help &amp; Troubleshooting</h1>
        <p>
          Quick answers to common questions about uploading your resume, understanding scores, and navigating the system.
        </p>
      </div>

      <div data-tour="help-faq" style={{ marginTop: "28px" }}>
        <section style={{ marginBottom: "24px" }}>
          <h2>My PDF says no text found.</h2>
          <p>
            Your PDF is likely a scanned image or flattened graphic without an embedded text layer. SkillGap requires actual text to extract skills. To resolve this, export your document directly to PDF from Microsoft Word, Google Docs, or LaTeX, or upload your resume as a DOCX file.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>The skills found are wrong or incomplete.</h2>
          <p>
            You have full control over the extracted skills. On the results page under &ldquo;Skills we found in your resume&rdquo;, click &ldquo;remove&rdquo; next to any irrelevant skill, or use the search box to add any missing skills directly from the canonical taxonomy. Then click &ldquo;Recalculate&rdquo; to refresh your score immediately.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>What does the score mean?</h2>
          <p>
            {COPY.scoreExplanation} Read the complete breakdown on our{" "}
            <Link href="/about">About page</Link>.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>Why does a skill I have show as missing?</h2>
          <p>
            The skill might be phrased differently in your resume or described inside project narratives that did not match an exact alias. You can easily add it manually using the taxonomy search box on the results page.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>Is my resume stored?</h2>
          <p>{COPY.privacyStatement}</p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>The page says the server is not responding.</h2>
          <p>
            {COPY.serverWakingMessage} Free hosting tiers put the service into standby during inactivity. The server usually takes 45 to 60 seconds to wake up and load models into memory.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>What are the system limitations?</h2>
          <p>{COPY.limitationsStatement}</p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>How do I see the tour again?</h2>
          <p>
            You can reopen the interface tour on any page at any time by clicking the &ldquo;?&rdquo; button in the top right corner of the header and selecting &ldquo;Show me around this page&rdquo;.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>Can the site write my resume for me?</h2>
          <p>
            Yes! Our builder helps you craft a clean, ATS-safe resume grounded strictly in your real skills and experience. The AI assistant polishes your bullet points and projects without inventing facts, dates, tools, or metrics. Visit the{" "}
            <Link href="/resume-builder">Resume builder page</Link> to start building or editing.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>Is my resume saved?</h2>
          <p>
            Only in your browser&apos;s local storage. Your resume data is never stored on our servers, never saved to databases, and never logged. You can clear your draft anytime using the &ldquo;Clear everything&rdquo; button.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>Why did the AI not change my bullet?</h2>
          <p>
            Our AI assistant enforces a strict honesty rule: it is strictly forbidden from adding tools, technologies, metrics, or factual claims you did not provide. If a bullet cannot be safely improved without inventing details, the system preserves your original wording.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>Which template should I choose?</h2>
          <p>
            All templates are single-column and 100% ATS-safe. Choose <strong>Classic</strong> for traditional serif styling, <strong>Compact</strong> for a tight sans-serif layout ideal for 1-page resumes, or <strong>Technical</strong> to emphasize skills and project portfolios above experience.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>Do I need to add social links?</h2>
          <p>
            No, all social profiles and links are completely optional. You can include links to GitHub, LinkedIn, or personal portfolios, but none are required to generate or export your resume.
          </p>
        </section>

        <section style={{ marginBottom: "24px" }}>
          <h2>The AI assistant is unavailable.</h2>
          <p>
            When running on free cloud hosting or when the local Ollama daemon is stopped, SkillGap automatically falls back to our deterministic rule-based assistant. Editing, ATS lint checks, and local auto-save continue to function uninterrupted.
          </p>
        </section>
      </div>

      <div style={{ marginTop: "36px", paddingTop: "16px", borderTop: "1px solid var(--border)" }}>
        <button
          type="button"
          className="link-button"
          onClick={handleReplayTour}
        >
          Replay the tour for this page
        </button>
      </div>
    </div>
  );
}
