#!/usr/bin/env bash
set -euo pipefail

TARGET_MINOR=${minor}
PATCH_VERSION=${patch}

if [[ "$PATCH_VERSION" -eq 0 ]]; then
  exit 0
fi

find . -name "go.mod" | while read -r file; do
  if grep -qE "^go 1\.${TARGET_MINOR}(\.[0-9]+)?$" "$file"; then
    echo "Updating $file"
    # reduce minor version by 1
    sed -Ei "s/^go 1\.${TARGET_MINOR}(\.[0-9]+)?$/go 1.$((TARGET_MINOR - 1))/" "$file"
  fi
done
