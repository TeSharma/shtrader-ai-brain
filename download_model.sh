#!/usr/bin/env bash
#
# ADTC 2026 — Shtrader LA model download
#
# Downloads the single quantized GGUF weight file used by Shtrader LA into model/.
# No API keys. No authentication. Resumable. Exits non-zero on any failure.
#
# Model: Llama-3.2-3B-Instruct, Q4_K_M quantization (~2.0 GB)
# Chosen for the ADTC budget-laptop profile (4 vCPU / 8 GB RAM / integrated GPU):
# it leaves ~5 GB of headroom for the OS and a 4096-token context while still
# following multi-step instructions and emitting valid JSON.

set -euo pipefail

MODEL_DIR="model"
MODEL_FILE="Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_PATH="${MODEL_DIR}/${MODEL_FILE}"
MODEL_URL="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf?download=true"
MIN_BYTES=1500000000 # sanity floor: a truncated download is a failure

log() { printf '[download_model] %s\n' "$*"; }
fail() { printf '[download_model] ERROR: %s\n' "$*" >&2; exit 1; }

command -v curl >/dev/null 2>&1 || fail "curl is required but not installed."

mkdir -p "${MODEL_DIR}"

if [ -f "${MODEL_PATH}" ]; then
  existing=$(wc -c < "${MODEL_PATH}" | tr -d ' ')
  if [ "${existing}" -ge "${MIN_BYTES}" ]; then
    log "Model already present at ${MODEL_PATH} (${existing} bytes). Skipping download."
  else
    log "Incomplete model found (${existing} bytes). Resuming download."
  fi
fi

if [ ! -f "${MODEL_PATH}" ] || [ "$(wc -c < "${MODEL_PATH}" | tr -d ' ')" -lt "${MIN_BYTES}" ]; then
  log "Downloading ${MODEL_FILE} ..."
  curl -L --fail --retry 5 --retry-delay 3 --retry-connrefused -C - \
    -o "${MODEL_PATH}" "${MODEL_URL}" \
    || fail "download failed"
fi

# --- Validation -------------------------------------------------------------

size=$(wc -c < "${MODEL_PATH}" | tr -d ' ')
[ "${size}" -ge "${MIN_BYTES}" ] || fail "downloaded file is too small (${size} bytes) — likely truncated."

# GGUF files begin with the ASCII magic bytes "GGUF".
magic=$(head -c 4 "${MODEL_PATH}")
[ "${magic}" = "GGUF" ] || fail "file at ${MODEL_PATH} is not a valid GGUF weight file (magic: '${magic}')."

log "Valid GGUF file: ${MODEL_PATH} (${size} bytes)"

if command -v sha256sum >/dev/null 2>&1; then
  log "sha256: $(sha256sum "${MODEL_PATH}" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
  log "sha256: $(shasum -a 256 "${MODEL_PATH}" | awk '{print $1}')"
fi

log "Done. Shtrader LA can now run fully offline."
