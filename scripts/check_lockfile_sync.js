#!/usr/bin/env node
/* eslint-disable no-console */
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..", "frontend");
const pkgPath = path.join(root, "package.json");
const lockPath = path.join(root, "package-lock.json");

function loadJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (err) {
    console.error(`[lockfile-check] failed to read ${file}: ${err.message}`);
    process.exit(1);
  }
}

const pkg = loadJson(pkgPath);
const lock = loadJson(lockPath);

const rootLock = lock.packages && lock.packages[""];
if (!rootLock) {
  console.error("[lockfile-check] package-lock.json missing root packages entry");
  process.exit(1);
}

function diffDeps(depMap, lockMap, label) {
  const missing = [];
  Object.keys(depMap || {}).forEach((name) => {
    if (!lockMap || !(name in lockMap)) {
      missing.push(name);
    }
  });
  if (missing.length) {
    console.error(`[lockfile-check] ${label} missing in package-lock.json: ${missing.join(", ")}`);
  }
  return missing;
}

const missingDeps = diffDeps(pkg.dependencies, rootLock.dependencies, "dependencies");
const missingDevDeps = diffDeps(pkg.devDependencies, rootLock.devDependencies, "devDependencies");

if (missingDeps.length || missingDevDeps.length) {
  console.error("[lockfile-check] package-lock.json is out of sync with package.json. Run npm install in frontend/ and commit the updated lockfile.");
  process.exit(1);
}

console.log("[lockfile-check] package-lock.json is in sync with package.json");
