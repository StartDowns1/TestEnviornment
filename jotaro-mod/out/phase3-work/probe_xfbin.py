import sys
from pathlib import Path

addon_root = Path(__file__).resolve().parents[1] / "tools" / "xfbin-importer-2.5.2" / "Blender-XFBIN-Importer"
sys.path.insert(0, str(addon_root))

from xfbin_lib.xfbin.xfbin_reader import read_xfbin

samples = [
    Path(__file__).parent / "asbr-jotaro" / "spc" / "2jsp01bod1.xfbin",
    Path(__file__).parent / "asbr-jotaro" / "spc" / "2jsp01acc1.xfbin",
    Path(__file__).parent / "storm-naruto" / "spc" / "1nrtbod1.xfbin",
]

for path in samples:
    print(f"PROBE {path.name} size={path.stat().st_size}")
    try:
        xfbin = read_xfbin(str(path))
        chunks = [chunk for page in xfbin.pages for chunk in page.chunks]
        print(f"OK pages={len(xfbin.pages)} chunks={len(chunks)}")
        for chunk in chunks[:12]:
            print(f"CHUNK {type(chunk).__name__} {getattr(chunk, 'name', '')}")
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc}")

