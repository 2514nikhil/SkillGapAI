/**
 * Tour and help system utility functions.
 * Hand-built for SkillGap. Deterministic, safe with blocked localStorage.
 */

export interface TourStep {
  target: string; // CSS selector, e.g. '[data-tour="resume-file"]'
  title: string;
  body: string;
  placement?: "bottom" | "top" | "auto";
}

/**
 * Filter steps whose target elements actually exist in the current DOM.
 * If a target does not exist, the step is skipped silently.
 */
export function filterValidSteps(
  steps: TourStep[],
  doc: { querySelector: (selector: string) => any } | null = typeof document !== "undefined" ? document : null
): TourStep[] {
  if (!doc) return [];
  return steps.filter((step) => {
    try {
      const el = doc.querySelector(step.target);
      return Boolean(el);
    } catch {
      return false;
    }
  });
}

/**
 * Safely check if a tour flag has been set in localStorage.
 * Wrapped in try/catch to gracefully handle environments where storage is blocked.
 */
export function hasVisitedTour(key: string, customStorage?: any): boolean {
  try {
    const storage = customStorage || (typeof window !== "undefined" ? window.localStorage : null);
    if (!storage) return false;
    return storage.getItem(key) === "true";
  } catch {
    return false;
  }
}

/**
 * Safely set a tour flag in localStorage.
 * Wrapped in try/catch.
 */
export function setVisitedTour(key: string, customStorage?: any): void {
  try {
    const storage = customStorage || (typeof window !== "undefined" ? window.localStorage : null);
    if (storage) {
      storage.setItem(key, "true");
    }
  } catch {
    // Ignore storage failure (e.g. private browsing with blocked storage)
  }
}
