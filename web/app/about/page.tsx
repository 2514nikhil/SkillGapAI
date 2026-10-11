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
        Looking to explore upcoming features? Check the{" "}
        <Link href="/resume-builder">Resume builder page</Link> or visit the{" "}
        <Link href="/help">Help &amp; Troubleshooting guide</Link>.
      </p>
    </div>
  );
}
