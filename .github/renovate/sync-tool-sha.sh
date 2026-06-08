#!/usr/bin/env bash
# Re-sync each pinned tarball SHA-256 to its current pinned version, in place. Idempotent.
# Run as a Renovate postUpgradeTask after a version bump so the version and its checksum land
# in the same PR. Executes at the repo root inside the Renovate container (curl, sha256sum,
# sed, awk, grep all present). Renovate gates it via RENOVATE_ALLOWED_COMMANDS.
set -euo pipefail

GITLEAKS_YML=".github/actions/security/gitleaks/action.yml"
SELF_YML=".github/workflows/self.yml"
DIST_YML=".github/actions/rust/install-dist/action.yml"

sha256_of() {
  local tmp; tmp="$(mktemp)"
  curl -fsSL "$1" -o "$tmp"
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$tmp" | cut -d' ' -f1
  else shasum -a 256 "$tmp" | cut -d' ' -f1; fi
}
ver()    { grep -E "$2:" "$1" | head -1 | sed -E 's/.*"([^"]+)".*/\1/'; }
set_sha() { sed -i -E "s|($2: *\")[^\"]+(\")|\1${3}\2|" "$1"; }

# gitleaks — single linux x64 tarball
v="$(ver "$GITLEAKS_YML" GITLEAKS_VERSION)"
set_sha "$GITLEAKS_YML" GITLEAKS_SHA256 \
  "$(sha256_of "https://github.com/gitleaks/gitleaks/releases/download/v${v}/gitleaks_${v}_linux_x64.tar.gz")"

# actionlint — single linux amd64 tarball
v="$(ver "$SELF_YML" ACTIONLINT_VERSION)"
set_sha "$SELF_YML" ACTIONLINT_SHA256 \
  "$(sha256_of "https://github.com/rhysd/actionlint/releases/download/v${v}/actionlint_${v}_linux_amd64.tar.gz")"

# cargo-dist — five per-OS archives, read from the release's own sha256.sum
v="$(ver "$DIST_YML" CARGO_DIST_VERSION)"
sums="$(curl -fsSL "https://github.com/axodotdev/cargo-dist/releases/download/v${v}/sha256.sum")"
pick() { grep -F "cargo-dist-$1" <<<"$sums" | awk '{print $1}'; }
set_sha "$DIST_YML" SHA256_X86_64_LINUX   "$(pick x86_64-unknown-linux-gnu.tar.xz)"
set_sha "$DIST_YML" SHA256_AARCH64_LINUX  "$(pick aarch64-unknown-linux-gnu.tar.xz)"
set_sha "$DIST_YML" SHA256_X86_64_DARWIN  "$(pick x86_64-apple-darwin.tar.xz)"
set_sha "$DIST_YML" SHA256_AARCH64_DARWIN "$(pick aarch64-apple-darwin.tar.xz)"
set_sha "$DIST_YML" SHA256_X86_64_WINDOWS "$(pick x86_64-pc-windows-msvc.zip)"

echo "::notice::tool SHA-256 values re-synced to their pinned versions"
