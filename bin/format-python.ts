#!/usr/bin/env node
/**
 * A cross-platform wrapper script to execute the Python linter (which requires virtualenv setup)
 *
 * Run alone `ts-node lint-python.ts` to format the whole Python project folder, or add extra CLI
 * arguments (like a list of specific files) to be passed through to `ruff format`.
 */
import { execSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import * as process from "node:process";

const PYPROJECT_ROOT = path.join(
  __dirname,
  "..",
  "chainlit_image",
  "foundational-llm-chat_app",
);
const PYTHON_ABSPATH = path.resolve(
  process.platform == "win32"
    ? path.join(PYPROJECT_ROOT, ".venv", "Scripts", "python")
    : path.join(PYPROJECT_ROOT, ".venv", "bin", "python"),
);

if (!fs.existsSync(PYTHON_ABSPATH)) {
  throw new Error(
    `Python virtualenv not found at ${PYTHON_ABSPATH}. ` +
      "Please install the Python project to be able to lint its files",
  );
}

// First 2 CLI args are ts-node and this script's name. Rest should be passed through to the
// formatter:
let extraArgs = process.argv.slice(2);
if (!extraArgs.length) {
  extraArgs = [path.resolve(PYPROJECT_ROOT)];
}

execSync([PYTHON_ABSPATH, "-m ruff format", ...extraArgs].join(" "), {
  stdio: "inherit",
});
