import { cpSync, existsSync, mkdirSync } from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const root = process.cwd();
const standaloneRoot = path.join(root, ".next", "standalone");
const standaloneNextRoot = path.join(standaloneRoot, ".next");
const sourceStatic = path.join(root, ".next", "static");
const targetStatic = path.join(standaloneNextRoot, "static");
const sourcePublic = path.join(root, "public");
const targetPublic = path.join(standaloneRoot, "public");
const serverPath = path.join(standaloneRoot, "server.js");

function ensureDir(target) {
  if (!existsSync(target)) {
    mkdirSync(target, { recursive: true });
  }
}

if (!existsSync(serverPath)) {
  console.error("Standalone server was not found. Run `npm run build` first.");
  process.exit(1);
}

ensureDir(standaloneNextRoot);

if (existsSync(sourceStatic)) {
  cpSync(sourceStatic, targetStatic, { recursive: true, force: true });
}

if (existsSync(sourcePublic)) {
  cpSync(sourcePublic, targetPublic, { recursive: true, force: true });
}

const child = spawn(process.execPath, [serverPath], {
  cwd: root,
  stdio: "inherit",
  env: process.env,
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
