#!/usr/bin/env bash
# PostToolUse hook: syntax-check Python files after Claude edits them.
# Exit 2 feeds the error back to Claude so it fixes it; anything else is silent.

file_path=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("file_path",""))')

case "$file_path" in
  *.py) ;;
  *) exit 0 ;;
esac

[ -f "$file_path" ] || exit 0

if ! output=$(python3 -c 'import sys; src=open(sys.argv[1]).read(); compile(src, sys.argv[1], "exec")' "$file_path" 2>&1); then
  echo "python syntax check failed for $file_path:" >&2
  echo "$output" >&2
  exit 2
fi

exit 0
