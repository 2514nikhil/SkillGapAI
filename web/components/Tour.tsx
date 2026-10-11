"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { filterValidSteps, hasVisitedTour, setVisitedTour, TourStep } from "@/lib/tourUtils";

export interface TourProps {
  steps: TourStep[];
  storageKey?: string;
  onFinish?: () => void;
  onSkip?: () => void;
}

interface SpotlightRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

type PopoverStyle = React.CSSProperties;

export default function Tour({
  steps,
  storageKey,
  onFinish,
  onSkip,
}: TourProps) {
  const [isActive, setIsActive] = useState<boolean>(false);
  const [validSteps, setValidSteps] = useState<TourStep[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [spotlight, setSpotlight] = useState<SpotlightRect | null>(null);
  const [popoverStyle, setPopoverStyle] = useState<PopoverStyle>({});
  
  const popoverRef = useRef<HTMLDivElement>(null);
  const prevFocusRef = useRef<HTMLElement | null>(null);

  // Check first-visit on mount
  useEffect(() => {
    // Check if user has already seen this tour
    const alreadyVisited = storageKey ? hasVisitedTour(storageKey) : false;

    // Filter valid steps currently in the DOM
    const initialValid = filterValidSteps(steps);
    setValidSteps(initialValid);

    if (!alreadyVisited && initialValid.length > 0) {
      // Auto start on first visit after slight delay to ensure render
      const timer = setTimeout(() => {
        prevFocusRef.current = document.activeElement as HTMLElement;
        setCurrentIndex(0);
        setIsActive(true);
      }, 250);
      return () => clearTimeout(timer);
    }
  }, [steps, storageKey]);

  // Listen for manual trigger (e.g. from Header "?" button)
  useEffect(() => {
    const handleManualStart = () => {
      const activeValid = filterValidSteps(steps);
      setValidSteps(activeValid);
      if (activeValid.length > 0) {
        prevFocusRef.current = document.activeElement as HTMLElement;
        setCurrentIndex(0);
        setIsActive(true);
      }
    };

    window.addEventListener("skillgap-start-tour", handleManualStart);
    return () => {
      window.removeEventListener("skillgap-start-tour", handleManualStart);
    };
  }, [steps]);

  const closeTour = useCallback((markVisited: boolean = true) => {
    setIsActive(false);
    setSpotlight(null);
    if (markVisited && storageKey) {
      setVisitedTour(storageKey);
    }
    if (prevFocusRef.current) {
      prevFocusRef.current.focus();
    }
  }, [storageKey]);

  // Update spotlight and popover positioning for the current step
  const updatePosition = useCallback(() => {
    if (!isActive || validSteps.length === 0) return;

    const currentStep = validSteps[currentIndex];
    if (!currentStep) return;

    const targetEl = document.querySelector(currentStep.target);
    if (!targetEl) {
      // If target vanished, try skipping to next step
      if (currentIndex + 1 < validSteps.length) {
        setCurrentIndex((i) => i + 1);
      } else {
        closeTour();
      }
      return;
    }

    const rect = targetEl.getBoundingClientRect();
    const pad = 4;

    const spot: SpotlightRect = {
      top: Math.max(0, rect.top - pad),
      left: Math.max(0, rect.left - pad),
      width: rect.width + pad * 2,
      height: rect.height + pad * 2,
    };
    setSpotlight(spot);

    // Compute popover placement
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const isMobile = vw < 600;

    if (isMobile) {
      setPopoverStyle({
        position: "fixed" as any,
        left: "12px",
        right: "12px",
        bottom: "12px",
        maxWidth: "none",
        width: "auto",
      });
      return;
    }

    const popoverWidth = 320;
    const approxPopoverHeight = 180;
    const placement = currentStep.placement || "auto";

    let left = Math.max(12, Math.min(vw - popoverWidth - 16, rect.left));
    let top = 0;

    const spaceBelow = vh - rect.bottom;
    const spaceAbove = rect.top;

    if (placement === "top" || (placement === "auto" && spaceBelow < approxPopoverHeight + 16 && spaceAbove > approxPopoverHeight)) {
      // Place above target
      top = Math.max(12, rect.top - approxPopoverHeight - 8);
    } else {
      // Default place below target
      top = rect.bottom + 8;
      if (top + approxPopoverHeight > vh - 12 && spaceAbove > approxPopoverHeight) {
        top = Math.max(12, rect.top - approxPopoverHeight - 8);
      }
    }

    setPopoverStyle({
      top: `${top}px`,
      left: `${left}px`,
      maxWidth: "320px",
    });
  }, [isActive, validSteps, currentIndex, closeTour]);

  // Scroll element into view and update positions
  useEffect(() => {
    if (!isActive || validSteps.length === 0) return;

    const currentStep = validSteps[currentIndex];
    if (!currentStep) return;

    const targetEl = document.querySelector(currentStep.target);
    if (targetEl) {
      targetEl.scrollIntoView({
        behavior: "auto",
        block: "nearest",
        inline: "nearest",
      });
    }

    updatePosition();
    // Re-check after layout settle
    const t = setTimeout(updatePosition, 50);

    // Focus popover for keyboard accessibility
    if (popoverRef.current) {
      popoverRef.current.focus();
    }

    return () => clearTimeout(t);
  }, [isActive, currentIndex, validSteps, updatePosition]);

  // Recompute position on resize and scroll
  useEffect(() => {
    if (!isActive) return;

    const handleScrollOrResize = () => {
      updatePosition();
    };

    window.addEventListener("resize", handleScrollOrResize);
    window.addEventListener("scroll", handleScrollOrResize, true);
    return () => {
      window.removeEventListener("resize", handleScrollOrResize);
      window.removeEventListener("scroll", handleScrollOrResize, true);
    };
  }, [isActive, updatePosition]);

  const handleNext = useCallback(() => {
    if (currentIndex + 1 < validSteps.length) {
      setCurrentIndex((i) => i + 1);
    } else {
      closeTour(true);
      if (onFinish) onFinish();
    }
  }, [currentIndex, validSteps.length, closeTour, onFinish]);

  const handleBack = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex((i) => i - 1);
    }
  }, [currentIndex]);

  const handleSkip = useCallback(() => {
    closeTour(true);
    if (onSkip) onSkip();
  }, [closeTour, onSkip]);

  // Keyboard navigation: Escape to close, Left/Right arrow keys
  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        handleSkip();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        handleNext();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        handleBack();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isActive, handleSkip, handleNext, handleBack]);

  if (!isActive || validSteps.length === 0) {
    return null;
  }

  const currentStep = validSteps[currentIndex];
  const isFirstStep = currentIndex === 0;
  const isLastStep = currentIndex === validSteps.length - 1;

  return (
    <div className="tour-container" aria-live="polite">
      {/* Dim overlay behind spotlight */}
      <div
        className="tour-overlay-blocker"
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 9990,
          backgroundColor: "rgba(29, 29, 27, 0.55)",
          cursor: "default",
        }}
        onClick={(e) => {
          // Clicking overlay does not close it as per requirements
          e.stopPropagation();
        }}
      />

      {/* Spotlight cutout around the target element */}
      {spotlight && (
        <div
          className="tour-spotlight"
          style={{
            position: "fixed",
            top: `${spotlight.top}px`,
            left: `${spotlight.left}px`,
            width: `${spotlight.width}px`,
            height: `${spotlight.height}px`,
            zIndex: 9992,
            outline: "2px solid var(--accent)",
            outlineOffset: "2px",
            borderRadius: "4px",
            backgroundColor: "transparent",
            boxShadow: "0 0 0 9999px rgba(29, 29, 27, 0.55)",
            pointerEvents: "none",
          }}
        />
      )}

      {/* Popover dialog */}
      <div
        ref={popoverRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="tour-step-title"
        tabIndex={-1}
        className="tour-popover"
        style={{
          position: "fixed",
          zIndex: 9995,
          backgroundColor: "#fffdf9",
          border: "1px solid var(--border)",
          borderRadius: "4px",
          padding: "14px",
          outline: "none",
          boxShadow: "none",
          ...popoverStyle,
        }}
      >
        {/* Top bar with title and Skip button */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "8px",
          }}
        >
          <div
            id="tour-step-title"
            style={{
              fontSize: "16px",
              fontWeight: 600,
              color: "var(--text)",
            }}
          >
            {currentStep.title}
          </div>
          <button
            type="button"
            className="link-button"
            onClick={handleSkip}
            style={{
              fontSize: "13px",
              color: "var(--muted)",
              marginLeft: "12px",
              flexShrink: 0,
            }}
            aria-label="Skip tour"
          >
            Skip
          </button>
        </div>

        {/* Step description */}
        <div
          style={{
            fontSize: "15px",
            color: "var(--text)",
            lineHeight: 1.45,
            marginBottom: "16px",
          }}
        >
          {currentStep.body}
        </div>

        {/* Bottom controls: Progress text on left, Back/Next on right */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span
            style={{
              fontSize: "13px",
              color: "var(--muted)",
            }}
          >
            {currentIndex + 1} of {validSteps.length}
          </span>

          <div style={{ display: "flex", gap: "8px" }}>
            {!isFirstStep && (
              <button
                type="button"
                className="link-button"
                onClick={handleBack}
                style={{
                  fontSize: "14px",
                  marginRight: "4px",
                }}
              >
                Back
              </button>
            )}
            <button
              type="button"
              onClick={handleNext}
              style={{
                fontSize: "14px",
                padding: "6px 12px",
              }}
            >
              {isLastStep ? "Finish" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
