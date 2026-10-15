import struct
import tempfile
import unittest
import zipfile
import plistlib
from pathlib import Path
from validate_ipa import BUNDLE_ID, macho, validate


def fixture(platform=3, cpu=0x0100000C, cryptid=0, signed=False):
    commands = struct.pack("<6I", 0x32, 24, platform, 0x110000, 0x1A0500, 0)
    commands += struct.pack("<6I", 0x2C, 24, 0, 0, cryptid, 0)
    if signed:
        commands += struct.pack("<4I", 0x1D, 16, 0, 0)
    return struct.pack("<8I", 0xFEEDFACF, cpu, 0, 2, 3 if signed else 2, len(commands), 0, 0) + commands


class MachOValidationTests(unittest.TestCase):
    def test_physical_tvos_arm64(self):
        self.assertEqual(macho(fixture())["architecture"], "arm64")

    def test_reject_ios(self):
        with self.assertRaises(ValueError): macho(fixture(platform=2))

    def test_reject_tvos_simulator_arm64(self):
        with self.assertRaises(ValueError): macho(fixture(platform=8))

    def test_reject_x86(self):
        with self.assertRaises(ValueError): macho(fixture(cpu=0x01000007))

    def test_reject_encrypted(self):
        with self.assertRaises(ValueError): macho(fixture(cryptid=1))

    def test_reject_signed(self):
        with self.assertRaises(ValueError): macho(fixture(signed=True))

    def test_reject_truncated(self):
        with self.assertRaises(ValueError): macho(fixture()[:-1])

    def test_reject_malformed_command(self):
        data = bytearray(fixture())
        struct.pack_into("<I", data, 36, 0)
        with self.assertRaises(ValueError): macho(data)


class IPAValidationTests(unittest.TestCase):
    def check_archive(self, change=None, missing=None, extra=None):
        info = {"CFBundleIdentifier": BUNDLE_ID, "CFBundleExecutable": "SignalProbe",
                "CFBundlePackageType": "APPL", "CFBundleSupportedPlatforms": ["AppleTVOS"],
                "DTPlatformName": "appletvos", "UIDeviceFamily": [3], "MinimumOSVersion": "17.0"}
        if change: info.update(change)
        files = {"Info.plist": plistlib.dumps(info), "SignalProbe": fixture(), "LaunchScreen.storyboardc/Info.plist": b"fixture"}
        if missing: del files[missing]
        if extra: files.update(extra)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.ipa"
            with zipfile.ZipFile(path, "w") as archive:
                for name, data in files.items():
                    entry = zipfile.ZipInfo("Payload/SignalProbe.app/" + name)
                    entry.external_attr = 0o100755 << 16
                    archive.writestr(entry, data)
            return validate(path)

    def test_accept_synthetic_device_archive(self):
        self.assertEqual(self.check_archive()["bundle_id"], BUNDLE_ID)

    def test_reject_wrong_bundle(self):
        with self.assertRaises(ValueError): self.check_archive({"CFBundleIdentifier": "org.other.app"})

    def test_reject_simulator_plist(self):
        with self.assertRaises(ValueError): self.check_archive({"CFBundleSupportedPlatforms": ["AppleTVSimulator"]})

    def test_reject_ios_family(self):
        with self.assertRaises(ValueError): self.check_archive({"UIDeviceFamily": [1, 2]})

    def test_reject_future_minimum(self):
        with self.assertRaises(ValueError): self.check_archive({"MinimumOSVersion": "28.0"})

    def test_reject_missing_launch(self):
        with self.assertRaises(ValueError): self.check_archive(missing="LaunchScreen.storyboardc/Info.plist")

    def test_reject_embedded_profile(self):
        with self.assertRaises(ValueError): self.check_archive(extra={"embedded.mobileprovision": b"synthetic"})

    def test_reject_unsafe_path(self):
        with self.assertRaises(ValueError): self.check_archive(extra={"../../../escape": b"synthetic"})


if __name__ == "__main__": unittest.main()
