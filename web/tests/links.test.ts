import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

function findTsxFiles(dir: string): string[] {
  let results: string[] = [];
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) {
      results = results.concat(findTsxFiles(fullPath));
    } else if (file.endsWith(".tsx")) {
      results.push(fullPath);
    }
  }
  return results;
}

test("Internal links check: all internal Links resolve to existing App Router pages", () => {
  const existingRoutes = new Set([
    "/",
    "/about",
    "/help",
    "/result",
    "/resume-builder",
  ]);

  const files = [
    ...findTsxFiles("app"),
    ...findTsxFiles("components"),
  ];

  const linkRegex = /<Link[^>]+href=["'](\/[^"']*)["']/g;

  for (const file of files) {
    const content = fs.readFileSync(file, "utf-8");
    let match;
    while ((match = linkRegex.exec(content)) !== null) {
      const targetRoute = match[1].split("?")[0].split("#")[0];
      assert.ok(
        existingRoutes.has(targetRoute),
        `Broken internal link '${targetRoute}' found in ${file}`
      );
    }
  }
});
