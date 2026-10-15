import json
from pathlib import Path

devices = json.loads(Path("evidence/simulators.json").read_text())["devices"]
matches = [d for runtime, entries in devices.items() if runtime.endswith("tvOS-26-5")
           for d in entries if d["isAvailable"] and d["name"] == "Apple TV 4K (3rd generation)"]
assert len(matches) == 1, "Expected the documented tvOS 26.5 Apple TV 4K third-generation simulator"
print("SIMULATOR_ID=" + matches[0]["udid"])
