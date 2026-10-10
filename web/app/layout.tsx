import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "SkillGap - Job-Skill Gap Analyzer",
  description: "Deterministic, explainable job-skill gap analyzer and learning roadmap.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="site-header-inner">
            <Link href="/" className="site-brand">
              <span className="site-brand-title">SkillGap</span>
              <span className="site-brand-badge">Deterministic Job-Skill Gap Analyzer</span>
            </Link>
            <nav className="site-nav">
              <Link href="/">Analyze Resume</Link>
              <a
                href="https://github.com/2514nikhil"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub
              </a>
            </nav>
          </div>
        </header>

        <main className="container">{children}</main>

        <footer className="site-footer">
          <div className="site-footer-inner">
            <div className="footer-credits">
              <strong>SkillGap</strong> &mdash; Built &amp; Designed by <strong>Nikhil Maghodiya</strong>
            </div>
            <div className="footer-links">
              <span>
                <strong>Developer:</strong> Nikhil Maghodiya
              </span>
              <span>
                <strong>Email:</strong>{" "}
                <a href="mailto:nikhilmaghodiya25@gmail.com">nikhilmaghodiya25@gmail.com</a>
              </span>
              <span>
                <strong>GitHub:</strong>{" "}
                <a
                  href="https://github.com/2514nikhil"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  github.com/2514nikhil
                </a>
              </span>
            </div>
            <div className="footer-note">
              SkillGap uses transparent mathematical scoring, empirical labor market demand profiles, and local ML models with zero black-box AI hallucinations.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
