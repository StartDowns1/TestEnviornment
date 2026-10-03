#!/usr/bin/env python3
"""B5: stage experiment-ladder rungs under out/stardust/stage/ladder/<RUNG>/data_win32/.

usage:
  stage_ladder.py L0 <path to dio_port/data_win32>        # control: copied as-is (local only!)
  stage_ladder.py L1|L2|L3 <xfbin> <relative path under data_win32, e.g. spc/1nrtbod1.xfbin>

Then: stardust build --config mod/config/stardust.toml --profile ladder
      (each rung lands in out/payload/ladder/<RUNG>/; install ONE rung at a time with -Set <RUNG>).
"""
import hashlib
import shutil
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1] / "out" / "stardust" / "stage" / "ladder"


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    rung = argv[0]
    dest = STAGE / rung / "data_win32"
    if dest.exists():
        shutil.rmtree(dest)
    if rung == "L0" and len(argv) == 2:
        src = Path(argv[1])
        if src.name.lower() != "data_win32":
            raise SystemExit("give the dio_port data_win32 folder itself")
        shutil.copytree(src, dest)
    elif rung in {"L1", "L2", "L3"} and len(argv) == 3:
        (dest / argv[2]).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(argv[1], dest / argv[2])
    else:
        raise SystemExit(__doc__)
    for f in sorted(dest.rglob("*")):
        if f.is_file():
            d = f.read_bytes()
            print(f"{f.relative_to(dest.parent)} size={len(d)} first16={d[:16].hex(' ')} sha256={hashlib.sha256(d).hexdigest().upper()}")


if __name__ == "__main__":
    main(sys.argv[1:])
