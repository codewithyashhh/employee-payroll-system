#!/usr/bin/env bash
set -euo pipefail

FEATURE_BRANCH="codex/build-production-ready-hr-and-payroll-system-atpa"
BASE_BRANCH="main"

if ! git show-ref --verify --quiet "refs/heads/${FEATURE_BRANCH}"; then
  echo "Feature branch '${FEATURE_BRANCH}' not found locally."
  exit 1
fi

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  echo "Base branch '${BASE_BRANCH}' not found locally."
  echo "Create/fetch it first, then run this script again."
  exit 1
fi

git checkout "${FEATURE_BRANCH}"
git merge "${BASE_BRANCH}" || {
  echo "Conflict detected. Resolve files, then run:"
  echo "  git add <resolved_files>"
  echo "  git commit -m 'Resolve merge conflicts between ${FEATURE_BRANCH} and ${BASE_BRANCH}'"
  exit 2
}

echo "Merge completed without conflicts."
