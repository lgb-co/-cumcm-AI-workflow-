#!/usr/bin/env sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PY="${CUMCM_PYTHON:-${CUMCM_CODE_ENV:-${MODELING_PY:-}}}"
if [ -n "$PY" ] && [ -d "$PY" ]; then
  if [ -x "$PY/bin/python" ]; then PY="$PY/bin/python"; elif [ -x "$PY/python" ]; then PY="$PY/python"; fi
fi
if [ -z "$PY" ]; then PY=$(command -v python3 || command -v python || true); fi
if [ -z "$PY" ]; then echo '[cumcm-flow] 找不到 Python 3.11+。' >&2; exit 127; fi
exec "$PY" "$HERE/cumcm_flow.py" "$@"
