import importlib.util, sys, traceback
from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[1]
addon_root=root/'tools'/'cc2-xfbin-blender-anm'
spec=importlib.util.spec_from_file_location('cc2_xfbin_blender_anm',addon_root/'__init__.py',submodule_search_locations=[str(addon_root)])
addon=importlib.util.module_from_spec(spec); sys.modules[spec.name]=addon; spec.loader.exec_module(addon); addon.register()
path=Path(sys.argv[sys.argv.index('--')+1]).resolve()
try:
 from cc2_xfbin_blender_anm.xfbin_lib.xfbin.xfbin_reader import read_xfbin
 xf=read_xfbin(str(path)); print('BASE_ADDON_PARSE_OK pages=',len(xf.pages))
 cls=sys.modules['cc2_xfbin_blender_anm.blender.importer'].XfbinImporter
 class DummyOperator:
  def report(self,*args): print('REPORT',args)
 opts={'use_full_material_names':True,'import_textures':False,'skip_lod_tex':False,'import_modelhit':False,'merge_verts':False}
 result=cls(DummyOperator(),str(path),opts).read(bpy.context)
 print('BASE_ADDON_IMPORT_OK',result)
except Exception:
 traceback.print_exc(); raise


