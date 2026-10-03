"""Use the community Blender XFBIN exporter to create a Naruto-slot candidate."""
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
addon.register()

blend_path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
out_path = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
if not out_path.is_relative_to(project_out):
    raise SystemExit("refusing output outside project out/")
out_path.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

result = bpy.ops.export_scene.xfbin(
    filepath=str(out_path),
    collection="2jsp01bod1",
    inject_to_xfbin=False,
    export_clumps=True,
    export_meshes=True,
    export_bones=True,
    export_dynamics=True,
    export_textures=True,
    export_tristrips=True,
    export_tangents=True,
    rename_content=True,
    source_name="2jsp01",
    target_name="1nrt",
)
if "FINISHED" not in result or not out_path.is_file():
    raise SystemExit(f"XFBIN export failed: {result}")
print(f"exported {out_path} ({out_path.stat().st_size} bytes)")

