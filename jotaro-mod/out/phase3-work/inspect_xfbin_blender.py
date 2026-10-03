"""Parse a decoded XFBIN with the downloaded Blender add-on's reader."""
import importlib.util
from pathlib import Path
import sys

import bpy

project_out = Path(__file__).resolve().parents[1]
addon_root = project_out / "tools" / "xfbin-importer-2.5.2" / "Blender-XFBIN-Importer"
spec = importlib.util.spec_from_file_location(
    "xfbin_importer", addon_root / "__init__.py",
    submodule_search_locations=[str(addon_root)],
)
addon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = addon
spec.loader.exec_module(addon)

from xfbin_importer.xfbin_lib.xfbin.xfbin_reader import read_xfbin

src = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
out = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
if not out.is_relative_to(project_out):
    raise SystemExit("refusing output outside project out/")

xfbin = read_xfbin(str(src))
lines = [f"file={src.name}", f"pages={len(xfbin.pages)}"]
for page_i, page in enumerate(xfbin.pages):
    lines.append(f"page[{page_i}] chunks={len(page.chunks)}")
    for chunk in page.chunks:
        row = [type(chunk).__name__, getattr(chunk, "name", ""), getattr(chunk, "type", "")]
        if hasattr(chunk, "models"):
            row.append(f"models={len(chunk.models)}")
        if hasattr(chunk, "coord_chunks"):
            row.append(f"coords={len(chunk.coord_chunks)}")
        if hasattr(chunk, "model_chunks"):
            row.append(f"model_chunks={len(chunk.model_chunks)}")
        lines.append("  " + " | ".join(map(str, row)))

out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))

