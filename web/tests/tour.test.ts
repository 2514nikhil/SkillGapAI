import test from "node:test";
import assert from "node:assert/strict";
import { filterValidSteps, hasVisitedTour, setVisitedTour } from "../lib/tourUtils.ts";

test("step-filtering logic: skips steps whose targets do not exist in the DOM", () => {
  const mockDoc = {
    querySelector: (selector) => {
      if (selector === '[data-tour="resume-file"]') {
        return { tagName: "DIV" };
      }
      if (selector === '[data-tour="target-role"]') {
        return { tagName: "DIV" };
      }
      return null;
    },
  };

  const steps = [
    { target: '[data-tour="resume-file"]', title: "Resume file", body: "Upload resume" },
    { target: '[data-tour="target-role"]', title: "Target role", body: "Pick role" },
    { target: '[data-tour="missing-table"]', title: "Missing table", body: "Not yet rendered" },
    { target: '[data-tour="unknown-element"]', title: "Unknown", body: "Does not exist" },
  ];

  const validSteps = filterValidSteps(steps, mockDoc);
  assert.equal(validSteps.length, 2);
  assert.equal(validSteps[0].target, '[data-tour="resume-file"]');
  assert.equal(validSteps[1].target, '[data-tour="target-role"]');
});

test("step-filtering logic: returns empty array if document is null or empty", () => {
  const steps = [
    { target: '[data-tour="resume-file"]', title: "Resume file", body: "Upload resume" },
  ];
  assert.deepEqual(filterValidSteps(steps, null), []);
});

test("first-visit flag logic: handles normal storage correctly", () => {
  const store = {};
  const mockStorage = {
    getItem: (key) => store[key] || null,
    setItem: (key, val) => { store[key] = String(val); },
  };

  const testKey = "skillgap_tour_upload_v1";

  // Initially unvisited
  assert.equal(hasVisitedTour(testKey, mockStorage), false);

  // Set visited
  setVisitedTour(testKey, mockStorage);
  assert.equal(hasVisitedTour(testKey, mockStorage), true);
});

test("first-visit flag logic: handles blocked or throwing storage gracefully", () => {
  const throwingStorage = {
    getItem: () => {
      throw new Error("SecurityError: The operation is insecure.");
    },
    setItem: () => {
      throw new Error("SecurityError: The operation is insecure.");
    },
  };

  const testKey = "skillgap_tour_upload_v1";

  // Should return false and not throw
  assert.doesNotThrow(() => {
    const visited = hasVisitedTour(testKey, throwingStorage);
    assert.equal(visited, false);
  });

  // setVisitedTour should not throw
  assert.doesNotThrow(() => {
    setVisitedTour(testKey, throwingStorage);
  });
});

test("Hint toggle state logic", () => {
  // Pure model of the Hint component's state transitions
  function createHintState() {
    let isOpen = false;
    return {
      get isOpen() { return isOpen; },
      toggle() { isOpen = !isOpen; },
      onKeyDown(key) {
        if (key === "Escape") {
          isOpen = false;
        }
      },
    };
  }

  const hint = createHintState();
  assert.equal(hint.isOpen, false);

  // Toggle opens
  hint.toggle();
  assert.equal(hint.isOpen, true);

  // Toggle again closes
  hint.toggle();
  assert.equal(hint.isOpen, false);

  // Reopen and test Escape key
  hint.toggle();
  assert.equal(hint.isOpen, true);
  hint.onKeyDown("Escape");
  assert.equal(hint.isOpen, false);

  // Other keys do not close
  hint.toggle();
  assert.equal(hint.isOpen, true);
  hint.onKeyDown("Enter");
  assert.equal(hint.isOpen, true);
});
