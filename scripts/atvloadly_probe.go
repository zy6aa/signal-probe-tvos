// Executed inside a pinned, separate atvloadly checkout, never linked into the app.
// No credentials, certificates, signing, network pairing, or installation.
package main

import (
    "encoding/json"
    "fmt"
    "os"
    "github.com/bitxeno/atvloadly/internal/model"
    "github.com/bitxeno/atvloadly/internal/signing/appcheck"
)

func main() {
    ipa, err := appcheck.AnalyzeIPA(os.Args[1])
    if err != nil { panic(err) }
    if ipa.Main.BundleID != "dev.zy6aa.signalprobe.tvos" { panic("wrong bundle id") }
    profile := &model.MobileProvisioningProfile{
        Platform: []string{"tvOS"},
        ApplicationIdentifierPrefix: []string{"SYNTHETIC1"},
        TeamIdentifier: []string{"SYNTHETIC1"},
        ProvisionedDevices: []string{"SYNTHETIC-DEVICE"},
        Entitlements: map[string]any{
            "application-identifier": "SYNTHETIC1.dev.zy6aa.signalprobe.tvos",
            "com.apple.developer.team-identifier": "SYNTHETIC1",
            "get-task-allow": true,
        },
    }
    input := appcheck.PlanInput{IPA: ipa, Profile: profile, DeviceClass: model.DeviceClassAppleTV, DeviceUDIDs: []string{"SYNTHETIC-DEVICE"}}
    plan := appcheck.BuildPlan(input)
    if plan.Blocking() { panic(plan.Err()) }
    profile.Platform = []string{"iOS"}
    if !appcheck.BuildPlan(input).Blocking() { panic("accepted iOS profile") }
    profile.Platform = []string{"tvOS"}
    input.DeviceUDIDs = []string{"WRONG-DEVICE"}
    if !appcheck.BuildPlan(input).Blocking() { panic("accepted unprovisioned device") }
    input.DeviceUDIDs = []string{"SYNTHETIC-DEVICE"}
    input.CustomIdentifier = "dev.zy6aa.signalprobe.resigned"
    profile.Entitlements["application-identifier"] = "SYNTHETIC1.dev.zy6aa.signalprobe.resigned"
    rewritten := appcheck.BuildPlan(input)
    if rewritten.Blocking() || rewritten.SignedMainBundleID != input.CustomIdentifier { panic("identifier rewrite failed") }
    result := map[string]any{"scope": "real IPA parsing + synthetic profile planning only; NOT free Apple ID provisioning/signing", "bundles": ipa.Bundles, "plan": plan, "identifier_rewrite": rewritten, "negative_profile_platform": "PASS", "negative_device_udid": "PASS"}
    data, err := json.MarshalIndent(result, "", "  ")
    if err != nil { panic(err) }
    fmt.Println(string(data))
}
