const fs = require("fs");

function readInput() {
  let raw = "";
  try {
    raw = fs.readFileSync(0, "utf8");
    return { raw, input: raw.trim() ? JSON.parse(raw) : {} };
  } catch {
    return { raw, input: {} };
  }
}

function output(raw) {
  if (raw) process.stdout.write(raw);
}

function toolInput(input) {
  return input.tool_input || input.toolInput || {};
}

function preBash(raw, input) {
  const command = String(toolInput(input).command || "");
  const destructive = [
    /\bgit\s+reset\s+--hard\b/i,
    /\bgit\s+clean\s+-[^\s]*f/i,
    /\bdocker\s+compose\s+down\b[\s\S]*\s-v\b/i,
    /\bdocker\s+volume\s+rm\b/i,
    /\bDROP\s+(DATABASE|TABLE)\b/i,
    /\bTRUNCATE\s+TABLE\b/i,
    /\brm\s+-rf\s+(\/|\*|\.|\.\.)\b/i
  ];

  if (destructive.some((pattern) => pattern.test(command))) {
    console.error("[ccpv] BLOCKED destructive command. Ask the user for explicit approval and confirm target paths first.");
    process.exit(2);
  }

  if (/\bgit\s+push\s+--force\b/i.test(command) || /\b--no-verify\b/i.test(command)) {
    console.error("[ccpv] Reminder: review the diff and explain why bypassing normal safeguards is necessary.");
  }

  if (/\bdocker\s+compose\s+up\b/i.test(command) && !/\s--build\b/i.test(command)) {
    console.error("[ccpv] Reminder: for Docker app changes, consider whether `docker compose up --build` is required.");
  }

  output(raw);
}

function postEdit(raw, input) {
  const data = toolInput(input);
  const path = String(data.file_path || data.path || "");

  if (/\.(py)$/i.test(path)) {
    console.error("[ccpv] Python edit: verify FastAPI/Pydantic/SQLAlchemy contracts and run the nearest pytest/ruff/mypy command when available.");
  }

  if (/\.(vue|ts|tsx|js|jsx)$/i.test(path)) {
    console.error("[ccpv] Frontend edit: run the nearest typecheck/lint/test/build command when available; keep Vue API payloads aligned with FastAPI schemas.");
  }

  if (/(alembic|migration|models?|schemas?|repositories?|database|\.sql|docker-compose|compose\.ya?ml|Dockerfile)/i.test(path)) {
    console.error("[ccpv] Data/Docker edit: check MySQL migration safety, indexes, env vars, rollback path, and compose config.");
  }

  if (/(\.github[\\/]|workflows|playwright|vitest|pytest|Dockerfile|docker-compose|compose\.ya?ml)/i.test(path)) {
    console.error("[ccpv] Test/CI edit: report the exact verification command run, or state why it was skipped.");
  }

  output(raw);
}

function stop(raw) {
  console.error("[ccpv] Before claiming completion, include fresh verification evidence for touched FastAPI/Vue/MySQL/Docker/test paths.");
  output(raw);
}

const { raw, input } = readInput();
const mode = process.argv[2] || "";

if (mode === "pre-bash") {
  preBash(raw, input);
} else if (mode === "post-edit") {
  postEdit(raw, input);
} else if (mode === "stop") {
  stop(raw);
} else {
  output(raw);
}
