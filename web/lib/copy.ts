/**
 * Single source of truth for all explanatory and policy texts.
 * Shared between /about, /help, and tooltips/hints to guarantee zero contradiction.
 */

export const COPY = {
  // How the score is calculated
  scoreExplanation:
    "The overall match score reflects how much of the target role's empirical skill demand your resume covers, weighted by how frequently each skill appears in actual job postings, combined with semantic text alignment. It is designed as a practical learning benchmark, not an automated hiring verdict.",

  scoringBreakdown: {
    coverage:
      "Empirical skill coverage (70% weight): Evaluates which skills required by the role appear in your resume, weighted by their market prevalence across real job postings.",
    semantic:
      "Semantic alignment (30% weight): Dense embedding cosine similarity computed with SentenceTransformers (MiniLM) between your resume text and the role demand profile.",
  },

  // Privacy and data handling
  privacyStatement:
    "Your resume file and its parsed text are processed strictly in memory during the request and immediately discarded. SkillGap does not persist your resume document, personal contact details, or profile data to any database or disk.",

  // Known limitations
  limitationsStatement:
    "SkillGap relies on explicit skill mentions and semantic vector similarity. Scanned image-only PDFs without an embedded text layer cannot be parsed. The system does not assess human soft skills, work culture fit, or portfolio depth. Scores are a roadmap for skill improvement, not a hiring decision.",

  // Where the data comes from
  dataSourcesStatement:
    "Role demand profiles and skill frequencies are extracted from thousands of real job postings and verified industry resumes across 30 roles. The skills taxonomy contains over 430 canonical skills with alias normalization.",

  // Server startup / cold-start explanation
  serverWakingMessage:
    "The server is waking up. Try again in a minute.",
};
