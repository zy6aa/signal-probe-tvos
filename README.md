# Signal Probe

Original disposable SwiftUI tvOS pipeline application. Bundle ID: `dev.zy6aa.signalprobe.tvos`.
No source from Plozz; no backend, login, packages, capabilities, or app extensions.

The launch storyboard leads to a focused Play button. Select opens an AVPlayerViewController;
AVKit provides remote Play/Pause, timeline seeking, and Back. The player pauses and releases
on dismissal. Apple provides the [Bip Bop HLS sample](https://developer.apple.com/streaming/examples/)
for developer testing. No video is bundled or redistributed. Network failures surface through AVKit.

## Build

The checked-in Xcode project is deterministically generated with Python's standard library:
`python3 scripts/generate_project.py`. No generator installation is needed.

Manually dispatch `.github/workflows/tvos.yml` in this public proof-of-concept repository.
Use only the free standard GitHub-hosted runner; never a paid larger runner.
No automatic push trigger, releases, deployment, or installation.
The job uses standard `macos-26` and explicitly checks Xcode 26.6. Runner-image updates may remove
the pinned toolchain; that causes a failure instead of silently changing Xcode.
The exact runtime is tvOS 26.5, not tvOS 27. Building with a lower SDK/minimum OS does not prove
operation on tvOS 27. The deployment target is tvOS 17.0 and device architecture is arm64.

Tests: tvOS host identity, HTTPS fixture identity, actual AVPlayer network loading/playback/pause/seek,
and a remote UI navigation smoke test. Python tests reject wrong-platform/architecture/encrypted/signed
Mach-O fixtures. Device validation examines the real executable, platform, plist, dependencies, ZIP
permissions, launch resources, and absence of signatures/profiles. The upstream atvloadly parser
and profile planner run on the actual IPA against synthetic matching and mismatched profiles.
Synthetic checks do not create valid provisioning profiles or prove free-account eligibility.

Artifacts contain an **unsigned device IPA**, Simulator app, device dSYM, xcresult, toolchain identity,
inspection logs, structural checks, and IPA SHA-256. ZIP timestamps/order/modes are deterministic for
the same input and commit. Byte-identical Xcode compilation across runner updates is not claimed.
Artifacts expire after three days to limit storage usage; download them promptly.

## Signing boundary

The unsigned IPA is not installable. A later local signing experiment must obtain a real, unexpired
tvOS development provisioning profile for the actual Apple TV UDID and matching App ID, plus a valid
certificate/private key. No paid capabilities are requested. Re-sign the main executable and every
embedded binary (if any), embed the profile, and validate resulting entitlements and signature.
The SDK frameworks are system dependencies, not bundled frameworks to sign.

[atvloadly](https://github.com/bitxeno/atvloadly) is inspected at
`95d60bc1bc1a14c1b34f6fc894dc7e2e337f7d7f`. It supports identifier rewriting, checks tvOS profile
platform and device provisioning, and documents Apple TV pairing in Settings → Remotes and Devices
→ Remote App and Devices. Its README warns about support for newly released OS versions.
[Open issue #121](https://github.com/bitxeno/atvloadly/issues/121) reports successful pairing but no
registered device on tvOS 27 with v0.4.6; this is a user report on a different device/environment,
not a reproduced failure for A2843/24J361. Free Apple ID provisioning and real tvOS 27 installation
remain unproven. No Apple credentials, Windows/BIOS/network changes, or device operations are used here.
