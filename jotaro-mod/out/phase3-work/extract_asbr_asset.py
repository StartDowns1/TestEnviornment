"""Use Arrow Forge's documented ASBR CPK reader on selected local entries."""
from pathlib import Path
import sys

arrow_forge = Path(__file__).resolve().parents[1] / "tools" / "Arrow-Forge"
sys.path.insert(0, str(arrow_forge))
from parsers.cpk_parser import CpkReader  # noqa: E402


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: extract_asbr_asset.py data.cpk entry/path out-file")
    archive = Path(sys.argv[1])
    requested = sys.argv[2].replace("\\", "/").lower()
    output = Path(sys.argv[3]).resolve()
    project_out = Path(__file__).resolve().parents[1]
    if not output.is_relative_to(project_out):
        raise SystemExit("refusing output outside project out/")

    reader = CpkReader(str(archive))
    match = next((e for e in reader.entries if e.path.lower() == requested), None)
    if match is None:
        raise SystemExit(f"entry not found: {requested}")
    data = reader.read_entry_data(match, decompress=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(f"entry={match.path} stored={match.file_size} expected={match.extract_size} output={len(data)}")
    print(f"signature={data[:16].hex(' ')}")
    if match.extract_size and len(data) != match.extract_size:
        raise SystemExit("decoded byte count differs from CPK TOC ExtractSize")


if __name__ == "__main__":
    main()

