"""Deterministic ZIP ordering/timestamps/modes; binary reproducibility is not claimed."""
from pathlib import Path
import datetime
import os
import subprocess
import zipfile

root = Path(__file__).resolve().parents[1]
app = root / "build/device/Build/Products/Release-appletvos/SignalProbe.app"
assert app.is_dir(), "Device app missing"
timestamp = int(subprocess.check_output(["git", "show", "-s", "--format=%ct"], cwd=root))
date = datetime.datetime.fromtimestamp(max(timestamp, 315532800), datetime.timezone.utc).timetuple()[:6]
out = root / "evidence/SignalProbe-unsigned.ipa"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(app.rglob("*")):
        assert not path.is_symlink(), "Unexpected symlink"
        if not path.is_file():
            continue
        info = zipfile.ZipInfo("Payload/SignalProbe.app/" + path.relative_to(app).as_posix(), date)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = (0o100755 if os.access(path, os.X_OK) else 0o100644) << 16
        archive.writestr(info, path.read_bytes())
print(out)
