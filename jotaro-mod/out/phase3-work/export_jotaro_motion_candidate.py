"""Proof a Jotaro motion XFBIN export using the community animation add-on."""
import importlib.util
from pathlib import Path
import sys

import bpy

project_out = Path(__file__).resolve().parents[1]

def load_addon(name, addon_root):
    spec = importlib.util.spec_from_file_location(
        name, addon_root / "__init__.py",
        submodule_search_locations=[str(addon_root)],
    )
    addon = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = addon
    spec.loader.exec_module(addon)
    addon.register()
    return addon

xfbin_root = project_out / "tools" / "xfbin-importer-2.5.2" / "Blender-XFBIN-Importer"
load_addon("xfbin_importer", xfbin_root)
anm_root = project_out / "tools" / "cc2-anm-export-blender"
load_addon("cc2_anm_export_blender", anm_root)

body = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
motion = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
out_path = Path(sys.argv[sys.argv.index("--") + 3]).resolve()
if not out_path.is_relative_to(project_out):
    raise SystemExit("refusing output outside project out/")
out_path.parent.mkdir(parents=True, exist_ok=True)

class DummyOperator:
    def report(self, *_args):
        pass

importer_cls = sys.modules["xfbin_importer.blender.importer"].XfbinImporter
options = {
    "use_full_material_names": True,
    "import_all_textures": True,
    "clear_textures": False,
    "skip_lod_tex": False,
    "import_modelhit": True,
}
for source in (body, motion):
    importer_cls(DummyOperator(), str(source), options).read(bpy.context)

def ensure_light_object(name, light_type):
    old = bpy.data.objects.get(name)
    if old and old.type == "LIGHT" and old.data:
        return old
    matrix = old.matrix_world.copy() if old else None
    collections = list(old.users_collection) if old else [bpy.context.scene.collection]
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.lights.new(name, type=light_type)
    obj = bpy.data.objects.new(name, data)
    for collection in collections:
        collection.objects.link(obj)
    if matrix is not None:
        obj.matrix_world = matrix
    obj.animation_data_create()
    return obj

# The importer represents CC2 light references as non-Light objects. The
# exporter requires Blender Light datablocks for default values.
anm_object = next(
    obj for obj in bpy.data.objects
    if obj.name.startswith("#XFBIN Animations [2jsp01mot1]")
)
for anm_chunk in anm_object.xfbin_anm_chunks_data.anm_chunks:
    for light_ref in anm_chunk.lightdircs:
        ensure_light_object(light_ref.name, "SUN")
    for light_ref in anm_chunk.lightpoints:
        ensure_light_object(light_ref.name, "POINT")

result = bpy.ops.export_anm_scene.xfbin(
    filepath=str(out_path),
    collection="2jsp01mot1",
    inject_to_xfbin=False,
    export_material_animations=True,
    export_ambient=False,
    export_fog=False,
)
if "FINISHED" not in result or not out_path.is_file():
    raise SystemExit(f"animation export failed: {result}")

from xfbin_importer.xfbin_lib.xfbin.xfbin_reader import read_xfbin
parsed = read_xfbin(str(out_path))
anm_names = [
    chunk.name
    for page in parsed.pages
    for chunk in page.chunks
    if type(chunk).__name__ == "NuccChunkAnm"
]
print(f"exported {out_path} bytes={out_path.stat().st_size} pages={len(parsed.pages)} animations={len(anm_names)}")
print("sample=" + ", ".join(anm_names[:12]))

