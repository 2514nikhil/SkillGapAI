import {
  AnalyzeResponse,
  CompareResponse,
  RoleItem,
  SkillItem,
  WhatIfResponse,
} from "./types";
import { COPY } from "./copy";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/**
 * Robust fetch wrapper that gracefully maps cold start, network, or server timeouts
 * to a friendly explanation message.
 */
async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  try {
    const res = await fetch(url, init);
    // If backend is waking up or gateway timeout (502, 503, 504)
    if (res.status === 502 || res.status === 503 || res.status === 504) {
      throw new Error(COPY.serverWakingMessage);
    }
    return res;
  } catch (err: unknown) {
    if (err instanceof Error && err.message === COPY.serverWakingMessage) {
      throw err;
    }
    // Network errors, connection refused, or cold start downtime
    throw new Error(COPY.serverWakingMessage);
  }
}

/**
 * Helper to parse backend error responses cleanly.
 */
async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `Server error (${res.status})`;
    try {
      const data = await res.json();
      if (data && data.detail) {
        if (typeof data.detail === "string") {
          errorMsg = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorMsg = data.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(", ");
        }
      }
    } catch {
      // Body not json
    }
    throw new Error(errorMsg);
  }
  return res.json() as Promise<T>;
}

export async function getRoles(): Promise<RoleItem[]> {
  const res = await apiFetch(`${API_BASE}/roles`, { cache: "no-store" });
  return handleResponse<RoleItem[]>(res);
}

export async function searchSkills(query: string): Promise<SkillItem[]> {
  const res = await apiFetch(`${API_BASE}/skills?q=${encodeURIComponent(query)}&limit=15`, {
    cache: "no-store",
  });
  return handleResponse<SkillItem[]>(res);
}

export async function analyzeResume(formData: FormData): Promise<AnalyzeResponse> {
  const res = await apiFetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<AnalyzeResponse>(res);
}

export async function simulateWhatIf(payload: {
  analysis_id?: string;
  skills?: string[];
  role: string;
  add: string[];
}): Promise<WhatIfResponse> {
  const res = await apiFetch(`${API_BASE}/whatif`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<WhatIfResponse>(res);
}

export async function compareRoles(payload: {
  analysis_id?: string;
  skills?: string[];
  roles?: string[];
}): Promise<CompareResponse> {
  const res = await apiFetch(`${API_BASE}/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<CompareResponse>(res);
}
