"""Headless Blender import and scene summary for one decoded XFBIN."""
import importlib.util
import json
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

# Remove Blender's default cube, camera, and light so the saved proof scene is clean.
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

src = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
blend_out = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
summary_out = Path(sys.argv[sys.argv.index("--") + 3]).resolve()
for target in (blend_out, summary_out):
    if not target.is_relative_to(project_out):
        raise SystemExit("refusing output outside project out/")


class DummyOperator:
    def report(self, *_args):
        pass


importer_class = sys.modules["xfbin_importer.blender.importer"].XfbinImporter
importer = importer_class(DummyOperator(), str(src), {
    "use_full_material_names": True,
    "import_all_textures": True,
    "clear_textures": False,
    "skip_lod_tex": False,
    "import_modelhit": True,
})
importer.read(bpy.context)

meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
materials = sorted({mat.name for obj in meshes for mat in obj.data.materials if mat})
summary = {
    "source": str(src),
    "objects": len(bpy.data.objects),
    "mesh_objects": len(meshes),
    "armatures": [
        {"name": obj.name, "bones": len(obj.data.bones)} for obj in armatures
    ],
    "mesh_vertices": sum(len(obj.data.vertices) for obj in meshes),
    "mesh_faces": sum(len(obj.data.polygons) for obj in meshes),
    "materials": materials,
}
summary_out.parent.mkdir(parents=True, exist_ok=True)
summary_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
bpy.ops.wm.save_as_mainfile(filepath=str(blend_out))
print(json.dumps(summary, indent=2))

