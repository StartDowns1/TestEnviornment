"""Render a neutral local preview and report scene geometry/texture bindings."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

project_out = Path(__file__).resolve().parents[1]
blend_path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
render_path = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
report_path = Path(sys.argv[sys.argv.index("--") + 3]).resolve()
for target in (render_path, report_path):
    if not target.is_relative_to(project_out):
        raise SystemExit("refusing output outside project out/")

bpy.ops.wm.open_mainfile(filepath=str(blend_path))
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
coords = [o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
minimum = [min(v[i] for v in coords) for i in range(3)]
maximum = [max(v[i] for v in coords) for i in range(3)]
center = Vector([(a + b) / 2 for a, b in zip(minimum, maximum)])
dims = [b - a for a, b in zip(minimum, maximum)]
images = []
material_report = []
for mat in bpy.data.materials:
    nodes = []
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                nodes.append({"image": node.image.name, "source": node.image.source})
                images.append(node.image.name)
    material_report.append({"material": mat.name, "image_nodes": nodes})

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.display.shading.light = "STUDIO"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.color_type = "RANDOM"
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.display.shading.curvature_ridge_factor = 1.4
scene.display.shading.curvature_valley_factor = 1.0

camera_data = bpy.data.cameras.new("PreviewCamera")
camera = bpy.data.objects.new("PreviewCamera", camera_data)
scene.collection.objects.link(camera)
camera.location = center + Vector((0.0, -max(dims) * 3.1, max(dims) * 0.2))
camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = max(dims) * 1.25
scene.camera = camera

scene.render.filepath = str(render_path)
report = {
    "bounds_min": minimum,
    "bounds_max": maximum,
    "dimensions": dims,
    "materials": material_report,
    "images_in_materials": sorted(set(images)),
    "mesh_objects": len(meshes),
    "armatures": [{"name": o.name, "bones": len(o.data.bones)}
                  for o in scene.objects if o.type == "ARMATURE"],
}
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
bpy.ops.render.render(write_still=True)

