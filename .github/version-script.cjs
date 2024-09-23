#!/bin/env node

/**
 * This scripts queries the npm registry to pull out the latest version for a given tag.
 */

const fs = require("fs");
const semver = require("semver");
const child_process = require("child_process");
const assert = require("assert");

const BRANCH_VERSION_PATTERN = /^([A-Za-z]*)-(\d+.\d+.\d+)$/

// Load the contents of the manifest.json file
let manifestJSON;
try {
  manifestJSON = JSON.parse(fs.readFileSync('/home/runner/work/homekit-ratgdo/homekit-ratgdo/docs/manifest.json', "utf8"));
  console.log("Using manifest.json from primary path", tag);
} catch (err) {
  if (err.code === 'ENOENT') {
    manifestJSON = JSON.parse(fs.readFileSync('./docs/manifest.json', "utf8"));
    console.log("Using manifest.json from fallback path", tag);
  } else {
    throw err;
  }
}

let refArgument = process.argv[2];
let tagArgument = process.argv[3] || "latest";

if (refArgument == null) {
  console.error("ref argument is missing");
  console.error("Usage: version-script.cjs <ref> [tag]");
  process.exit(1);
}

function desiredTargetVersion(ref) {
  // ref is a GitHub action ref string
  if (ref.startsWith("refs/pull/")) {
    throw Error("The version script was executed inside a PR!");
  }

  assert(ref.startsWith("refs/heads/"))
  let branchName = ref.slice("refs/heads/".length);

  let results = branchName.match(BRANCH_VERSION_PATTERN);
  if (results != null) {
    if (results[1] !== tagArgument) {
      console.warn(`The base branch name (${results[1]}) differs from the tag name ${tagArgument}`);
    }

    return results[2];
  }

  // legacy mode were we use the `betaVersion` property in the manifest.json
  if (branchName === "beta" && manifestJSON.betaVersion) {
    return manifestJSON.betaVersion
  }

  throw new Error("Malformed branch name for ref: " + ref + ". Can't derive the base version. Use a branch name like: beta-x.x.x!");
}

// derive the base version from the branch ref
const baseVersion = desiredTargetVersion(refArgument);

// save the manifest.json
manifestJSON.version = baseVersion;
fs.writeFileSync("manifest.json", JSON.stringify(manifestJSON, null, 2));
