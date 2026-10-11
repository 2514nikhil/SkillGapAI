"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on outside click or Escape key, returning focus to button
  useEffect(() => {
    if (!isMenuOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setIsMenuOpen(false);
        buttonRef.current.focus();
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setIsMenuOpen(false);
        buttonRef.current?.focus();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMenuOpen]);

  const toggleMenu = () => {
    setIsMenuOpen((prev) => !prev);
  };

  const handleStartTour = () => {
    setIsMenuOpen(false);
    buttonRef.current?.focus();
    // Dispatch custom event to start tour for current page
    window.dispatchEvent(new CustomEvent("skillgap-start-tour"));
  };

  const handleGoToHelp = () => {
    setIsMenuOpen(false);
    router.push("/help");
  };

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Link href="/" className="site-brand">
          <span className="site-brand-title">SkillGap</span>
        </Link>

        <nav className="site-nav" style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <Link href="/about">About</Link>
          <Link href="/resume-builder">Resume builder</Link>

          <div style={{ position: "relative", display: "inline-block" }}>
            <button
              ref={buttonRef}
              type="button"
              className="help-button"
              onClick={toggleMenu}
              aria-label="Help"
              title="Help"
              aria-expanded={isMenuOpen}
              aria-haspopup="true"
              style={{
                width: "28px",
                height: "28px",
                minWidth: "28px",
                padding: 0,
                border: "1px solid var(--border)",
                borderRadius: "4px",
                backgroundColor: "var(--surface)",
                color: "var(--text)",
                fontFamily: "inherit",
                fontSize: "15px",
                fontWeight: 500,
                lineHeight: "26px",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
              }}
            >
              ?
            </button>

            {isMenuOpen && (
              <div
                ref={menuRef}
                role="menu"
                style={{
                  position: "absolute",
                  top: "34px",
                  right: 0,
                  backgroundColor: "#fffdf9",
                  border: "1px solid var(--border)",
                  borderRadius: "4px",
                  padding: "6px 0",
                  minWidth: "210px",
                  zIndex: 1000,
                  boxShadow: "none",
                }}
              >
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleStartTour}
                  style={{
                    display: "block",
                    width: "100%",
                    textAlign: "left",
                    padding: "8px 14px",
                    background: "none",
                    border: "none",
                    borderRadius: 0,
                    color: "var(--text)",
                    fontSize: "14px",
                    fontWeight: "normal",
                    cursor: "pointer",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f2efe9")}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                >
                  Show me around this page
                </button>
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleGoToHelp}
                  style={{
                    display: "block",
                    width: "100%",
                    textAlign: "left",
                    padding: "8px 14px",
                    background: "none",
                    border: "none",
                    borderRadius: 0,
                    color: "var(--text)",
                    fontSize: "14px",
                    fontWeight: "normal",
                    cursor: "pointer",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f2efe9")}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                >
                  Help and troubleshooting
                </button>
              </div>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}
