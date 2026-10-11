import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Resume builder - SkillGap",
  robots: {
    index: false,
    follow: false,
  },
};

export default function ResumeBuilderPage() {
  const isBuilderEnabled = process.env.NEXT_PUBLIC_RESUME_BUILDER_ENABLED === "true";

  if (isBuilderEnabled) {
    // TODO: When NEXT_PUBLIC_RESUME_BUILDER_ENABLED is true, mount the real
    // Resume Builder workspace component here (e.g. <ResumeBuilderWorkspace />).
    return (
      <div>
        <h1>Make your resume with AI</h1>
        <p>Real resume builder component is not yet implemented.</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: "16px" }}>
        <Link href="/">Back to analyzer</Link>
      </div>

      <h1>Make your resume with AI</h1>

      <div
        style={{
          border: "1px solid #d9d5cc",
          borderRadius: "4px",
          padding: "14px",
          backgroundColor: "#fffdf9",
          marginTop: "16px",
          marginBottom: "24px",
        }}
      >
        <strong>Upcoming Feature:</strong> This capability is actively in development as part of our next major platform release.
      </div>

      <h2>What it will do</h2>
      <ul>
        <li>Turn your skills and experience into a clean, ready-to-send resume.</li>
        <li>Use the gaps found in your analysis to suggest what to add.</li>
        <li>Let you edit everything before you download it.</li>
      </ul>

      <p style={{ marginTop: "20px" }}>
        Coming soon in a major update. For now, you can explore role requirements and analyze your resume against any target role.
      </p>

      <p>
        <Link href="/">Go to the analyzer</Link>
      </p>
    </div>
  );
}
