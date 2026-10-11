"use client";

import React, { useEffect, useId, useRef, useState } from "react";

export interface HintProps {
  label?: string;
  children: React.ReactNode;
  ariaLabel?: string;
  style?: React.CSSProperties;
}

/**
 * Reusable inline Hint component (Amtrak-style).
 * Clicking toggles a bordered note directly below or adjacent to the element.
 * Closes on Escape or toggle click. Keyboard accessible.
 */
export default function Hint({
  label = "What's this?",
  children,
  ariaLabel,
  style,
}: HintProps) {
  const [isOpen, setIsOpen] = useState(false);
  const noteId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const toggleOpen = () => {
    setIsOpen((prev) => !prev);
  };

  return (
    <span className="hint-wrapper" style={{ display: "inline-block", ...style }}>
      <button
        ref={triggerRef}
        type="button"
        className="link-button hint-trigger"
        onClick={toggleOpen}
        aria-expanded={isOpen}
        aria-controls={noteId}
        aria-label={ariaLabel || label}
        style={{
          fontSize: "13px",
          marginLeft: "8px",
          textDecoration: "underline",
          fontWeight: "normal",
        }}
      >
        {label}
      </button>

      {isOpen && (
        <div
          id={noteId}
          className="hint-box"
          role="note"
          style={{
            marginTop: "6px",
            marginBottom: "8px",
            padding: "8px 12px",
            backgroundColor: "#fffdf9",
            border: "1px solid var(--border)",
            borderRadius: "4px",
            fontSize: "14px",
            color: "var(--text)",
            lineHeight: 1.45,
            maxWidth: "520px",
          }}
        >
          {children}
        </div>
      )}
    </span>
  );
}
