#!/usr/bin/env python3
"""Pre-commit asset guard: reject game assets and non-allowlisted files under out/.

Usage: check_no_assets.py [paths...]   (default: `git diff --cached --name-only`)
Paths are repo-relative; files under jotaro-mod/ are checked relative to it.
"""
import fnmatch
import os
import subprocess
import sys

ALLOW_EXT = {".md", ".py", ".ps1", ".bat", ".rs", ".toml", ".lock", ".json", ".txt", ".gitignore"}
DENY_EXT = {".cpk", ".xfbin", ".dds", ".gfx", ".swf", ".blend", ".exe", ".dll", ".png", ".jpg", ".jpeg",
            ".wav", ".adx", ".hca", ".awb", ".acb", ".usm", ".bin", ".bak", ".zip", ".7z", ".rar", ".pdb"}
MAX_BYTES = 1024 * 1024
OUT_ALLOW = ["out/rust/Cargo.toml", "out/rust/Cargo.lock", "out/rust/README.md", "out/rust/src/**",
             "out/phase3-work/*.py", "out/phase5/*.ps1", "out/phase5/*.bat"]
PROJECT = "jotaro-mod/"


def ext_of(path: str) -> str:
    base = os.path.basename(path).lower()
    if base == ".gitignore":
        return ".gitignore"
    return os.path.splitext(base)[1]


def out_allowed(rel: str) -> bool:
    for pat in OUT_ALLOW:
        if pat.endswith("/**"):
            if rel.startswith(pat[:-2]):
                return True
        elif fnmatch.fnmatch(rel, pat) and rel.count("/") == pat.count("/"):
            return True
    return False


def check(path: str, root: str) -> str | None:
    norm = path.replace("\\", "/")
    rel = norm[len(PROJECT):] if norm.startswith(PROJECT) else norm
    ext = ext_of(norm)
    if ext in DENY_EXT:
        return f"denied extension {ext}"
    if ext not in ALLOW_EXT:
        return f"extension {ext or '(none)'} not in allowlist"
    if rel.startswith("out/") and not out_allowed(rel):
        return "under out/ but not in the legacy-code allowlist"
    full = os.path.join(root, norm)
    if os.path.isfile(full) and os.path.getsize(full) >= MAX_BYTES:
        return f"file is {os.path.getsize(full)} bytes (limit {MAX_BYTES})"
    return None


def main() -> int:
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                          check=True).stdout.strip()
    paths = sys.argv[1:] or subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], capture_output=True, text=True,
        cwd=root, check=True).stdout.split()
    bad = [(p, r) for p in paths if (r := check(p, root))]
    for p, r in bad:
        print(f"ASSET GUARD: {p}: {r}", file=sys.stderr)
    if bad:
        print(f"ASSET GUARD: {len(bad)} violation(s); commit refused.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
