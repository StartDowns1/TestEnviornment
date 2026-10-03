import importlib.util, sys, traceback
from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[1]
addon_root=root/'tools'/'xfbin-importer-2.5.2'/'Blender-XFBIN-Importer'
spec=importlib.util.spec_from_file_location('xfbin_importer',addon_root/'__init__.py',submodule_search_locations=[str(addon_root)])
addon=importlib.util.module_from_spec(spec); sys.modules[spec.name]=addon; spec.loader.exec_module(addon); addon.register()
path=Path(sys.argv[sys.argv.index('--')+1]).resolve()
class DummyOperator:
 def report(self,*args): print('REPORT',args)
try:
 cls=sys.modules['xfbin_importer.blender.importer'].XfbinImporter
 options={'use_full_material_names':True,'import_all_textures':True,'clear_textures':False,'skip_lod_tex':False,'import_modelhit':True}
 obj=cls(DummyOperator(),str(path),options).read(bpy.context)
 print('IMPORT_OK',path,obj)
except Exception:
 traceback.print_exc(); raise

