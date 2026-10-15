import XCTest

@MainActor
final class RemoteTests: XCTestCase {
    func testRemoteOpensPlayerAndReturnsHome() {
        let app = XCUIApplication()
        app.launch()
        let play = app.buttons["playSample"]
        XCTAssertTrue(play.waitForExistence(timeout: 10))
        XCTAssertTrue(play.hasFocus)
        capture(app, name: "Home — focused Play button")
        XCUIRemote.shared.press(.select)
        XCTAssertTrue(app.otherElements["nativePlayer"].waitForExistence(timeout: 15), "Native AVKit player must appear")
        capture(app, name: "Native AVKit player")
        XCUIRemote.shared.press(.playPause)
        // Menu dismisses AVKit controls first when visible; a second press exits.
        XCUIRemote.shared.press(.menu)
        if !play.waitForExistence(timeout: 3) { XCUIRemote.shared.press(.menu) }
        XCTAssertTrue(play.waitForExistence(timeout: 10))
    }

    private func capture(_ app: XCUIApplication, name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
