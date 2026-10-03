"""Read a motion XFBIN with the exporter project's Rust-backed reader."""
import importlib.util
from pathlib import Path
import sys

import bpy

project_out = Path(__file__).resolve().parents[1]
root = project_out / "tools" / "cc2-anm-export-blender"
spec = importlib.util.spec_from_file_location(
    "cc2_anm_export_blender", root / "__init__.py",
    submodule_search_locations=[str(root)],
)
addon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = addon
spec.loader.exec_module(addon)

from cc2_anm_export_blender.xfbin import xfbin_lib

path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
xfbin = xfbin_lib.read_xfbin(str(path))
print("type=" + type(xfbin).__name__)
print("attributes=" + repr([name for name in dir(xfbin) if not name.startswith("_")]))
print("pages=" + str(len(xfbin.pages)))
print("types=" + repr([type(page).__name__ for page in xfbin.pages[:4]]))

