#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

for name in backend frontend; do
  pid_file="logs/$name.pid"
  if [ -f "$pid_file" ]; then
    pid="$(cat "$pid_file")"
    if kill "$pid" >/dev/null 2>&1; then
      echo "Stopped $name process $pid"
    else
      echo "$name process $pid was not running"
    fi
    rm -f "$pid_file"
  else
    echo "No $name pid file found"
  fi
done

