#!/usr/bin/env python3
"""B1: decode one CPK entry (Storm 4 or ASBR) with Arrow-Forge's community CpkReader.

usage:
  decode_storm_entry.py find <catalog-dir> <name-fragment>      # e.g. find out/phase2-work 1nrtbod1
  decode_storm_entry.py decode <cpk> <entry/path> <out-file>    # out-file must be under out/

`decode` writes BOTH the stored payload (<out>.stored) and the decompressed payload,
prints size / first 16 bytes / SHA-256 / wrapper for each, and if the decompressed
result is still not NUCC but starts with CRILAYLA, runs the existing CRILAYLA probe.
Never writes outside the project's out/ folder and never touches the CPK.
"""
import hashlib
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "out"
MAGIC = [(b"NUCC", "XFBIN"), (b"CPK ", "CPK"), (b"CRILAYLA", "CRILAYLA"), (b"DDS ", "DDS"),
         (b"\x28\xb5\x2f\xfd", "zstd"), (b"\x04\x22\x4d\x18", "LZ4"), (b"\x1f\x8b", "gzip")]


def kind(b: bytes) -> str:
    for m, k in MAGIC:
        if b.startswith(m):
            return k
    if len(b) > 1 and b[0] == 0x78 and b[1] in (0x01, 0x9C, 0xDA):
        return "zlib?"
    return "UNKNOWN"


def report(label: str, data: bytes) -> None:
    print(f"{label}: size={len(data)} sha256={hashlib.sha256(data).hexdigest().upper()} "
          f"kind={kind(data)} first16={data[:16].hex(' ')}")


def find(catalog: Path, frag: str) -> None:
    hits = 0
    for f in sorted(catalog.rglob("*")):
        if f.is_file() and f.suffix.lower() in {".txt", ".csv", ".tsv", ".json", ".log", ".md"}:
            for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
                if frag.lower() in line.lower():
                    print(f"{f.relative_to(catalog)}:{n}: {line.strip()[:200]}")
                    hits += 1
    print(f"{hits} catalog line(s) mention '{frag}'")


def decode(cpk: Path, entry: str, out: Path) -> None:
    out = out.resolve()
    if not out.is_relative_to(OUT):
        raise SystemExit("refusing output outside project out/")
    sys.path.insert(0, str(OUT / "tools" / "Arrow-Forge"))
    from parsers.cpk_parser import CpkReader  # community reader (local, ignored)
    reader = CpkReader(str(cpk))
    want = entry.replace("\\", "/").lower()
    match = next((e for e in reader.entries if e.path.lower() == want), None)
    if match is None:
        near = [e.path for e in reader.entries if Path(want).name in e.path.lower()][:10]
        raise SystemExit(f"entry not found: {want}; same-name entries: {near}")
    out.parent.mkdir(parents=True, exist_ok=True)
    stored = reader.read_entry_data(match, decompress=False)
    Path(str(out) + ".stored").write_bytes(stored)
    report("stored ", stored)
    data = reader.read_entry_data(match, decompress=True)
    out.write_bytes(data)
    report("decoded", data)
    print(f"toc: stored={match.file_size} extract={match.extract_size}")
    if match.extract_size and len(data) != match.extract_size:
        print("WARNING: decoded size differs from TOC ExtractSize")
    if not data.startswith(b"NUCC") and stored.startswith(b"CRILAYLA"):
        sys.path.insert(0, str(OUT / "phase3-work"))
        from decode_crilayla_probe import decompress
        try:
            probe = decompress(stored)
            Path(str(out) + ".crilayla").write_bytes(probe)
            report("crilayla-probe", probe)
        except Exception as exc:  # record, don't guess
            print(f"crilayla-probe FAILED: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "find":
        find(Path(sys.argv[2]), sys.argv[3])
    elif len(sys.argv) == 5 and sys.argv[1] == "decode":
        decode(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
    else:
        raise SystemExit(__doc__)
