import {
  AIImproveBulletResponse,
  AIPolishProjectResponse,
  AISuggestSkillsResponse,
  AISummaryResponse,
  LintIssue,
  Resume,
  SocialPlatform,
  TailorResponse,
  TechCatalog,
} from "./resumeTypes";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function requestJson<T>(url: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, options);
  } catch {
    throw new ApiError("Server not responding. Editing and local auto-save continue to work.");
  }

  if (!res.ok) {
    let errorDetail = `Server error (${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) {
        errorDetail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Non-JSON response
    }
    throw new ApiError(errorDetail, res.status);
  }

  return (await res.json()) as T;
}

export async function fetchTechCatalog(): Promise<TechCatalog> {
  return requestJson<TechCatalog>(`${API_BASE}/resume/catalog`);
}

export async function fetchSocialPlatforms(): Promise<SocialPlatform[]> {
  return requestJson<SocialPlatform[]>(`${API_BASE}/resume/socials`);
}

export async function lintResume(resume: Resume): Promise<LintIssue[]> {
  return requestJson<LintIssue[]>(`${API_BASE}/resume/lint`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resume),
  });
}

export async function renderHtmlPreview(
  resume: Resume,
  template: "classic" | "compact" | "technical" = "classic",
  pageSize: "A4" | "Letter" = "A4"
): Promise<string> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/resume/render`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume,
        format: "html",
        template,
        page_size: pageSize,
      }),
    });
  } catch {
    throw new ApiError("Server not responding. Editing and local auto-save continue to work.");
  }

  if (!res.ok) {
    throw new ApiError(`Preview render error (${res.status})`, res.status);
  }

  return res.text();
}

export async function downloadResume(
  resume: Resume,
  format: "pdf" | "docx" | "md" | "txt" | "json",
  template: "classic" | "compact" | "technical" = "classic",
  pageSize: "A4" | "Letter" = "A4"
): Promise<Blob> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/resume/render`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume,
        format,
        template,
        page_size: pageSize,
      }),
    });
  } catch {
    throw new ApiError("Server not responding. Export unavailable right now.");
  }

  if (!res.ok) {
    let errorDetail = `Failed to generate ${format.toUpperCase()}`;
    try {
      const data = await res.json();
      if (data?.detail) errorDetail = data.detail;
    } catch {
      // Ignored
    }
    throw new ApiError(errorDetail, res.status);
  }

  return res.blob();
}

export async function importResumeFile(file: File): Promise<{ resume: Resume; needs_review: Array<{ field: string; note: string }> }> {
  const formData = new FormData();
  formData.append("file", file);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/resume/import`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new ApiError("Server not responding. Import failed.");
  }

  if (!res.ok) {
    let errorDetail = "Failed to import resume document";
    try {
      const data = await res.json();
      if (data?.detail) errorDetail = data.detail;
    } catch {
      // Ignored
    }
    throw new ApiError(errorDetail, res.status);
  }

  return res.json();
}

export async function aiImproveBullet(
  text: string,
  context?: { role?: string; company?: string; skills?: string[] }
): Promise<AIImproveBulletResponse> {
  return requestJson<AIImproveBulletResponse>(`${API_BASE}/resume/ai/bullet`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, context }),
  });
}

export async function aiDraftSummary(resume: Resume): Promise<AISummaryResponse> {
  return requestJson<AISummaryResponse>(`${API_BASE}/resume/ai/summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resume),
  });
}

export async function aiPolishProject(
  name: string,
  tech: string[],
  notes: string
): Promise<AIPolishProjectResponse> {
  return requestJson<AIPolishProjectResponse>(`${API_BASE}/resume/ai/project`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, tech, notes }),
  });
}

export async function aiSuggestSkills(resume: Resume): Promise<AISuggestSkillsResponse> {
  return requestJson<AISuggestSkillsResponse>(`${API_BASE}/resume/ai/suggest-skills`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resume),
  });
}

export async function aiTailor(resume: Resume, target: string): Promise<TailorResponse> {
  return requestJson<TailorResponse>(`${API_BASE}/resume/ai/tailor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume, target }),
  });
}
