import AVFoundation
import XCTest
@testable import SignalProbe

final class ProbeTests: XCTestCase {
    func testSampleUsesOfficialHTTPSHost() {
        XCTAssertEqual(SampleMedia.url.scheme, "https")
        XCTAssertEqual(SampleMedia.url.host, "devstreaming-cdn.apple.com")
    }

    func testAppIsTVOS() {
        let bundle = Bundle(for: ProbeTests.self)
        XCTAssertEqual(bundle.infoDictionary?["CFBundleSupportedPlatforms"] as? [String], ["AppleTVSimulator"])
        #if !os(tvOS)
        XCTFail("Tests must execute on tvOS")
        #endif
    }

    // Real network/decode smoke check, deliberately fails on unavailable media.
    @MainActor
    func testSampleLoadsPlaysPausesAndSeeks() async throws {
        let asset = AVURLAsset(url: SampleMedia.url)
        let playable = try await asset.load(.isPlayable)
        XCTAssertTrue(playable)
        let duration = try await asset.load(.duration)
        XCTAssertGreaterThan(duration.seconds, 30)
        let player = AVPlayer(playerItem: AVPlayerItem(asset: asset))
        defer { player.pause() }
        player.play()
        let deadline = Date().addingTimeInterval(60)
        while player.currentTime().seconds < 1 && Date() < deadline && player.error == nil {
            try await Task.sleep(for: .milliseconds(250))
        }
        XCTAssertNil(player.error)
        XCTAssertGreaterThanOrEqual(player.currentTime().seconds, 1, "Playback must advance")
        player.pause()
        XCTAssertEqual(player.rate, 0)
        let sought = await player.seek(to: CMTime(seconds: 20, preferredTimescale: 600), toleranceBefore: .zero, toleranceAfter: .zero)
        XCTAssertTrue(sought)
        XCTAssertEqual(player.currentTime().seconds, 20, accuracy: 1)
    }
}
