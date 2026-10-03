#!/usr/bin/env python3
"""B3/B4: STRUCTURE-ONLY inventory of XFBIN files using xfbin_lib (Blender-XFBIN-Importer).

usage:
  xfbin_inventory.py inventory <file-or-dir>... --json out/stardust/x.json --md docs/x.md
  xfbin_inventory.py diff <vanilla> <reference> <candidate> --md docs/chunk_diff.md

Records only: relative file name, size, SHA-256, first 4 bytes, page count, and per-chunk
(type, name, filePath). No asset bytes are copied. Runs with plain Python (no Blender).
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "out" / "tools" / "xfbin-importer-2.5.2" / "Blender-XFBIN-Importer"))


def inspect(path: Path, base: Path) -> dict:
    data = path.read_bytes()
    rec = {"file": str(path.relative_to(base)) if path.is_relative_to(base) else path.name,
           "size": len(data), "sha256": hashlib.sha256(data).hexdigest().upper(), "magic": data[:4].hex(" ")}
    if not data.startswith(b"NUCC"):
        rec["error"] = "not NUCC"
        return rec
    try:
        from xfbin_lib.xfbin.xfbin_reader import read_xfbin
        x = read_xfbin(str(path))
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"
        return rec
    rec["pages"] = []
    for page in x.pages:
        rec["pages"].append([{"type": type(c).__name__, "name": getattr(c, "name", ""),
                              "path": getattr(c, "filePath", "")} for c in page.chunks])
    return rec


def collect(inputs):
    out = []
    for i in map(Path, inputs):
        files = sorted(p for p in i.rglob("*") if p.is_file()) if i.is_dir() else [i]
        out += [inspect(f, i if i.is_dir() else i.parent) for f in files]
    return out


def md_inventory(recs) -> str:
    lines = ["| File | Size | SHA-256 (first 16) | Magic | Pages | Chunks | Chunk types |", "|---|---:|---|---|---:|---:|---|"]
    for r in recs:
        chunks = [c for p in r.get("pages", []) for c in p]
        types = Counter(c["type"] for c in chunks)
        lines.append(f"| `{r['file']}` | {r['size']:,} | `{r['sha256'][:16]}` | `{r['magic']}` | {len(r.get('pages', []))} | "
                     f"{len(chunks)} | {r.get('error') or ', '.join(f'{k}×{v}' for k, v in types.most_common())} |")
    lines += ["", "## Chunk names per file", ""]
    for r in recs:
        lines.append(f"### `{r['file']}`")
        for n, p in enumerate(r.get("pages", [])):
            lines.append(f"- page {n}: " + ", ".join(f"{c['type'].replace('NuccChunk', '')}:`{c['name']}`" for c in p))
        lines.append("")
    return "\n".join(lines)


def md_diff(recs, labels) -> str:
    sets = [Counter((c["type"], c["name"]) for p in r.get("pages", []) for c in p) for r in recs]
    types = [Counter(c["type"] for p in r.get("pages", []) for c in p) for r in recs]
    lines = ["| Metric | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
    lines.append("| size | " + " | ".join(f"{r['size']:,}" for r in recs) + " |")
    lines.append("| pages | " + " | ".join(str(len(r.get('pages', []))) for r in recs) + " |")
    for t in sorted(set().union(*types)):
        lines.append(f"| {t} | " + " | ".join(str(c.get(t, 0)) for c in types) + " |")
    lines += ["", f"## Chunks only in {labels[2]} (absent from both others)", ""]
    for k in sorted(set(sets[2]) - set(sets[0]) - set(sets[1])):
        lines.append(f"- {k[0]} `{k[1]}`")
    lines += ["", f"## Chunks in {labels[0]} missing from {labels[2]}", ""]
    for k in sorted(set(sets[0]) - set(sets[2])):
        lines.append(f"- {k[0]} `{k[1]}`")
    lines += ["", "## Page-by-page type sequence", ""]
    for lab, r in zip(labels, recs):
        lines.append(f"- **{lab}**: " + " / ".join("+".join(c["type"].replace("NuccChunk", "") for c in p) for p in r.get("pages", [])))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["inventory", "diff"])
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--json")
    ap.add_argument("--md")
    a = ap.parse_args()
    recs = collect(a.inputs)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(recs, indent=1))
    if a.mode == "diff":
        if len(recs) != 3:
            raise SystemExit("diff needs exactly 3 files: vanilla reference candidate")
        text = md_diff(recs, ["vanilla", "reference", "candidate"])
    else:
        text = md_inventory(recs)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
