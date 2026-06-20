#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse


SHA_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")


def read_sha(path: Path) -> str:
    match = SHA_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"{path}: no SHA-256 found")
    return match.group(0).lower()


def homebrew_desc(raw: str, formula: Path) -> str:
    desc = raw.strip().rstrip(".")
    if len(desc) > 80:
        for sep in (" — ", " – ", " - ", ": "):
            if sep in desc:
                desc = desc.split(sep, 1)[0].strip().rstrip(".")
                break
    if len(desc) > 80:
        raise SystemExit(f"{formula}: Homebrew desc remains over 80 chars")
    return desc


def sha_for_url(url: str, dist_dir: Path, formula: Path) -> str:
    artifact = Path(urlparse(url).path).name
    sha_path = dist_dir / f"{artifact}.sha256"
    if not sha_path.exists():
        raise SystemExit(f"{formula}: missing checksum file for {artifact}")
    return read_sha(sha_path)


def add_checksums(lines: list[str], dist_dir: Path, formula: Path) -> list[str]:
    output: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        url_match = re.match(r'^(\s*)url\s+"([^"]+)"\s*$', line)
        if not url_match:
            output.append(line)
            i += 1
            continue

        indent, url = url_match.groups()
        output.append(line)
        i += 1

        if i < len(lines) and re.match(r"^\s*sha256\s+", lines[i]):
            i += 1

        output.append(f'{indent}sha256 "{sha_for_url(url, dist_dir, formula)}"')

    return output


def normalize_desc_and_version(lines: list[str], formula: Path) -> list[str]:
    output: list[str] = []
    for line in lines:
        if re.match(r'^\s*version\s+"[^"]+"\s*$', line):
            continue

        desc_match = re.match(r'^(\s*)desc\s+"([^"]*)"\s*$', line)
        if desc_match:
            indent, desc = desc_match.groups()
            output.append(f'{indent}desc "{homebrew_desc(desc, formula)}"')
            continue

        output.append(line)

    return output


def normalize_aliases(text: str) -> str:
    pattern = re.compile(r"  BINARY_ALIASES = \{\n(?P<body>.*?)\n  \}(?:\.freeze)?", re.S)
    match = pattern.search(text)
    if not match:
        return text

    keys = re.findall(r'^\s*"([^"]+)":\s*\{\},?\s*$', match.group("body"), re.M)
    if not keys:
        return text

    tokens = [f'"{key}":' for key in keys]
    width = max(len(token) for token in tokens)
    body = "\n".join(f"    {token}{' ' * (width - len(token) + 1)}{{}}," for token in tokens)
    replacement = f"  BINARY_ALIASES = {{\n{body}\n  }}.freeze"
    return text[: match.start()] + replacement + text[match.end() :]


def normalize_install(text: str, binary: str) -> str:
    pattern = re.compile(r"(  def install\n).*?(    install_binary_aliases!\n)", re.S)
    return pattern.sub(rf'\1    bin.install "{binary}"\n\2', text, count=1)


def add_test_block(text: str, binary: str) -> str:
    if re.search(r"^\s*test do\s*$", text, re.M):
        return text

    block = f'\n  test do\n    assert_match version.to_s, shell_output("#{{bin}}/{binary} --version")\n  end\n'
    marker = "\nend\n"
    if not text.endswith(marker):
        raise SystemExit("formula does not end with a class-level end")
    return text[: -len(marker)] + block + "end\n"


def harden_formula(formula: Path, dist_dir: Path) -> None:
    lines = formula.read_text(encoding="utf-8").splitlines()
    lines = normalize_desc_and_version(lines, formula)
    lines = add_checksums(lines, dist_dir, formula)
    text = "\n".join(lines) + "\n"
    text = normalize_aliases(text)
    text = normalize_install(text, formula.stem)
    text = add_test_block(text, formula.stem)
    formula.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: harden-homebrew-formula.py <dist-dir>")

    dist_dir = Path(sys.argv[1])
    formulas = sorted(dist_dir.glob("*.rb"))
    for formula in formulas:
        harden_formula(formula, dist_dir)


if __name__ == "__main__":
    main()
