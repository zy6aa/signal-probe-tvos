import XCTest

@MainActor
final class RemoteTests: XCTestCase {
    func testRemoteOpensPlayerAndReturnsHome() {
        let app = XCUIApplication()
        app.launch()
        let play = app.buttons["playSample"]
        XCTAssertTrue(play.waitForExistence(timeout: 10))
        XCTAssertTrue(play.hasFocus)
        XCUIRemote.shared.press(.select)
        XCTAssertTrue(app.otherElements["nativePlayer"].waitForExistence(timeout: 15), "Native AVKit player must appear")
        XCUIRemote.shared.press(.playPause)
        // Menu dismisses AVKit controls first when visible; a second press exits.
        XCUIRemote.shared.press(.menu)
        if !play.waitForExistence(timeout: 3) { XCUIRemote.shared.press(.menu) }
        XCTAssertTrue(play.waitForExistence(timeout: 10))
    }
}
