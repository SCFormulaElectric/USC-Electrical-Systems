import sys, importlib.util
D=r"C:\Users\thuta\OneDrive\Documents\KiCad\10.0\3rdparty\plugins\com_github_jvanderberg_kicad-jlcimport"
sys.stdout.reconfigure(encoding="utf-8")
spec=importlib.util.spec_from_file_location("kicad_jlcimport", D+r"\__init__.py", submodule_search_locations=[D])
m=importlib.util.module_from_spec(spec); sys.modules["kicad_jlcimport"]=m; spec.loader.exec_module(m)
from kicad_jlcimport import cli
sys.argv=["cli"]+sys.argv[1:]; cli.main()
