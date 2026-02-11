#!/usr/bin/env bash

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly DEFAULT_BASE_REF="891377205362.dkr.ecr.eu-west-1.amazonaws.com/d1db59e/mcp-atlassian/images/mcp-atlassian:latest"

base_ref="${1:-$DEFAULT_BASE_REF}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required." >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required." >&2
  exit 1
fi

inspect_json="$(docker buildx imagetools inspect "${base_ref}" --format '{{json .}}')"
digest="$(printf '%s' "${inspect_json}" | jq -r '.manifest.digest // empty')"
if [[ -z "${digest}" || "${digest}" == "null" ]]; then
  echo "Failed to resolve image digest for ${base_ref}." >&2
  exit 1
fi

base_repo="$(printf '%s' "${base_ref}" | sed -E 's/@sha256:[a-f0-9]{64}$//; s/:[^/:]+$//')"
pinned_ref="${base_repo}@${digest}"

update_dockerfile() {
  local dockerfile="$1"
  local tmp_file=""

  if [[ ! -f "${dockerfile}" ]]; then
    echo "Missing Dockerfile: ${dockerfile}" >&2
    exit 1
  fi

  tmp_file="$(mktemp)"
  if ! awk -v ref="${pinned_ref}" '
    BEGIN { updated = 0 }
    /^ARG BASE_IMAGE_REF=/ {
      print "ARG BASE_IMAGE_REF=" ref
      updated = 1
      next
    }
    { print }
    END {
      if (updated == 0) {
        exit 1
      }
    }
  ' "${dockerfile}" > "${tmp_file}"; then
    rm -f "${tmp_file}"
    echo "Failed to update BASE_IMAGE_REF in ${dockerfile}" >&2
    exit 1
  fi

  mv "${tmp_file}" "${dockerfile}"
}

update_dockerfile "${REPO_ROOT}/apps/mcp-jira/Dockerfile"
update_dockerfile "${REPO_ROOT}/apps/mcp-confluence/Dockerfile"

echo "Updated wrapper Dockerfiles to:"
echo "  ${pinned_ref}"
