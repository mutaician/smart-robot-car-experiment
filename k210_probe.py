import gc
import os
import sys


print("K210 probe starting...")
print("platform:", sys.platform)
print("cwd:", os.getcwd())
print("flash files:", os.listdir("/flash"))
print("free memory:", gc.mem_free())

try:
    print("config.json:")
    print(open("/flash/config.json").read())
except Exception as exc:
    print("could not read config:", repr(exc))

for module_name in ("sensor", "lcd", "image", "maix", "KPU", "fpioa_manager"):
    try:
        module = __import__(module_name)
        print("import ok:", module_name)
        print("dir", module_name, ":", dir(module)[:40])
    except Exception as exc:
        print("import failed:", module_name, repr(exc))

try:
    from maix import KPU

    print("from maix import KPU: ok")
    print("KPU dir:", dir(KPU)[:60])
except Exception as exc:
    print("from maix import KPU failed:", repr(exc))

print("Available frozen/built-in modules:")
help("modules")

print("K210 probe done.")
