// Fase 15 §28/§41 — artefato de build rastreável (version + checksum + build metadata).
// Roda como postbuild (npm run build) — sem dependência nova, só stdlib do Node.
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const pkg = JSON.parse(readFileSync(join(root, "package.json"), "utf-8"));
const indexHtml = readFileSync(join(root, "dist", "index.html"));

const buildInfo = {
  version: pkg.version,
  checksum: `sha256:${createHash("sha256").update(indexHtml).digest("hex")}`,
  built_at: new Date().toISOString(),
};

writeFileSync(join(root, "dist", "build-info.json"), JSON.stringify(buildInfo, null, 2));
console.log(`build-info.json escrito: ${JSON.stringify(buildInfo)}`);
