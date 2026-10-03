import importlib.util, json, sys
from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[1]
addon_root=root/'tools'/'xfbin-importer-2.5.2'/'Blender-XFBIN-Importer'
spec=importlib.util.spec_from_file_location('xfbin_importer',addon_root/'__init__.py',submodule_search_locations=[str(addon_root)])
addon=importlib.util.module_from_spec(spec); sys.modules[spec.name]=addon; spec.loader.exec_module(addon); addon.register()
source_asbr=Path(sys.argv[sys.argv.index('--')+1]).resolve(); source_storm=Path(sys.argv[sys.argv.index('--')+2]).resolve(); dest=Path(sys.argv[sys.argv.index('--')+3]).resolve()
class DummyOperator:
 def report(self,*args): pass
cls=sys.modules['xfbin_importer.blender.importer'].XfbinImporter
opts={'use_full_material_names':True,'import_all_textures':True,'clear_textures':False,'skip_lod_tex':False,'import_modelhit':True}
for p in (source_asbr,source_storm): cls(DummyOperator(),str(p),opts).read(bpy.context)
rigs={o.name:[b.name for b in o.data.bones] for o in bpy.data.objects if o.type=='ARMATURE' and o.name in ('2jsp01bod1','1nrtbod1')}
a=set(rigs.get('2jsp01bod1',[])); s=set(rigs.get('1nrtbod1',[]))
report={'asbr_bones':len(a),'storm_bones':len(s),'matching_names':len(a&s),'asbr_only':sorted(a-s),'storm_only':sorted(s-a),'asbr_order':rigs.get('2jsp01bod1',[]),'storm_order':rigs.get('1nrtbod1',[])}
dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps({k:v for k,v in report.items() if not k.endswith('_order')},indent=2))

