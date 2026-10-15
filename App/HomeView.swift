import AVKit
import SwiftUI

enum SampleMedia {
    // Apple publishes Bip Bop as an HLS developer playback test stream.
    static let url = URL(string: "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_ts/master.m3u8")!
}

struct HomeView: View {
    @State private var presentingPlayer = false
    @FocusState private var playFocused: Bool

    var body: some View {
        VStack(spacing: 32) {
            Image(systemName: "play.tv").font(.system(size: 80))
            Text("Signal Probe").font(.largeTitle.bold())
            Text("Independent tvOS build and playback verification")
                .foregroundStyle(.secondary)
            Button("Play sample video") { presentingPlayer = true }
                .accessibilityIdentifier("playSample")
                .focused($playFocused)
            Text("Bip Bop • Apple HLS developer test stream\ndeveloper.apple.com/streaming/examples • testing only")
                .font(.caption).multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Text("Use the remote to select Play. In the player, use Play/Pause and the native timeline to seek. Back returns here.")
                .font(.caption).multilineTextAlignment(.center)
        }
        .padding(80)
        .onAppear { playFocused = true }
        .fullScreenCover(isPresented: $presentingPlayer) {
            NativePlayer()
                .ignoresSafeArea()
                .onExitCommand { presentingPlayer = false }
        }
    }
}

// AVKit owns remote transport, focus, scrubbing, and playback state.
// One player exists per presentation and is paused/released on dismissal.
struct NativePlayer: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> AVPlayerViewController {
        let controller = AVPlayerViewController()
        controller.player = AVPlayer(url: SampleMedia.url)
        controller.showsPlaybackControls = true
        controller.view.accessibilityIdentifier = "nativePlayer"
        controller.player?.play()
        return controller
    }

    func updateUIViewController(_ controller: AVPlayerViewController, context: Context) {}

    static func dismantleUIViewController(_ controller: AVPlayerViewController, coordinator: ()) {
        controller.player?.pause()
        controller.player = nil
    }
}
