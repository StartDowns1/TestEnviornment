"""B5 rung L1: vanilla Storm Naruto body, scaled 1.4x, exported through the SAME exporter as Jotaro.

usage: blender -b --python scripts/blender/l1_storm_roundtrip.py -- <vanilla 1nrtbod1.xfbin> <out.xfbin>

Prefers inject mode (patch the vanilla file) when the installed exporter exposes it; the
operator's properties are printed first so the choice is visible in the log. Output must
be under the project's out/ folder.
"""
import importlib.util
import sys
from pathlib import Path

import bpy

PROJECT = Path(__file__).resolve().parents[2]
addon_root = PROJECT / "out" / "tools" / "xfbin-importer-2.5.2" / "Blender-XFBIN-Importer"
spec = importlib.util.spec_from_file_location("xfbin_importer", addon_root / "__init__.py",
                                              submodule_search_locations=[str(addon_root)])
addon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = addon
spec.loader.exec_module(addon)
addon.register()

args = sys.argv[sys.argv.index("--") + 1:]
src, out = Path(args[0]).resolve(), Path(args[1]).resolve()
if not out.is_relative_to(PROJECT / "out"):
    raise SystemExit("refusing output outside project out/")
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


class DummyOperator:
    def report(self, *_a):
        pass


cls = sys.modules["xfbin_importer.blender.importer"].XfbinImporter
cls(DummyOperator(), str(src), {"use_full_material_names": True, "import_all_textures": True, "clear_textures": False,
                                "skip_lod_tex": False, "import_modelhit": True}).read(bpy.context)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"]
if not arm:
    raise SystemExit("no armature imported; cannot build L1")
for a in arm:
    a.scale = (1.4, 1.4, 1.4)  # the visual tell: a giant Naruto
bpy.context.view_layer.update()

props = {p.identifier for p in bpy.ops.export_scene.xfbin.get_rna_type().properties}
print("EXPORTER PROPERTIES:", sorted(props))
collection = next((c.name for c in bpy.data.collections if "1nrtbod1" in c.name), None)
if collection is None:
    raise SystemExit(f"no 1nrtbod1 collection; collections={[c.name for c in bpy.data.collections]}")
kw = dict(filepath=str(out), collection=collection, export_clumps=True, export_meshes=True, export_bones=True,
          export_dynamics=True, export_textures=True, export_tristrips=True, export_tangents=True)
inject_path = next((p for p in ("inject_xfbin_path", "xfbin_path", "inject_path") if p in props), None)
if "inject_to_xfbin" in props and inject_path:
    kw.update(inject_to_xfbin=True, **{inject_path: str(src)})
    print(f"MODE: inject into vanilla via {inject_path}")
else:
    kw.update(inject_to_xfbin=False)
    print("MODE: full export (inject property not found) — record this in DECISIONS.md")
kw = {k: v for k, v in kw.items() if k in props or k == "filepath"}
out.parent.mkdir(parents=True, exist_ok=True)
result = bpy.ops.export_scene.xfbin(**kw)
data = out.read_bytes() if out.is_file() else b""
print(f"result={result} size={len(data)} first16={data[:16].hex(' ')}")
if "FINISHED" not in result or not data.startswith(b"NUCC"):
    raise SystemExit("L1 export did not produce a NUCC file")
