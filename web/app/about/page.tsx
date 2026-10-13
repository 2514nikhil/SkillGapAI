import Link from "next/link";
import { COPY } from "@/lib/copy";

export default function AboutPage() {
  return (
    <div>
      <div style={{ marginBottom: "16px" }}>
        <Link href="/">Back to analyzer</Link>
      </div>

      <h1>About SkillGap</h1>
      <p>
        SkillGap is an open, deterministic job-skill gap analyzer and curriculum recommender designed to help candidates prepare for real-world employment with clear, reproducible metrics.
      </p>

      <h2>How the Score is Calculated</h2>
      <p>{COPY.scoreExplanation}</p>
      <ul>
        <li>
          <strong>{COPY.scoringBreakdown.coverage}</strong>
        </li>
        <li>
          <strong>{COPY.scoringBreakdown.semantic}</strong>
        </li>
      </ul>

      <h2>How the Resume Builder Works</h2>
      <p>
        SkillGap includes a built-in, ATS-first resume builder designed to transform empirical skill gap insights directly into clean, submission-ready resumes without tracking or data leakage.
      </p>
      <ul>
        <li>
          <strong>Stateless &amp; Zero-PII:</strong> Your resume draft is saved only in your browser&apos;s <code>localStorage</code>. No resume text, contact details, or credentials are ever stored on our servers or logged to disk.
        </li>
        <li>
          <strong>The Honesty Rule:</strong> Our AI writing assistant operates under a strict faithfulness contract: it is prohibited from inventing facts, employers, tools, dates, or performance percentages. Every suggested revision requires candidate review and explicit approval via &ldquo;Use this&rdquo;.
        </li>
        <li>
          <strong>Single-Column ATS Templates:</strong> All templates (Classic, Compact, Technical) are single-column HTML/CSS compiled to PDF via WeasyPrint with bundled Liberation and DejaVu fonts, ensuring 100% text readability for corporate applicant tracking systems.
        </li>
      </ul>

      <h2>Deployment &amp; AI Hosting Architecture</h2>
      <p>
        SkillGap is engineered to run seamlessly on standard free cloud hosting (e.g. Render 512MB RAM tier, Hugging Face Spaces). Because local SLMs (such as Qwen 2.5) require GPU or substantial memory, <code>USE_SLM=false</code> is the default in production. In this environment, all writing assistance, bullet improvements, and summary generation are executed by our deterministic, rule-based pipeline with zero cold-start delay.
      </p>

      <h2>Where the Data Comes From</h2>
      <p>{COPY.dataSourcesStatement}</p>

      <h2>Privacy &amp; Data Handling</h2>
      <p>{COPY.privacyStatement}</p>

      <h2>Known Limitations</h2>
      <p>{COPY.limitationsStatement}</p>

      <h2>Credits &amp; Project Info</h2>
      <p>
        Built &amp; designed by <strong>Nikhil Maghodiya</strong>.
      </p>
      <ul>
        <li>
          <strong>Email:</strong>{" "}
          <a href="mailto:nikhilmaghodiya25@gmail.com">nikhilmaghodiya25@gmail.com</a>
        </li>
        <li>
          <strong>GitHub:</strong>{" "}
          <a
            href="https://github.com/2514nikhil"
            target="_blank"
            rel="noopener noreferrer"
          >
            github.com/2514nikhil
          </a>
        </li>
      </ul>

      <p style={{ marginTop: "24px" }}>
        Ready to create or optimize your resume? Check out the{" "}
        <Link href="/resume-builder">Resume builder page</Link> or visit the{" "}
        <Link href="/help">Help &amp; Troubleshooting guide</Link>.
      </p>
    </div>
  );
}
