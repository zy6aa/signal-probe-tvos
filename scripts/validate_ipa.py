"""Fail-closed device IPA checks. Standard library only; never signs or installs."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import struct
import sys
import zipfile

BUNDLE_ID = "dev.zy6aa.signalprobe.tvos"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def macho(data):
    require(len(data) >= 32, "Truncated Mach-O")
    magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack_from("<8I", data)
    require(magic == 0xFEEDFACF, "Expected thin little-endian 64-bit Mach-O")
    require(cpu == 0x0100000C, "Expected arm64")
    require(kind in (2, 6), "Expected executable or dylib")
    require(32 + size <= len(data), "Truncated load commands")
    platform = None
    dependencies = []
    signature = False
    offset = 32
    for _ in range(count):
        require(offset + 8 <= 32 + size, "Truncated load command")
        cmd, length = struct.unpack_from("<2I", data, offset)
        require(length >= 8 and offset + length <= 32 + size, "Invalid load command size")
        if cmd == 0x32:
            require(length >= 24, "Invalid build version")
            platform = struct.unpack_from("<I", data, offset + 8)[0]
        elif cmd == 0x2F:  # LC_VERSION_MIN_TVOS (older toolchains)
            platform = 3
        elif cmd == 0x2C:
            require(length >= 24, "Invalid encryption command")
            require(struct.unpack_from("<I", data, offset + 16)[0] == 0, "Encrypted executable")
        elif cmd == 0x1D:
            signature = True
        elif cmd in (0xC, 0x80000018, 0x8000001F, 0x20, 0x80000023):
            require(length >= 24, "Invalid dylib command")
            start = struct.unpack_from("<I", data, offset + 8)[0]
            require(24 <= start < length, "Invalid dylib name offset")
            dependencies.append(data[offset + start:offset + length].split(b"\0")[0].decode())
        offset += length
    require(offset == 32 + size, "Load command size mismatch")
    require(platform == 3, "Mach-O must target physical tvOS, not iOS or Simulator")
    require(not signature, "Expected unsigned code without LC_CODE_SIGNATURE")
    return {"architecture": "arm64", "platform": "tvOS device", "dependencies": dependencies, "signed": False}


def validate(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(set(names)) == len(names), "Duplicate ZIP entries")
        for name in names:
            parts = PurePosixPath(name).parts
            require(not name.startswith("/") and ".." not in parts and "\\" not in name, "Unsafe ZIP path")
        roots = {"/".join(PurePosixPath(n).parts[:2]) for n in names if n.startswith("Payload/") and len(PurePosixPath(n).parts) >= 2}
        require(roots == {"Payload/SignalProbe.app"}, "Expected exactly one app")
        root = "Payload/SignalProbe.app/"
        info = plistlib.loads(archive.read(root + "Info.plist"))
        require(info["CFBundleIdentifier"] == BUNDLE_ID, "Wrong bundle identifier")
        require(info["CFBundleExecutable"] == "SignalProbe", "Wrong executable")
        require(info["CFBundlePackageType"] == "APPL", "Wrong bundle type")
        require(info["CFBundleSupportedPlatforms"] == ["AppleTVOS"], "Wrong plist platform")
        require(info["DTPlatformName"] == "appletvos", "Wrong SDK platform")
        require(info["UIDeviceFamily"] == [3], "Wrong device family")
        require(tuple(map(int, info["MinimumOSVersion"].split("."))) <= (27, 0), "Minimum OS exceeds target device")
        require(any(n.startswith(root + "LaunchScreen.storyboardc/") for n in names), "Missing compiled launch screen")
        require(not any(n.endswith("embedded.mobileprovision") or "/_CodeSignature/" in n for n in names), "Unexpected signing material")
        require(not any(".appex/" in n for n in names), "Unexpected extension")
        executable = archive.getinfo(root + "SignalProbe")
        require((executable.external_attr >> 16) & 0o111, "Executable ZIP mode missing")
        binaries = {}
        for name in names:
            if name.endswith("/"):
                continue
            data = archive.read(name)
            if data[:4] == b"\xcf\xfa\xed\xfe":
                binaries[name] = macho(data)
        require(root + "SignalProbe" in binaries, "Missing Mach-O executable")
        for name, binary in binaries.items():
            for dep in binary["dependencies"]:
                if dep.startswith(("/System/Library/", "/usr/lib/")):
                    continue
                if dep.startswith("@rpath/"):
                    require(root + "Frameworks/" + dep.removeprefix("@rpath/") in names, "Unresolved dependency: " + dep)
                else:
                    raise ValueError("Unexpected dependency: " + dep)
        return {"bundle_id": BUNDLE_ID, "minimum_os": info["MinimumOSVersion"], "binaries": binaries,
                "ipa_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                "verdict": "STRUCTURAL PASS ONLY — unsigned, not installable"}


if __name__ == "__main__":
    print(json.dumps(validate(sys.argv[1]), indent=2))
