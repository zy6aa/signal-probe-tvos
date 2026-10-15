"""Generate a small native Xcode project using only Python's standard library."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
objects = {}


def uid(name):
    return hashlib.sha256(name.encode()).hexdigest()[:24].upper()


def add(object_key, isa, **fields):
    key = uid(object_key)
    objects[key] = dict(isa=isa, **fields)
    return key


def encode(value):
    if isinstance(value, dict):
        return "{ " + " ".join(f"{encode(k)} = {encode(v)};" for k, v in value.items()) + " }"
    if isinstance(value, list):
        return "( " + ", ".join(encode(v) for v in value) + ", )" if value else "()"
    return json.dumps(str(value))


products = []
targets = []
groups = []
common = {
    "SDKROOT": "appletvos", "TVOS_DEPLOYMENT_TARGET": "17.0",
    "SUPPORTED_PLATFORMS": "appletvos appletvsimulator", "TARGETED_DEVICE_FAMILY": "3",
    "SWIFT_VERSION": "6.0", "SWIFT_STRICT_CONCURRENCY": "complete",
    "CLANG_ENABLE_MODULES": "YES", "CODE_SIGNING_ALLOWED": "NO",
    "CODE_SIGNING_REQUIRED": "NO", "CODE_SIGN_IDENTITY": "",
    "ENABLE_USER_SCRIPT_SANDBOXING": "YES",
}


def configurations(name, settings):
    refs = []
    for config in ["Debug", "Release"]:
        values = dict(settings)
        values.update(SWIFT_OPTIMIZATION_LEVEL="-Onone" if config == "Debug" else "-O",
                      DEBUG_INFORMATION_FORMAT="dwarf-with-dsym", ENABLE_TESTABILITY="YES" if config == "Debug" else "NO")
        refs.append(add(name + config, "XCBuildConfiguration", name=config, buildSettings=values))
    return add(name + "configs", "XCConfigurationList", buildConfigurations=refs,
               defaultConfigurationIsVisible=0, defaultConfigurationName="Release")


def target(name, folder, sources, resources, kind, bundle):
    product = add(name + "product", "PBXFileReference", explicitFileType="wrapper.application" if kind == "application" else "wrapper.cfbundle",
                  path=name + (".app" if kind == "application" else ".xctest"), sourceTree="BUILT_PRODUCTS_DIR")
    products.append(product)
    files = []
    phases = []
    for phase, paths in [("Sources", sources), ("Resources", resources)]:
        builds = []
        for path in paths:
            file = add(folder + path, "PBXFileReference", lastKnownFileType="sourcecode.swift" if path.endswith(".swift") else "file.storyboard", path=path, sourceTree="<group>")
            files.append(file)
            builds.append(add(folder + path + "build", "PBXBuildFile", fileRef=file))
        phases.append(add(name + phase, "PBX" + phase + "BuildPhase", buildActionMask=2147483647, files=builds, runOnlyForDeploymentPostprocessing=0))
    phases.append(add(name + "Frameworks", "PBXFrameworksBuildPhase", buildActionMask=2147483647, files=[], runOnlyForDeploymentPostprocessing=0))
    groups.append(add(folder, "PBXGroup", children=files, path=folder, sourceTree="<group>"))
    settings = dict(common, PRODUCT_NAME="$(TARGET_NAME)", PRODUCT_BUNDLE_IDENTIFIER=bundle,
                    LD_RUNPATH_SEARCH_PATHS=["$(inherited)", "@executable_path/Frameworks", "@loader_path/Frameworks"])
    if kind == "application":
        settings.update(INFOPLIST_FILE="App/Info.plist", GENERATE_INFOPLIST_FILE="NO")
    else:
        settings.update(GENERATE_INFOPLIST_FILE="YES")
    dependencies = []
    if kind == "bundle.unit-test":
        settings.update(TEST_HOST="$(BUILT_PRODUCTS_DIR)/SignalProbe.app/SignalProbe", BUNDLE_LOADER="$(TEST_HOST)")
    if kind == "bundle.ui-testing":
        settings.update(TEST_TARGET_NAME="SignalProbe")
    if kind != "application":
        proxy = add(name + "proxy", "PBXContainerItemProxy", containerPortal=uid("project"), proxyType=1, remoteGlobalIDString=uid("SignalProbe"), remoteInfo="SignalProbe")
        dependencies.append(add(name + "dep", "PBXTargetDependency", target=uid("SignalProbe"), targetProxy=proxy))
    ref = add(name, "PBXNativeTarget", name=name, productName=name, productReference=product,
              productType="com.apple.product-type." + kind, buildConfigurationList=configurations(name, settings),
              buildPhases=phases, buildRules=[], dependencies=dependencies)
    targets.append(ref)


target("SignalProbe", "App", ["ProbeApp.swift", "HomeView.swift"], ["LaunchScreen.storyboard"], "application", "dev.zy6aa.signalprobe.tvos")
target("ProbeTests", "Tests", ["ProbeTests.swift"], [], "bundle.unit-test", "dev.zy6aa.signalprobe.tests")
target("RemoteTests", "UITests", ["RemoteTests.swift"], [], "bundle.ui-testing", "dev.zy6aa.signalprobe.uitests")
products_group = add("products", "PBXGroup", children=products, name="Products", sourceTree="<group>")
main = add("main", "PBXGroup", children=groups + [products_group], sourceTree="<group>")
project = add("project", "PBXProject", attributes={"LastUpgradeCheck": "2660"}, buildConfigurationList=configurations("project", common),
              compatibilityVersion="Xcode 14.0", developmentRegion="en", knownRegions=["en", "Base"], mainGroup=main,
              productRefGroup=products_group, projectDirPath="", projectRoot="", targets=targets)
directory = ROOT / "SignalProbe.xcodeproj"
directory.mkdir(exist_ok=True)
(directory / "project.pbxproj").write_text("// !$*UTF8*$!\n" + encode(dict(archiveVersion=1, classes={}, objectVersion=56, objects=objects, rootObject=project)) + "\n", encoding="utf-8")

scheme = ET.Element("Scheme", LastUpgradeVersion="2660", version="1.7")
build = ET.SubElement(scheme, "BuildAction", parallelizeBuildables="YES", buildImplicitDependencies="YES")
entries = ET.SubElement(build, "BuildActionEntries")


def reference(parent, name, extension):
    ET.SubElement(parent, "BuildableReference", BuildableIdentifier="primary", BlueprintIdentifier=uid(name),
                  BuildableName=name + extension, BlueprintName=name, ReferencedContainer="container:SignalProbe.xcodeproj")


entry = ET.SubElement(entries, "BuildActionEntry", buildForTesting="YES", buildForRunning="YES", buildForProfiling="YES", buildForArchiving="YES", buildForAnalyzing="YES")
reference(entry, "SignalProbe", ".app")
test = ET.SubElement(scheme, "TestAction", buildConfiguration="Debug", selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB", selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB", shouldUseLaunchSchemeArgsEnv="YES")
testables = ET.SubElement(test, "Testables")
for name in ["ProbeTests", "RemoteTests"]:
    reference(ET.SubElement(testables, "TestableReference", skipped="NO"), name, ".xctest")
launch = ET.SubElement(scheme, "LaunchAction", buildConfiguration="Debug", selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB", selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB", launchStyle="0", useCustomWorkingDirectory="NO", ignoresPersistentStateOnLaunch="NO", debugDocumentVersioning="YES", allowLocationSimulation="YES")
reference(ET.SubElement(launch, "BuildableProductRunnable", runnableDebuggingMode="0"), "SignalProbe", ".app")
ET.SubElement(scheme, "AnalyzeAction", buildConfiguration="Debug")
ET.SubElement(scheme, "ArchiveAction", buildConfiguration="Release", revealArchiveInOrganizer="YES")
schemes = directory / "xcshareddata/xcschemes"
schemes.mkdir(parents=True, exist_ok=True)
ET.indent(scheme)
ET.ElementTree(scheme).write(schemes / "SignalProbe.xcscheme", encoding="utf-8", xml_declaration=True)
print("Generated SignalProbe.xcodeproj (app + unit tests + remote UI tests; no dependencies)")
