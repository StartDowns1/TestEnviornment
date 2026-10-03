"""Inspect whether decoded ASBR motion curves bind to the imported Jotaro rig."""
import importlib.util
import json
from pathlib import Path
import re
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

body = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
motion = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
report_path = Path(sys.argv[sys.argv.index("--") + 3]).resolve()
if not report_path.is_relative_to(project_out):
    raise SystemExit("refusing output outside project out/")

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

armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
actions = list(bpy.data.actions)
main_rig = next((obj for obj in armatures if obj.name == "2jsp01bod1"), None)
model_bones = {bone.name for bone in main_rig.data.bones} if main_rig else set()
data = {
    "body": body.name,
    "motion": motion.name,
    "armatures": [
        {"name": arm.name, "bones": len(arm.data.bones)} for arm in armatures
    ],
    "action_count": len(actions),
    "total_fcurves": 0,
    "total_keyframes": 0,
    "rig_targeted_action_count": 0,
    "rig_targeted_fcurves": 0,
    "rig_targeted_bone_names": [],
    "rig_targeted_missing_bone_names": [],
    "sample_actions": [],
}
rig_curve_names = set()
rig_missing_names = set()
rig_action_names = set()
for action in actions:
    curve_count = 0
    key_count = 0
    groups = set()
    slots = set()
    action_bone_names = set()
    action_rig_fcurves = 0
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                slot_name = getattr(bag.slot, "identifier", "")
                slot_type = getattr(bag.slot, "target_id_type", "")
                slots.add(f"{slot_name} [{slot_type}]")
                curve_count += len(bag.fcurves)
                key_count += sum(len(curve.keyframe_points) for curve in bag.fcurves)
                for curve in bag.fcurves:
                    match = re.search(r'pose\.bones\["([^"]+)"\]', curve.data_path)
                    if match:
                        bone_name = match.group(1)
                        action_bone_names.add(bone_name)
                        action_rig_fcurves += 1
                        if slot_name in {"2jsp01bod1", "OB2jsp01bod1"}:
                            rig_curve_names.add(bone_name)
                            if bone_name not in model_bones:
                                rig_missing_names.add(bone_name)
                            rig_action_names.add(action.name)
                    if curve.group:
                        groups.add(curve.group.name)
    data["total_fcurves"] += curve_count
    data["total_keyframes"] += key_count
    if len(data["sample_actions"]) < 12:
        data["sample_actions"].append({
            "name": action.name,
            "fcurves": curve_count,
            "keyframes": key_count,
            "bone_fcurves": action_rig_fcurves,
            "bone_names": sorted(action_bone_names)[:12],
            "slots": sorted(slots),
            "bone_groups": sorted(groups)[:8],
        })
data["rig_targeted_action_count"] = len(rig_action_names)
data["rig_targeted_fcurves"] = sum(
    len(bag.fcurves)
    for action in actions
    for layer in getattr(action, "layers", [])
    for strip in layer.strips
    for bag in strip.channelbags
    if getattr(bag.slot, "identifier", "") in {"2jsp01bod1", "OB2jsp01bod1"}
)
data["rig_targeted_bone_names"] = sorted(rig_curve_names)
data["rig_targeted_missing_bone_names"] = sorted(rig_missing_names)

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(json.dumps(data, indent=2))

