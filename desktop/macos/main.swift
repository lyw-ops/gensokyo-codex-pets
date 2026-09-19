import AppKit
import CryptoKit

let appID = Bundle.main.bundleIdentifier ?? "local.reimu.onigiri.desktop"
let sleepChainPreview = Bundle.main.object(forInfoDictionaryKey:"PetSleepChainPreview") as? Bool ?? false
let previewBuild = Bundle.main.object(forInfoDictionaryKey: "PetPreviewBuild") as? Bool ?? false

struct FrameRecord: Decodable { let file: String; let duration_ms: Int; let sha256: String }
struct SourceRecord: Decodable { let file: String; let sha256: String }
struct Canvas: Decodable { let width: Int; let height: Int }
struct Playback: Decodable { let fps: Double; let frame_count: Int; let loop: Bool }
struct Manifest: Decodable {
    let exact_frame_source_version: Int
    let character: String
    let state_set: String
    let state: String
    let canvas: Canvas
    let playback: Playback
    let base: SourceRecord
    let frames: [FrameRecord]
}
struct AssetFailure: LocalizedError {
    let message: String
    var errorDescription: String? { message }
}
func digest(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
func require(_ value: @autoclosure () -> Bool, _ message: String) throws {
    if !value() { throw AssetFailure(message: message) }
}

/// Append-only observation log for the character's own timeline.
/// It records what already happened and never selects a pose, a gate or a state.
/// Two bounded generations are kept so an unattended run cannot grow without limit.
final class PetLog {
    static let shared = PetLog()
    private let queue = DispatchQueue(label: "local.reimu.petlog")
    private let limit: Int
    private let stamp: ISO8601DateFormatter
    let url: URL?

    init(explicit: String? = option("--behavior-log"), disabled: Bool = CommandLine.arguments.contains("--no-behavior-log"),
         limit: Int = 1 << 20) {
        self.limit = limit
        stamp = ISO8601DateFormatter()
        stamp.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard !disabled else { url = nil; return }
        let target: URL
        if let explicit { target = URL(fileURLWithPath: explicit) }
        else {
            target = FileManager.default.homeDirectoryForCurrentUser
                .appendingPathComponent("Library/Logs/ReimuPet/behavior.jsonl")
        }
        do {
            try FileManager.default.createDirectory(at: target.deletingLastPathComponent(),
                                                    withIntermediateDirectories: true)
            if !FileManager.default.fileExists(atPath: target.path) {
                try Data().write(to: target, options: .withoutOverwriting)
            }
            url = target
        } catch { url = nil } // Logging is best effort; the pet must run without it.
    }

    func write(_ kind: String, _ detail: [String: String] = [:]) {
        guard let url else { return }
        var record = detail as [String: Any]
        record["kind"] = kind
        record["at"] = stamp.string(from: Date())
        record["uptime"] = (ProcessInfo.processInfo.systemUptime * 1000).rounded() / 1000
        queue.async {
            guard let line = try? JSONSerialization.data(withJSONObject: record, options: [.sortedKeys]) else { return }
            var blob = line
            blob.append(0x0a)
            let manager = FileManager.default
            let size = (try? manager.attributesOfItem(atPath: url.path))?[.size] as? Int ?? 0
            if size > self.limit {
                let rolled = url.appendingPathExtension("1")
                try? manager.removeItem(at: rolled)
                try? manager.moveItem(at: url, to: rolled)
            }
            if let handle = try? FileHandle(forWritingTo: url) {
                defer { try? handle.close() }
                _ = try? handle.seekToEnd()
                try? handle.write(contentsOf: blob)
            } else {
                try? blob.write(to: url, options: .atomic)
            }
        }
    }

    /// Drains pending writes so a recorded quit is on disk before the process leaves.
    func flush() { queue.sync {} }
}

struct ReactionArt {
    let image: NSImage?
    let failure: String?
    let alpha: NSBitmapImageRep?
    static func load(root: URL, sha: String) -> ReactionArt {
        do {
            let data = try Data(contentsOf:root.appendingPathComponent("annoyed.png"))
            try require(digest(data) == sha, "生气表情摘要不匹配")
            guard let image = NSImage(data:data), let rep = NSBitmapImageRep(data:data),
                  rep.pixelsWide == 688, rep.pixelsHigh == 688, rep.hasAlpha else {
                throw AssetFailure(message:"生气表情不是有效的 688×688 透明 PNG")
            }
            return ReactionArt(image:image,failure:nil,alpha:rep)
        } catch { return ReactionArt(image:nil,failure:error.localizedDescription,alpha:nil) }
    }
}

/// Where a clip's canvas sits inside the pet window, in units of `reference` points.
enum ClipPlacement {
    case full
    /// Literal placement, reviewed and approved as pixels. Never re-derive an approved one.
    case inset(x: Double, y: Double, side: Double, reference: Double)
    /// Derived placement for a clip whose own support edge is known: the canvas is drawn at
    /// `scale` of the window and slid vertically until its support edge meets the standing
    /// shoe line, so a new pose needs two reviewed numbers instead of new code.
    case supportAligned(scale: Double, xFraction: Double)
}

/// One packaged animation. Adding a clip is one registry row plus one `PetArtwork`
/// case, not another ternary inside the loader.
struct ClipSpec {
    let artwork: PetArtwork
    let directory: String
    let option: String
    let side: Int
    let frameCount: Int
    let fps: Int
    let stateSet: String
    let state: String
    let baseKey: String
    let manifestKey: String
    let placement: ClipPlacement
    /// Where the character meets the ground in this clip's own canvas, as a fraction from
    /// the top. The standing clip's value is the line every seated pose is aligned to.
    let supportEdge: Double
    /// The only file the manifest may name for this frame index.
    let frameFile: (Int) -> String

    static let registry: [ClipSpec] = [
        ClipSpec(artwork: .standing, directory: "Standing", option: "--standing-root",
                 side: 1254, frameCount: 140, fps: 20,
                 stateSet: "neutral_standing_v1", state: "idle_blink",
                 baseKey: "PetStandingBaseSHA256", manifestKey: "PetStandingManifestSHA256",
                 placement: .full, supportEdge: 1230.0 / 1254.0,
                 frameFile: { index in
                     (index == 97 || index == 98) ? "poses/closed.png"
                         : ([96, 99, 100].contains(index) ? "poses/half.png" : "base.png")
                 }),
        // Placement approved in Harness reimu-idle-meal-transition-20260907-v1: the seated
        // canvas is inset so its support edge meets the standing shoe line.
        ClipSpec(artwork: .eating, directory: "Pet", option: "--asset-root",
                 side: 688, frameCount: 40, fps: 10,
                 stateSet: "reference_onigiri_example", state: "eat_blink",
                 baseKey: "PetBaseSHA256", manifestKey: "PetManifestSHA256",
                 placement: .inset(x: 57 + 2.796511627906966, y: -63.26162790697674,
                                   side: 482, reference: 596),
                 supportEdge: 582.0 / 688.0,
                 frameFile: { index in String(format: "frames/frame_%03d.png", index) }),
    ] + (Bundle.main.object(forInfoDictionaryKey:"PetWorkTier2ManifestSHA256") == nil ? [] : [
        // This is the reviewed task_2 exact-frame source, not the generic/manual eating clip.
        // Its explicit runtime identity prevents any other task count from selecting it.
        ClipSpec(artwork:.workEatingTier2,directory:"WorkEatingTier2",option:"--work-tier-2-root",
                 side:596,frameCount:16,fps:10,stateSet:"eating",state:"task_2",
                 baseKey:"PetWorkTier2BaseSHA256",manifestKey:"PetWorkTier2ManifestSHA256",
                 placement:.full,supportEdge:585.0/596,
                 frameFile:{ index in String(format:"frames/frame_%03d.png",index) })
    ]) + (Bundle.main.object(forInfoDictionaryKey:"PetSlouchManifestSHA256") == nil ? [] : [
        ClipSpec(artwork:.slouch,directory:"Slouch",option:"--slouch-root",
                 side:596,frameCount:140,fps:20,stateSet:"double_cheek_v1",state:"idle_blink",
                 baseKey:"PetSlouchBaseSHA256",manifestKey:"PetSlouchManifestSHA256",
                 // Whole-scene footprint: align the tatami bottom, not the knee line.
                 placement:.supportAligned(scale:0.86,xFraction:0.07),supportEdge:568.0/596,
                 frameFile:{ (128...132).contains($0) ? "poses/closed.png" : "base.png" })
    ]) + (Bundle.main.object(forInfoDictionaryKey:"PetWorkTier3ManifestSHA256") == nil ? [] : [
        // Tier 3 currently has one reviewed Eating Set drawing. Keep it an honest still;
        // do not move the flattened table or tatami to manufacture motion.
        ClipSpec(artwork:.workEatingTier3,directory:"WorkEatingTier3",option:"--work-tier-3-root",
                 side:596,frameCount:1,fps:8,stateSet:"eating",state:"task_3",
                 baseKey:"PetWorkTier3BaseSHA256",manifestKey:"PetWorkTier3ManifestSHA256",
                 placement:.full,supportEdge:585.0/596,
                 frameFile:{ _ in "frames/frame_000.png" })
    ]) + (Bundle.main.object(forInfoDictionaryKey:"PetWorkTier4ManifestSHA256") == nil ? [] : [
        // Tier 4 is also one immutable Eating Set drawing. It stays a static native hold;
        // the flattened ramen/table/tatami scene must never be moved to imitate chewing.
        ClipSpec(artwork:.workEatingTier4,directory:"WorkEatingTier4",option:"--work-tier-4-root",
                 side:596,frameCount:1,fps:8,stateSet:"eating",state:"task_4",
                 baseKey:"PetWorkTier4BaseSHA256",manifestKey:"PetWorkTier4ManifestSHA256",
                 placement:.full,supportEdge:586.0/596,
                 frameFile:{ _ in "frames/frame_000.png" })
    ]) + (Bundle.main.object(forInfoDictionaryKey:"PetSleepManifestSHA256") == nil ? [] : [
        ClipSpec(artwork:.sleeping,directory:"Sleep",option:"--sleep-root",
                 side:1254,frameCount:sleepChainPreview ? 5 : 1,fps:sleepChainPreview ? 5 : 1,
                 stateSet:sleepChainPreview ? "sleep_chain_panel_v2" : "sleep_table_selected_v1",
                 state:sleepChainPreview ? "timing_preview" : "static_preview",
                 baseKey:"PetSleepBaseSHA256",manifestKey:"PetSleepManifestSHA256",
                 placement:.supportAligned(scale:0.8482811774958408,xFraction:0.0751829509829442),
                 supportEdge:1207.0/1254,frameFile:{i in sleepChainPreview ? ["base.png","poses/awake.png","poses/yawn.png","poses/drowsy.png","base.png"][i] : "base.png"})
    ])



    static func named(_ artwork: PetArtwork) -> ClipSpec {
        registry.first { $0.artwork == artwork } ?? registry[0]
    }
}

/// The loaded registry. Every drawing path looks a clip up here, so none of them
/// branches on a particular artwork name.
struct ClipSet {
    private let clips: [PetArtwork: Clip]
    init(_ clips: [PetArtwork: Clip]) { self.clips = clips }
    subscript(_ artwork: PetArtwork) -> Clip { clips[artwork] ?? clips[ClipSpec.registry[0].artwork]! }
    var all: [Clip] { ClipSpec.registry.map { self[$0.artwork] } }
    func contains(_ artwork: PetArtwork) -> Bool { clips[artwork] != nil }
    func isVerified(_ artwork: PetArtwork) -> Bool { clips[artwork]?.fallback == nil }
    /// Existing idle/manual actions depend only on their two historical core clips.
    /// A damaged optional work-tier package must degrade that slice, not disable unrelated actions.
    var verified: Bool { isVerified(.standing) && isVerified(.eating) }
    var animated: Bool { all.contains { $0.images.count > 1 } }
}

struct Clip {
    let base: NSImage
    let alpha: NSBitmapImageRep
    let images: [NSImage]
    let durations: [Double]
    let fallback: String?
    var total: Double { durations.reduce(0, +) }
    func index(at seconds: Double) -> Int {
        guard images.count > 1, total > 0 else { return 0 }
        let t = max(0, seconds).truncatingRemainder(dividingBy: total)
        var boundary = 0.0
        for (index, duration) in durations.enumerated() {
            boundary += duration
            if t + 0.00000001 < boundary { return index }
        }
        return 0
    }
    static func load(root: URL, spec: ClipSpec, baseSHA: String, manifestSHA: String) throws -> Clip {
        let side = spec.side, count = spec.frameCount, fps = spec.fps
        let baseData = try Data(contentsOf: root.appendingPathComponent("base.png"))
        try require(digest(baseData) == baseSHA, "静态基准校验失败")
        guard let base = NSImage(data: baseData), let alpha = NSBitmapImageRep(data: baseData),
              alpha.pixelsWide == side, alpha.pixelsHigh == side, alpha.hasAlpha else {
            throw AssetFailure(message: "静态基准不是有效的 \(side)×\(side) 透明 PNG")
        }
        do {
            let bytes = try Data(contentsOf: root.appendingPathComponent("source.json"))
            try require(digest(bytes) == manifestSHA, "动画清单校验失败")
            let m = try JSONDecoder().decode(Manifest.self, from: bytes)
            try require(m.exact_frame_source_version == 1 && m.character == "reimu" &&
                m.state_set == spec.stateSet && m.state == spec.state, "动画身份不匹配")
            try require(m.canvas.width == side && m.canvas.height == side && m.playback.frame_count == count &&
                m.frames.count == count && m.playback.loop && m.playback.fps == Double(fps), "动画规格不匹配")
            try require(m.base.file == "base.png" && m.base.sha256 == baseSHA, "基准绑定不匹配")
            var cache = [baseSHA: base], images = [NSImage](), durations = [Double]()
            for (i, frame) in m.frames.enumerated() {
                let expectedFile = spec.frameFile(i)
                try require(frame.file == expectedFile && frame.duration_ms == 1000 / fps, "帧路径或时序不匹配")
                let data = try Data(contentsOf: root.appendingPathComponent(frame.file))
                try require(digest(data) == frame.sha256, "第 \(i + 1) 帧校验失败")
                if cache[frame.sha256] == nil {
                    guard let image = NSImage(data: data), let rep = NSBitmapImageRep(data: data),
                          rep.pixelsWide == side, rep.pixelsHigh == side, rep.hasAlpha else {
                        throw AssetFailure(message: "第 \(i + 1) 帧不是有效透明 PNG")
                    }
                    cache[frame.sha256] = image
                }
                images.append(cache[frame.sha256]!); durations.append(Double(frame.duration_ms) / 1000)
            }
            try require(m.frames.first?.sha256 == baseSHA && m.frames.last?.sha256 == baseSHA, "循环首尾不匹配")
            return Clip(base: base, alpha: alpha, images: images, durations: durations, fallback: nil)
        } catch {
            return Clip(base: base, alpha: alpha, images: [base], durations: [0], fallback: error.localizedDescription)
        }
    }
}

func fit(_ proposed: NSRect, in screen: NSRect) -> NSRect {
    let side = max(1, min(proposed.width, screen.width, screen.height))
    return NSRect(x: min(max(proposed.minX, screen.minX), screen.maxX - side),
                  y: min(max(proposed.minY, screen.minY), screen.maxY - side), width: side, height: side)
}
func translated(_ origin: NSPoint, from start: NSPoint, to end: NSPoint) -> NSPoint {
    NSPoint(x: origin.x + end.x - start.x, y: origin.y + end.y - start.y)
}

final class PetPanel: NSPanel {
    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }
}
// AppKit has an upward Y axis; Harness bottom_center translation is downward.
func artworkRect(in bounds: NSRect, artwork: PetArtwork) -> NSRect {
    artworkRect(in: bounds, spec: ClipSpec.named(artwork))
}

func artworkRect(in bounds: NSRect, spec: ClipSpec) -> NSRect {
    switch spec.placement {
    case .full: return bounds
    case .inset(let x, let y, let side, let reference):
        let unit = bounds.width / reference
        return NSRect(x: bounds.minX + x * unit, y: bounds.minY + y * unit,
                      width: side * unit, height: side * unit)
    case .supportAligned(let scale, let xFraction):
        // The shoe line of the standing pose is the one ground truth both poses share.
        let shoeFromBottom = 1 - ClipSpec.named(.standing).supportEdge
        let drawn = scale * bounds.width
        return NSRect(x: bounds.minX + xFraction * bounds.width,
                      y: bounds.minY + shoeFromBottom * bounds.height
                         - (1 - spec.supportEdge) * drawn,
                      width: drawn, height: drawn)
    }
}

final class PetView: NSView {
    weak var owner: PetApp?
    var image: NSImage? { didSet { needsDisplay = true } }
    var dragging = false, pointerHeld = false
    var pointerStart = NSPoint.zero, windowStart = NSPoint.zero
    override var isOpaque: Bool { false }
    override func draw(_ dirtyRect: NSRect) {
        NSColor.clear.setFill(); dirtyRect.fill(using: .copy)
        NSGraphicsContext.current?.imageInterpolation = .high
        image?.draw(in: artworkRect(in: bounds, artwork: owner?.displayedArtwork ?? .standing), from: .zero, operation: .sourceOver, fraction: 1,
                    respectFlipped: false, hints: nil)
        if let owner = owner, !owner.qa {
            let attributes: [NSAttributedString.Key: Any] = [.font:NSFont.systemFont(ofSize:11),.foregroundColor:NSColor.white]
            if !owner.reactionCaption.isEmpty {
                let caption = owner.reactionCaption as NSString
                let size = caption.size(withAttributes:attributes)
                let bubble = NSRect(x:(bounds.width-size.width-18)/2,y:32,width:size.width+18,height:23)
                NSColor(calibratedRed:0.55,green:0.15,blue:0.09,alpha:0.9).setFill()
                NSBezierPath(roundedRect:bubble,xRadius:9,yRadius:9).fill()
                caption.draw(at:NSPoint(x:bubble.minX+9,y:bubble.minY+5),withAttributes:attributes)
            }
        }
    }
    override func mouseDown(with event: NSEvent) {
        guard let window = window else { return }
        pointerHeld = true; dragging = false; pointerStart = NSEvent.mouseLocation; windowStart = window.frame.origin
        window.ignoresMouseEvents = false
    }
    override func mouseDragged(with event: NSEvent) {
        guard pointerHeld else { return }
        let point = NSEvent.mouseLocation
        guard dragging || hypot(point.x-pointerStart.x,point.y-pointerStart.y) >= 4 else { return }
        if !dragging { dragging = true; owner?.beginInteractionDrag() }
        owner?.moveDuringDrag(startOrigin: windowStart, startPointer: pointerStart, endPointer: NSEvent.mouseLocation)
    }
    override func mouseUp(with event: NSEvent) {
        guard pointerHeld else { return }
        pointerHeld = false
        let moved = dragging; dragging = false
        if moved { owner?.endInteractionDrag() } else { owner?.clicked() }
    }
    override func rightMouseDown(with event: NSEvent) {
        guard let menu = owner?.makeMenu() else { return }
        NSMenu.popUpContextMenu(menu, with: event, for: self)
    }
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }
}

final class PetApp: NSObject, NSApplicationDelegate, NSWindowDelegate, NSMenuDelegate {
    let clips: ClipSet
    var clip: Clip { clips[.eating] }
    var standing: Clip { clips[.standing] }
    var displayedArtwork: PetArtwork = .standing
    var showingAnnoyed = false
    var displayedAlpha: NSBitmapImageRep {
        if showingAnnoyed, let alpha = reaction.alpha { return alpha }
        return clips[displayedArtwork].alpha
    }
    let reaction: ReactionArt
    let preferences: UserDefaults
    let qa: Bool
    var panel: PetPanel!, view: PetView!, status: NSStatusItem!
    var statusBubble: StatusBubbleController!
    var timer: Timer?, pointerTimer: Timer?
    var workTimer: Timer?
    var workStatus = WorkStatus()
    let behavior = PetBehavior(now:ProcessInfo.processInfo.systemUptime)
    var contextMenuOpen = false
    var reactionCaption = ""
    var behaviorNode = "disconnected"
    var now: Double { ProcessInfo.processInfo.systemUptime }
    var workStatePath: URL {
        if let path = option("--work-state-path") { return URL(fileURLWithPath:path) }
        return FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/ReimuCompanion/snapshot.json")
    }
    var playing = false, suspended = false, placing = false
    var frameIndex = 0
    var paused: Bool { preferences.bool(forKey: "paused") }
    var reduced: Bool { preferences.bool(forKey: "reduced") || NSWorkspace.shared.accessibilityDisplayShouldReduceMotion }
    var availableWorkTiers: Set<Int> {
        var result = Set<Int>()
        if clips.contains(.workEatingTier2) && clips.isVerified(.workEatingTier2) { result.insert(2) }
        if clips.contains(.workEatingTier3) && clips.isVerified(.workEatingTier3) { result.insert(3) }
        if clips.contains(.workEatingTier4) && clips.isVerified(.workEatingTier4) { result.insert(4) }
        return result
    }

    init(clips: ClipSet, reaction: ReactionArt, preferences: UserDefaults, qa: Bool) {
        self.clips = clips; self.reaction = reaction; self.preferences = preferences; self.qa = qa
    }
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        if !qa {
            behavior.onTrace = { kind, detail in PetLog.shared.write(kind, detail) }
            PetLog.shared.write("launch", ["version": Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "",
                                           "build": Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "",
                                           "bundle": appID, "preview": previewBuild ? "true" : "false",
                                           "pid": String(ProcessInfo.processInfo.processIdentifier),
                                           "animation": clip.fallback == nil ? "verified" : "fallback",
                                           "standing": standing.fallback == nil ? "verified" : "fallback"])
        }
        view = PetView(frame: NSRect(x: 0, y: 0, width: 240, height: 240)); view.owner = self
        view.setAccessibilityElement(true); view.setAccessibilityRole(.image)
        view.setAccessibilityLabel("灵梦桌宠，拖动可移动，右键打开菜单")
        panel = PetPanel(contentRect: view.frame, styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
        panel.title = previewBuild ? "灵梦桌宠预览" : "灵梦桌宠"
        panel.isOpaque = false; panel.backgroundColor = .clear; panel.hasShadow = false
        panel.level = .floating; panel.hidesOnDeactivate = false; panel.isReleasedWhenClosed = false
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.contentView = view; panel.delegate = self; panel.ignoresMouseEvents = true
        status = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusBubble = StatusBubbleController(expanded: !preferences.bool(forKey: "statusBubbleCollapsed"))
        statusBubble.onToggle = { [weak self] in self?.toggleStatusBubble() }
        statusBubble.content.contextMenu = { [weak self] in self?.makeMenu() ?? NSMenu() }
        statusBubble.update(workStatus)
        status.button?.title = previewBuild ? "灵梦预览" : "灵梦"
        status.button?.toolTip = "灵梦桌宠 · 拖动移动，右键设置"
        status.menu = makeMenu()
        if qa { behavior.setBase("idle",now:now) }
        restorePosition(); panel.orderFrontRegardless(); statusBubble.panel.orderFrontRegardless(); pollWorkState(); syncPlayback()
        if !qa {
            workTimer = Timer(timeInterval:1,repeats:true) { [weak self] _ in
                self?.pollWorkState()
                if self?.playing == false { self?.drawCurrent() }
            }
            RunLoop.main.add(workTimer!,forMode:.common)
        }
        pointerTimer = Timer(timeInterval: 0.08, repeats: true) { [weak self] _ in self?.updateHitTest() }
        RunLoop.main.add(pointerTimer!, forMode: .common)
        let center = NSWorkspace.shared.notificationCenter
        center.addObserver(self, selector: #selector(accessibilityChanged), name: NSWorkspace.accessibilityDisplayOptionsDidChangeNotification, object: nil)
        for name in [NSWorkspace.willSleepNotification, NSWorkspace.screensDidSleepNotification, NSWorkspace.sessionDidResignActiveNotification] {
            center.addObserver(self, selector: #selector(sleepNow), name: name, object: nil)
        }
        for name in [NSWorkspace.didWakeNotification, NSWorkspace.screensDidWakeNotification, NSWorkspace.sessionDidBecomeActiveNotification] {
            center.addObserver(self, selector: #selector(wakeNow), name: name, object: nil)
        }
        NotificationCenter.default.addObserver(self, selector: #selector(screensChanged), name: NSApplication.didChangeScreenParametersNotification, object: nil)
        if qa { DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) { self.selfTest() } }
        if previewBuild && !qa && CommandLine.arguments.contains("--preview-slouch") {
            previewSlouch()
        }
        if previewBuild && !qa && CommandLine.arguments.contains("--preview-sleep-chain") { previewSleepChain() }
        if previewBuild && !qa && CommandLine.arguments.contains("--preview-sleep") { previewSleep() }
        if let path = option("--launch-report") {
            let info: [String: Any] = ["pid": ProcessInfo.processInfo.processIdentifier, "window_id": panel.windowNumber,
                "frames": clip.images.count, "bundle": Bundle.main.bundlePath, "fallback": clip.fallback ?? "none",
                "floating": panel.level == .floating, "opaque": panel.isOpaque, "size": panel.frame.width,
                "status_window_id": statusBubble.panel.windowNumber, "preview": previewBuild,
                "sleep_frames":ClipSpec.registry.contains(where:{$0.artwork == .sleeping}) ? clips[.sleeping].images.count : 0,
            "sleep_reason":ClipSpec.registry.contains(where:{$0.artwork == .sleeping}) ? (clips[.sleeping].fallback ?? "none") : "not packaged",
            "slouch_frames":ClipSpec.registry.contains(where:{$0.artwork == .slouch}) ? clips[.slouch].images.count : 0,
            "slouch_reason":ClipSpec.registry.contains(where:{$0.artwork == .slouch}) ? (clips[.slouch].fallback ?? "none") : "not packaged",
            "work_tier_2_frames":clips.contains(.workEatingTier2) ? clips[.workEatingTier2].images.count : 0,
            "work_tier_2_reason":clips.contains(.workEatingTier2) ? (clips[.workEatingTier2].fallback ?? "none") : "not packaged",
            "work_tier_3_frames":clips.contains(.workEatingTier3) ? clips[.workEatingTier3].images.count : 0,
            "work_tier_3_reason":clips.contains(.workEatingTier3) ? (clips[.workEatingTier3].fallback ?? "none") : "not packaged",
            "work_tier_4_frames":clips.contains(.workEatingTier4) ? clips[.workEatingTier4].images.count : 0,
            "work_tier_4_reason":clips.contains(.workEatingTier4) ? (clips[.workEatingTier4].fallback ?? "none") : "not packaged",
            "standing_frames":standing.images.count, "standing_fallback":standing.fallback ?? "none",
                "artwork":displayedArtwork.rawValue, "behavior":behaviorNode]
            try? JSONSerialization.data(withJSONObject: info, options: [.prettyPrinted, .sortedKeys]).write(to: URL(fileURLWithPath: path))
        }
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        panel.orderFrontRegardless(); statusBubble.panel.orderFrontRegardless(); return true
    }
    func applicationWillTerminate(_ notification: Notification) {
        if !qa { PetLog.shared.write("quit", ["node": behaviorNode]); PetLog.shared.flush() }
        savePosition(); timer?.invalidate(); pointerTimer?.invalidate(); workTimer?.invalidate()
        NSWorkspace.shared.notificationCenter.removeObserver(self); NotificationCenter.default.removeObserver(self)
        if qa, let domain = option("--qa-domain") { preferences.removePersistentDomain(forName: domain) }
    }
    func visibleScreen(for rect: NSRect) -> NSRect {
        let screens = NSScreen.screens.map(\.visibleFrame)
        return screens.max(by: { a, b in
            let i = a.intersection(rect), j = b.intersection(rect)
            return (i.isNull ? 0 : i.width * i.height) < (j.isNull ? 0 : j.width * j.height)
        }) ?? NSRect(x: 0, y: 0, width: 1440, height: 900)
    }
    func defaultRect() -> NSRect {
        let screen = NSScreen.main?.visibleFrame ?? visibleScreen(for: .zero)
        let value = preferences.double(forKey: "size")
        let side = [160.0, 240, 320, 400].contains(value) ? value : 240
        let x = previewBuild ? screen.midX - side / 2 : screen.maxX - side - 24
        let y = previewBuild ? screen.midY : screen.minY + 12
        return fit(NSRect(x: x, y: y, width: side, height: side), in: screen)
    }
    func restorePosition() {
        var rect = defaultRect()
        if preferences.bool(forKey: "hasPosition") {
            let x = preferences.double(forKey: "x"), y = preferences.double(forKey: "y")
            if x.isFinite && y.isFinite { rect.origin = NSPoint(x: x, y: y) }
        }
        place(fit(rect, in: visibleScreen(for: rect))); savePosition()
    }
    func place(_ rect: NSRect) {
        placing = true; panel.setFrame(rect, display: true); placing = false; positionStatusBubble()
    }
    func positionStatusBubble() {
        guard panel != nil else { return }
        statusBubble?.place(pet: panel.frame, screen: visibleScreen(for: panel.frame))
    }
    func savePosition() {
        guard panel != nil else { return }
        preferences.set(panel.frame.minX, forKey: "x"); preferences.set(panel.frame.minY, forKey: "y")
        preferences.set(panel.frame.width, forKey: "size"); preferences.set(true, forKey: "hasPosition")
    }
    func windowDidMove(_ notification: Notification) {
        positionStatusBubble()
        if !placing && !view.dragging { savePosition() }
    }
    func moveDuringDrag(startOrigin: NSPoint, startPointer: NSPoint, endPointer: NSPoint) {
        panel.setFrameOrigin(translated(startOrigin, from: startPointer, to: endPointer))
    }
    func finishDrag() { place(fit(panel.frame, in: visibleScreen(for: panel.frame))); savePosition(); updateHitTest() }
    func solid(at screenPoint: NSPoint) -> Bool {
        let r = artworkRect(in: panel.frame, artwork: displayedArtwork)
        guard panel.frame.contains(screenPoint), r.contains(screenPoint) else { return false }
        let alpha = displayedAlpha
        let x = min(alpha.pixelsWide-1, max(0, Int((screenPoint.x - r.minX) / r.width * Double(alpha.pixelsWide))))
        let y = min(alpha.pixelsHigh-1, max(0, Int((r.maxY - screenPoint.y) / r.height * Double(alpha.pixelsHigh))))
        return (alpha.colorAt(x: x, y: y)?.alphaComponent ?? 0) > 0.10
    }
    func updateHitTest() {
        if !view.pointerHeld { panel.ignoresMouseEvents = !solid(at: NSEvent.mouseLocation) }
        statusBubble?.updateHitTest()
    }
    @objc func toggleStatusBubble() {
        statusBubble.setExpanded(!statusBubble.expanded)
        preferences.set(!statusBubble.expanded, forKey: "statusBubbleCollapsed")
    }
    func log(_ kind: String, _ detail: [String: String] = [:]) {
        guard !qa else { return }
        PetLog.shared.write(kind, detail)
    }
    func clicked() { log("input",["source":"click"]); behavior.click(now:now); syncPlayback() }
    func beginInteractionDrag() { log("input",["source":"drag_begin"]); behavior.beginDrag(now:now); syncPlayback() }
    func endInteractionDrag() { log("input",["source":"drag_end"]); behavior.endDrag(now:now); finishDrag(); syncPlayback() }
    @objc func previewSleepChain() {
        guard previewBuild, sleepChainPreview, clips[.sleeping].fallback == nil else { return }
        behavior.previewSleepChain(now:now); syncPlayback()
    }
    @objc func previewSleep() {
        guard previewBuild, ClipSpec.registry.contains(where:{$0.artwork == .sleeping}), clips[.sleeping].fallback == nil else { return }
        behavior.previewSleep(now:now); syncPlayback()
    }
    @objc func previewSlouch() {
        guard previewBuild, ClipSpec.registry.contains(where:{$0.artwork == .slouch}), clips[.slouch].fallback == nil else { return }
        behavior.previewSlouch(now:now); syncPlayback()
    }
    @objc func feedOnce() { log("input",["source":"feed"]); behavior.feed(now:now); syncPlayback() }
    func image(for output: PetPresentation) -> NSImage {
        if output.usesAnnoyedArt, let image = reaction.image { return image }
        let selected = clips[output.artwork]
        return selected.images[min(output.frame,selected.images.count-1)]
    }
    func drawCurrent() {
        let output = behavior.presentation(now:now,motionAllowed:!paused && !reduced && !suspended, mealsAllowed:clips.verified && !view.pointerHeld && !contextMenuOpen, slouchAllowed:ClipSpec.registry.contains(where:{$0.artwork == .slouch}) && clips[.slouch].fallback == nil, availableWorkTiers:availableWorkTiers)
        behaviorNode = output.node
        reactionCaption = output.caption
        displayedArtwork = output.artwork
        showingAnnoyed = output.usesAnnoyedArt && reaction.image != nil
        let selected = clips[output.artwork]
        frameIndex = min(output.frame,selected.images.count-1)
        view.image = image(for:output)
        let pose = displayedArtwork == .standing ? "站姿" : (displayedArtwork == .workEatingTier2 ? "2项任务吃饭" : (displayedArtwork == .workEatingTier3 ? "3项任务吃饭" : (displayedArtwork == .workEatingTier4 ? "4项任务吃饭" : (displayedArtwork == .slouch ? "双手托腮" : (displayedArtwork == .sleeping ? "伏桌睡姿预览" : "吃饭坐姿")))))
        view.setAccessibilityLabel("灵梦桌宠，\(workStatus.label)，\(pose)，\(reactionCaption.isEmpty ? "" : reactionCaption + "，")单击互动，拖动移动，右键菜单")
        if playing && !output.wantsAnimation {
            playing = false; timer?.invalidate(); timer = nil
        }
    }
    func pollWorkState() {
        guard !qa else { return }
        let next = WorkStatus.load(workStatePath)
        if next != workStatus {
            log("work",["state":next.state,"active":String(next.active),"unknown":String(next.unknown),
                        "providers":next.providers.joined(separator:"+")])
            workStatus = next
            statusBubble.update(next)
            behavior.setWorkStatus(next.state,activeTaskCount:next.active,now:now)
            let name = previewBuild ? "灵梦预览" : "灵梦"
            status.button?.title = next.active > 0 ? "\(name) · \(next.active)" : name
            status.button?.toolTip = next.label
            syncPlayback()
        }
    }
    func syncPlayback() {
        playing = false; timer?.invalidate(); timer = nil
        let wants = behavior.presentation(now:now,motionAllowed:!paused && !reduced && !suspended, mealsAllowed:clips.verified && !view.pointerHeld && !contextMenuOpen, slouchAllowed:ClipSpec.registry.contains(where:{$0.artwork == .slouch}) && clips[.slouch].fallback == nil, availableWorkTiers:availableWorkTiers).wantsAnimation
        if !paused && !reduced && !suspended && clips.animated && wants {
            playing = true
            timer = Timer(timeInterval:0.05,repeats:true) { [weak self] _ in self?.drawCurrent() }
            RunLoop.main.add(timer!,forMode:.common)
        }
        drawCurrent()
    }
    func item(_ title: String, _ action: Selector?, key: String = "") -> NSMenuItem {
        let item = NSMenuItem(title: title, action: action, keyEquivalent: key); item.target = self; return item
    }
    func makeMenu() -> NSMenu {
        let menu = NSMenu(); menu.delegate = self; menu.autoenablesItems = false
        let headingText = displayedArtwork == .workEatingTier2 ? "灵梦 · 2项任务吃饭" : (displayedArtwork == .workEatingTier3 ? "灵梦 · 3项任务吃饭" : (displayedArtwork == .workEatingTier4 ? "灵梦 · 4项任务吃饭" : "灵梦 · 常态站姿"))
        let heading = item(headingText, nil); heading.isEnabled = false; menu.addItem(heading)
        if !qa {
            let current = item(workStatus.label,nil); current.isEnabled = false; menu.addItem(current)
            for provider in ["codex","claude"] {
                let label = provider == "codex" ? "Codex" : "Claude Code"
                let line = item(label + (workStatus.providers.contains(provider) ? "：已收到事件" : "：尚未收到事件"),nil)
                line.isEnabled = false; menu.addItem(line)
            }
            if workStatus.unknown > 0 {
                let unknown = item("另有 \(workStatus.unknown) 项状态待确认",nil); unknown.isEnabled = false; menu.addItem(unknown)
            }
        }
        if let reason = clip.fallback {
            let warning = item("动画不可用，已显示静态原图", nil); warning.toolTip = reason; warning.isEnabled = false; menu.addItem(warning)
        }
        if let reason = standing.fallback {
            let warning = item("站姿眨眼不可用，已保持原站姿",nil)
            warning.toolTip = reason; warning.isEnabled = false; menu.addItem(warning)
        }
        if clips.contains(.workEatingTier2), let reason = clips[.workEatingTier2].fallback {
            let warning = item("2项任务动画不可用，已安全降级为站姿",nil)
            warning.toolTip = reason; warning.isEnabled = false; menu.addItem(warning)
        }
        if clips.contains(.workEatingTier3), let reason = clips[.workEatingTier3].fallback {
            let warning = item("3项任务姿态不可用，已安全降级为站姿",nil)
            warning.toolTip = reason; warning.isEnabled = false; menu.addItem(warning)
        }
        if clips.contains(.workEatingTier4), let reason = clips[.workEatingTier4].fallback {
            let warning = item("4项任务姿态不可用，已安全降级为站姿",nil)
            warning.toolTip = reason; warning.isEnabled = false; menu.addItem(warning)
        }
        if let reason = reaction.failure {
            let warning = item("生气表情不可用，连点仅显示文字",nil)
            warning.toolTip = reason; warning.isEnabled = false; menu.addItem(warning)
        }
        menu.addItem(.separator())
        menu.addItem(item(statusBubble?.expanded == false ? "展开任务状态框" : "收起任务状态框", #selector(toggleStatusBubble)))
        let feed = item("喂一口饭团",#selector(feedOnce)); feed.isEnabled = workStatus.state != "failed" && clip.images.count == 40
        menu.addItem(feed)
        if previewBuild, ClipSpec.registry.contains(where:{$0.artwork == .sleeping}) {
            if sleepChainPreview {
                let chain=item("入睡/醒来短链（12秒）",#selector(previewSleepChain))
                chain.isEnabled = workStatus.state != "failed" && clips[.sleeping].fallback == nil
                menu.addItem(chain)
            }
            let sleep = item("睡姿预览（静态60秒）",#selector(previewSleep))
            sleep.isEnabled = workStatus.state != "failed" && clips[.sleeping].fallback == nil
            menu.addItem(sleep)
        }
        if previewBuild, ClipSpec.registry.contains(where:{$0.artwork == .slouch}) {
            let rest = item("托腮预览（14秒）",#selector(previewSlouch))
            rest.isEnabled = workStatus.state != "failed" && clips[.slouch].fallback == nil
            menu.addItem(rest)
        }
        let help = item("单击回应 · 双击连眨眼 · 连点会不耐烦",nil); help.isEnabled = false; menu.addItem(help)
        if !qa {
            let autonomy = item(idleMealSummary(),nil)
            autonomy.toolTip = "打开这个菜单本身会暂停并重置安静计时；行为日志是不打扰的观察方式。"
            autonomy.isEnabled = false; menu.addItem(autonomy)
            if let path = PetLog.shared.url {
                let reveal = item("在 Finder 中显示行为日志",#selector(revealLog))
                reveal.toolTip = path.path; menu.addItem(reveal)
            }
        }
        let pause = item(paused ? "继续播放" : "暂停动画", #selector(togglePause)); pause.isEnabled = clips.animated && !reduced; menu.addItem(pause)
        let motion = item(NSWorkspace.shared.accessibilityDisplayShouldReduceMotion ? "减弱动态（系统已开启）" : "减弱动态", #selector(toggleReduced))
        motion.state = reduced ? .on : .off; motion.isEnabled = !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion; menu.addItem(motion)
        let size = item("大小", nil); let submenu = NSMenu(); submenu.autoenablesItems = false
        for n in [160, 240, 320, 400] {
            let choice = item("\(n) px", #selector(changeSize)); choice.tag = n
            choice.state = abs((panel?.frame.width ?? 240) - CGFloat(n)) < 1 ? .on : .off; submenu.addItem(choice)
        }
        size.submenu = submenu; menu.addItem(size)
        menu.addItem(item("回到右下角", #selector(resetPosition)))
        menu.addItem(.separator())
        menu.addItem(item("关于灵梦桌宠", #selector(about)))
        menu.addItem(item(previewBuild ? "退出灵梦桌宠预览" : "退出灵梦桌宠", #selector(quit), key: "q"))
        return menu
    }
    func menuWillOpen(_ menu: NSMenu) { contextMenuOpen = true; log("gate",["gate":"menu_open","value":"true"]); syncPlayback() }
    func menuDidClose(_ menu: NSMenu) { contextMenuOpen = false; log("gate",["gate":"menu_open","value":"false"]); syncPlayback() }
    func menuNeedsUpdate(_ menu: NSMenu) {
        let fresh = makeMenu(); menu.removeAllItems()
        while fresh.numberOfItems > 0 { let i = fresh.item(at: 0)!; fresh.removeItem(i); menu.addItem(i) }
    }
    @objc func togglePause() {
        preferences.set(!paused, forKey: "paused"); log("gate",["gate":"paused","value":paused ? "true" : "false"])
        behavior.cancelTransient(now:now); syncPlayback()
    }
    @objc func toggleReduced() {
        preferences.set(!preferences.bool(forKey: "reduced"), forKey: "reduced")
        log("gate",["gate":"reduced_motion","value":reduced ? "true" : "false"])
        behavior.cancelTransient(now:now); syncPlayback()
    }
    @objc func changeSize(_ sender: NSMenuItem) {
        guard [160,240,320,400].contains(sender.tag) else { return }
        let old = panel.frame, side = CGFloat(sender.tag)
        let proposed = NSRect(x: old.midX - side / 2, y: old.minY, width: side, height: side)
        place(fit(proposed, in: visibleScreen(for: old))); savePosition(); updateHitTest()
    }
    /// Describes the real autonomy timers. The 25% roll is never presented as a prediction.
    func idleMealSummary() -> String {
        if PetBehavior.autonomousEpisodeNodes.contains(behaviorNode) { return "挂机吃饭：正在进行" }
        if behavior.autonomySuppressed { return "挂机吃饭：当前被暂停或减弱动态等条件抑制" }
        if workStatus.state != "idle" { return "挂机吃饭：仅在已观察的闲置状态尝试" }
        let eta = behavior.mealEta(now: now)
        if eta <= 0 { return "挂机吃饭：下次检查即可尝试（每次 25% 概率）" }
        return "挂机吃饭：最早 \(Int(ceil(eta))) 秒后尝试（每次 25% 概率）"
    }
    @objc func revealLog() {
        guard let path = PetLog.shared.url else { return }
        PetLog.shared.flush()
        NSWorkspace.shared.activateFileViewerSelecting([path])
    }
    @objc func resetPosition() { place(defaultRect()); savePosition() }
    @objc func accessibilityChanged() {
        log("gate",["gate":"system_reduced_motion","value":NSWorkspace.shared.accessibilityDisplayShouldReduceMotion ? "true" : "false"])
        behavior.cancelTransient(now:now); syncPlayback()
    }
    @objc func sleepNow() { suspended = true; log("gate",["gate":"suspended","value":"true"]); behavior.cancelTransient(now:now); syncPlayback() }
    @objc func wakeNow() { suspended = false; log("gate",["gate":"suspended","value":"false"]); behavior.cancelTransient(now:now); syncPlayback() }
    @objc func screensChanged() { finishDrag() }
    @objc func about() {
        let alert = NSAlert()
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? ""
        alert.messageText = "灵梦桌宠 \(version)" + (previewBuild ? " · 独立预览" : "")
        alert.informativeText = "平时站立、低频眨眼；任务卡片显示真实工作状态，右键可喂饭团。单击回应、双击连眨眼、连续四次点击会皱眉，出现怒气符号和「むっ！」。挂机时偶尔自己吃一顿，其中一部分会在吃完后停下来慢慢咀嚼、目光飘一会儿再抬头。拖动后回到当前工作状态，右键可喂一口。\n\n只统计已通过本地钩子观察到的主任务。轮次结束不代表任务成功；长时间没有新事件会标为待确认。\n\n非官方东方同人示例。原有图片由用户提供，托腮素材由 AI 辅助制作并经用户确认，本地使用；未建立公开再分发授权。"
        alert.addButton(withTitle: "知道了"); NSApp.activate(ignoringOtherApps: true); alert.runModal()
    }
    @objc func quit() { NSApp.terminate(nil) }
    func selfTest() {
        do {
            var checks = [String]()
            try require(panel.level == .floating && !panel.isOpaque && !panel.hasShadow, "透明置顶窗口失败"); checks.append("transparent floating native panel")
            try require(clip.images.count == 40 && abs(clip.total - 4) < 0.00001 && clip.fallback == nil, "实际素材加载失败"); checks.append("40 verified frames and 4000 ms")
            try require(standing.images.count == 140 && abs(standing.total - 7) < 0.00001 && standing.fallback == nil,
                        "站姿素材加载失败"); checks.append("140 verified standing frames and 7000 ms")
            try require(standing.index(at:4.8) == 96 && standing.index(at:4.9) == 98 && standing.index(at:7) == 0,
                        "站姿时间轴失败"); checks.append("approved standing blink timing")
            if clips.contains(.workEatingTier2) {
                let tier2 = clips[.workEatingTier2]
                try require(tier2.fallback == nil && tier2.images.count == 16 && abs(tier2.total - 1.6) < 0.00001,
                            "task_2 精确素材加载失败")
                let work = PetBehavior(now:0); work.setWorkStatus("working",activeTaskCount:2,now:0)
                let full = work.presentation(now:0.4,availableWorkTiers:[2,3])
                try require(full.artwork == .workEatingTier2 && full.frame == 4 && image(for:full) === tier2.images[4],
                            "working + 2 未选择 task_2 精确帧")
                let reducedWork = work.presentation(now:0.9,motionAllowed:false,availableWorkTiers:[2,3])
                try require(reducedWork.artwork == .workEatingTier2 && reducedWork.frame == 0 && !reducedWork.wantsAnimation,
                            "task_2 减弱动态未固定声明代表帧")
                let degraded = work.presentation(now:1.0,availableWorkTiers:[3])
                try require(degraded.artwork == .standing && degraded.node == "work_fallback_tier_2",
                            "task_2 缺失时未安全降级")
                checks.append("task_2 native identity, exact frame selection, reduced motion and safe fallback")
            }
            if clips.contains(.workEatingTier3) {
                let tier3 = clips[.workEatingTier3]
                try require(tier3.fallback == nil && tier3.images.count == 1 && abs(tier3.total - 0.125) < 0.00001,
                            "task_3 静态素材加载失败")
                let work = PetBehavior(now:0); work.setWorkStatus("working",activeTaskCount:3,now:0)
                let full = work.presentation(now:0.4,availableWorkTiers:[2,3])
                try require(full.artwork == .workEatingTier3 && full.frame == 0 && !full.wantsAnimation && image(for:full) === tier3.images[0],
                            "working + 3 未选择 task_3 静态帧")
                let reducedWork = work.presentation(now:0.9,motionAllowed:false,availableWorkTiers:[2,3])
                try require(reducedWork.artwork == .workEatingTier3 && reducedWork.frame == 0 && !reducedWork.wantsAnimation,
                            "task_3 减弱动态未保持声明代表帧")
                let degraded = work.presentation(now:1.0,availableWorkTiers:[2])
                try require(degraded.artwork == .standing && degraded.node == "work_fallback_tier_3",
                            "task_3 缺失时未安全降级")
                checks.append("task_3 native identity, static frame selection, reduced motion and safe fallback")
            }
            if clips.contains(.workEatingTier4) {
                let tier4 = clips[.workEatingTier4]
                try require(tier4.fallback == nil && tier4.images.count == 1 && abs(tier4.total - 0.125) < 0.00001,
                            "task_4 静态素材加载失败")
                let work = PetBehavior(now:0); work.setWorkStatus("working",activeTaskCount:4,now:0)
                let full = work.presentation(now:0.4,availableWorkTiers:[2,3,4])
                try require(full.artwork == .workEatingTier4 && full.frame == 0 && !full.wantsAnimation && image(for:full) === tier4.images[0],
                            "working + 4 未选择 task_4 静态帧")
                let reducedWork = work.presentation(now:0.9,motionAllowed:false,availableWorkTiers:[2,3,4])
                try require(reducedWork.artwork == .workEatingTier4 && reducedWork.frame == 0 && !reducedWork.wantsAnimation,
                            "task_4 减弱动态未保持声明代表帧")
                let degraded = work.presentation(now:1.0,availableWorkTiers:[2,3])
                try require(degraded.artwork == .standing && degraded.node == "work_fallback_tier_4",
                            "task_4 缺失时未安全降级")
                checks.append("task_4 native identity, static frame selection, reduced motion and safe fallback")
            }
            try require(reaction.image != nil && reaction.failure == nil, "生气表情加载失败")
            let model = PetBehavior(now:0); model.setBase("working",now:0)
            for t in [0.0,0.1,0.2,0.3] { model.click(now:t) }
            try require(image(for:model.presentation(now:0.4)) === reaction.image, "连点未选择已确认表情")
            try require(image(for:model.presentation(now:0.4,motionAllowed:false)) === standing.images[0], "减弱动态仍显示生气表情")
            model.setBase("needs_input",now:0.5)
            try require(image(for:model.presentation(now:1.6)) === standing.images[0], "反应结束未恢复最新工作状态")
            checks.append("verified annoyed artwork selection, reduced motion and restoration")
            try require(clip.index(at: 0.6) == 6 && clip.index(at: 2.9) == 29 && clip.index(at: 4.0) == 0, "播放时间轴失败"); checks.append("chew, blink and loop timestamps")
            if !reduced { try require(frameIndex > 0 && timer != nil, "原生计时器未播放"); checks.append("actual timer advances animation") }
            let menu = makeMenu()
            if !reduced, let index = menu.items.firstIndex(where: {$0.action == #selector(togglePause)}) {
                menu.performActionForItem(at: index); try require(paused && timer == nil, "暂停菜单失败")
                togglePause(); try require(!paused && timer != nil, "恢复失败"); checks.append("real menu pause and resume actions")
            }
            preferences.set(true, forKey: "reduced"); syncPlayback()
            try require(frameIndex == 0 && timer == nil, "减弱动态失败"); checks.append("reduced motion stops timer at frame zero")
            preferences.set(false, forKey: "reduced"); syncPlayback()
            sleepNow(); try require(timer == nil, "休眠未停计时器"); wakeNow(); checks.append("sleep/wake playback lifecycle")
            let old = panel.frame.origin
            moveDuringDrag(startOrigin: old, startPointer: NSPoint(x:100,y:100), endPointer: NSPoint(x:20,y:160))
            try require(panel.frame.origin == NSPoint(x:old.x-80,y:old.y+60), "拖动位移失败"); finishDrag(); checks.append("native window drag displacement and clamp")
            let size = item("320 px", #selector(changeSize)); size.tag = 320; changeSize(size)
            try require(panel.frame.width == 320 && preferences.double(forKey:"size") == 320, "大小记忆失败")
            let saved = panel.frame; place(defaultRect()); restorePosition()
            try require(panel.frame == saved, "位置恢复失败"); checks.append("resize and restore persisted position")
            let corner = NSPoint(x:panel.frame.minX + 1,y:panel.frame.maxY - 1)
            let center = NSPoint(x:panel.frame.midX,y:panel.frame.midY)
            try require(!solid(at:corner) && solid(at:center), "透明区鼠标穿透失败"); checks.append("alpha-based pointer hit testing")
            let meal = PetPresentation(node:"eat_onigiri",frame:0,caption:"",wantsAnimation:true,artwork:.eating)
            try require(image(for:meal) === clip.images[0], "喂食素材选择失败")
            displayedArtwork = .eating
            try require(displayedAlpha === clip.alpha && solid(at:center), "坐姿命中未随素材切换")
            displayedArtwork = .standing
            try require(displayedAlpha === standing.alpha, "站姿命中未恢复")
            checks.append("feeding and standing select their own image and alpha canvas")
            for side: CGFloat in [160,240,320,400,596] {
                let b=NSRect(x:0,y:0,width:side,height:side)
                let r=artworkRect(in:b,artwork:.eating)
                let seatedSupport=r.minY + (688-582)/688 * r.height
                let shoeSupport=side * (1254-1230)/1254
                try require(abs(seatedSupport-shoeSupport) < side/596, "站坐支撑线未对齐")
                try require(abs(r.width/r.height-1) < 0.000001, "坐姿非等比缩放")
            }
            checks.append("approved uniform seated placement and support edge across five sizes")
            // The derived rule must reproduce the approved seated placement, so a new pose
            // family needs two reviewed numbers rather than new placement code.
            let derived = ClipSpec(artwork:.eating,directory:"Pet",option:"--asset-root",
                side:688,frameCount:40,fps:10,stateSet:"reference_onigiri_example",state:"eat_blink",
                baseKey:"PetBaseSHA256",manifestKey:"PetManifestSHA256",
                placement:.supportAligned(scale:482.0/596,xFraction:(57 + 2.796511627906966)/596),
                supportEdge:582.0/688,frameFile:{ _ in "" })
            for side: CGFloat in [160,240,320,400,596] {
                let b=NSRect(x:0,y:0,width:side,height:side)
                let approved=artworkRect(in:b,artwork:.eating), rule=artworkRect(in:b,spec:derived)
                try require(abs(rule.minX-approved.minX) < 0.000001 &&
                            abs(rule.width-approved.width) < 0.000001, "派生摆放的横向或缩放不一致")
                try require(abs(rule.minY-approved.minY) < side/596, "派生摆放偏离已批准坐姿超过容差")
                let ruleSupport=rule.minY + (1 - derived.supportEdge) * rule.height
                try require(abs(ruleSupport - side * (1254-1230)/1254) < 0.000001, "派生摆放未对齐鞋线")
            }
            checks.append("derived support-aligned placement reproduces the approved seated rect")
            if ClipSpec.registry.contains(where:{$0.artwork == .slouch}) {
                let slouch=clips[.slouch]
                try require(slouch.fallback == nil && slouch.images.count == 140,"托腮素材验证失败")
                try require(slouch.index(at:6.4) == 128 && slouch.index(at:6.65) == 133,"托腮眨眼时序失败")
                let rest=PetBehavior(now:0); rest.setBase("idle",now:0); rest.previewSlouch(now:1)
                try require(image(for:rest.presentation(now:7.4)) === slouch.images[128],"托腮原生帧未选择")
                try require(image(for:rest.presentation(now:7.4,motionAllowed:false)) === slouch.images[0],"托腮减弱动态未冻结")
                displayedArtwork = .slouch
                try require(displayedAlpha === slouch.alpha,"托腮命中未切换")
                displayedArtwork = .standing
                for side:CGFloat in [160,240,320,400,596] {
                    let r=artworkRect(in:NSRect(x:0,y:0,width:side,height:side),artwork:.slouch)
                    try require(abs(r.minY+(1-568.0/596)*r.height-side*(1-1230.0/1254))<0.000001,"托腮支撑线失败")
                    try require(r.minY+(1-569.0/596)*r.height >= 0,"榻榻米被窗口底边裁剪")
                }
                let autoRest=PetBehavior(now:0,randomUnit:{0.27}); autoRest.setBase("idle",now:0)
                try require(image(for:autoRest.presentation(now:180)) === slouch.images[0],"自动托腮未选择原生素材")
                try require(image(for:autoRest.presentation(now:186.4)) === slouch.images[128],"自动托腮眨眼失败")
                try require(image(for:autoRest.presentation(now:194)) === standing.images[0],"自动托腮未恢复站姿")
                checks.append("automatic slouch native selection, blink and return")
                checks.append("slouch native selection, blink, reduced motion, hit mask and approved support alignment")
            }

            if ClipSpec.registry.contains(where:{$0.artwork == .sleeping}) {
                let sleep=clips[.sleeping]
                try require(sleep.fallback == nil && sleep.images.count == (sleepChainPreview ? 5 : 1),"睡姿素材失败")
                let m=PetBehavior(now:0); m.setBase("idle",now:0); m.previewSleep(now:1)
                try require(image(for:m.presentation(now:2)) === sleep.images[0],"睡姿选帧失败")
                try require(image(for:m.presentation(now:3,motionAllowed:false)) === sleep.images[0],"睡姿减弱动态失败")
                try require(image(for:m.presentation(now:61)) === standing.images[0],"睡姿到期未恢复")
                displayedArtwork = .sleeping
                try require(displayedAlpha === sleep.alpha,"睡姿命中区域失败")
                displayedArtwork = .standing
                for side:CGFloat in [160,240,320,400,596] {
                    let b=NSRect(x:0,y:0,width:side,height:side)
                    let r=artworkRect(in:b,artwork:.sleeping)
                    let visible=NSRect(x:r.minX+35.0/1254*r.width,y:r.minY+(1-1207.0/1254)*r.height,
                                       width:1186.0/1254*r.width,height:1156.0/1254*r.height)
                    try require(b.contains(visible),"睡姿可见区域裁剪")
                    try require(abs(visible.minY-side*(1-1230.0/1254))<0.000001,"睡姿支撑线失败")
                }
                if sleepChainPreview {
                    let chain=PetBehavior(now:0);chain.setBase("idle",now:0);chain.previewSleepChain(now:1)
                    for (time,index) in [(1.0,1),(2.0,2),(3.0,3),(4.0,0),(5.0,3),(5.6,0),(10.0,3),(11.0,1)] {
                        try require(image(for:chain.presentation(now:time)) === sleep.images[index],"睡眠短链选帧失败")
                    }
                    try require(image(for:chain.presentation(now:13)) === standing.images[0],"睡眠短链未恢复")
                    chain.previewSleepChain(now:14)
                    try require(image(for:chain.presentation(now:15,motionAllowed:false)) === sleep.images[0],"短链减弱动态未冻结")
                    checks.append("sleep preview chain native phase mapping, return and reduced motion")
                }
                checks.append("selected static sleep pose, reduced motion, expiry, hit mask and five-size support alignment")
            }
            let autonomous=PetBehavior(now:0,randomUnit:{0}); autonomous.setBase("idle",now:0)
            try require(image(for:autonomous.presentation(now:60)) === clip.images[0] &&
                        image(for:autonomous.presentation(now:64)) === clip.images[0], "挂机未播放两轮")
            try require(image(for:autonomous.presentation(now:68)) === standing.images[0], "挂机结束未回原站姿")
            checks.append("autonomous model selects actual native meal twice then original standing")
            if let reportPath=option("--qa-report") {
                let directory=URL(fileURLWithPath:reportPath).deletingLastPathComponent()
                for side: CGFloat in [160,596] {
                    let sample=PetView(frame:NSRect(x:0,y:0,width:side,height:side)); sample.owner=self
                    for art in ClipSpec.registry.map(\.artwork) {
                        displayedArtwork=art; sample.image=clips[art].images[0]
                        let bitmap=sample.bitmapImageRepForCachingDisplay(in:sample.bounds)!
                        sample.cacheDisplay(in:sample.bounds,to:bitmap)
                        try bitmap.representation(using:.png,properties:[:])!.write(to:directory.appendingPathComponent("native-\(art.rawValue)-\(Int(side)).png"))
                    }
                }
                displayedArtwork = .standing
            }
            let negative = NSRect(x:-1920,y:-200,width:1920,height:1080)
            let fitted = fit(NSRect(x:-5000,y:2000,width:400,height:400), in:negative)
            try require(negative.contains(fitted), "副屏边界修复失败"); checks.append("negative-coordinate screen clamping")
            try require(fit(NSRect(x:0,y:0,width:400,height:400),in:NSRect(x:0,y:0,width:300,height:200)).height == 200, "小屏尺寸裁定失败")
            checks.append("small screen bounds")
            let petBefore = panel.frame, timerBefore = timer
            let buttonBefore = statusBubble.button.convert(statusBubble.button.bounds, to: nil)
                .offsetBy(dx: statusBubble.panel.frame.minX, dy: statusBubble.panel.frame.minY)
            statusBubble.button.performClick(nil)
            try require(!statusBubble.expanded && statusBubble.card.isHidden &&
                        preferences.bool(forKey:"statusBubbleCollapsed"), "收起按钮或偏好失败")
            try require(panel.frame == petBefore && timer === timerBefore &&
                        statusBubble.panel.frame == buttonBefore, "收起状态框移动了人物、按钮或重启了计时器")
            try require(statusBubble.panel.frame.width == 28, "收起后透明大窗口仍在占位")
            let restoredCollapsed = StatusBubbleController(expanded: !preferences.bool(forKey:"statusBubbleCollapsed"))
            try require(!restoredCollapsed.expanded, "状态框收起偏好恢复失败")
            statusBubble.button.performClick(nil)
            try require(statusBubble.expanded && !statusBubble.card.isHidden && panel.frame == petBefore,
                        "展开状态框失败")
            checks.append("real capsule button collapses/expands with stable pet, anchor and animation timer")
            let restoredBubble = StatusBubbleController(expanded: !preferences.bool(forKey:"statusBubbleCollapsed"))
            try require(restoredBubble.expanded, "状态框显示偏好恢复失败")
            checks.append("capsule expanded preference restores independently of character settings")
            let heldFrame = frameIndex
            statusBubble.update(WorkStatus(state:"working",active:2,unknown:1,providers:["codex"]))
            try require(statusBubble.card.titleField.stringValue == "Codex 工作状态" &&
                        statusBubble.card.detailField.stringValue == "工作中 · 2 项 · 另有 1 项待确认" &&
                        frameIndex == heldFrame && timer === timerBefore, "真实状态展示或动画独立性失败")
            statusBubble.update(WorkStatus(state:"round_ended",providers:["codex"]))
            try require(statusBubble.card.detailField.stringValue == "这一轮已结束", "结束被误写为任务成功")
            statusBubble.update(WorkStatus(state:"unknown",unknown:1))
            try require(statusBubble.card.titleField.stringValue == "工作状态" &&
                        statusBubble.card.detailField.stringValue == "工作状态待确认", "未知来源或状态文案不真实")
            checks.append("capsule shows observed counts, uncertainty and round-end without claiming task names or success")
            statusBubble.update(workStatus)
            let bubbleFrame = statusBubble.panel.frame, buttonFrame = statusBubble.button.frame
            let buttonPoint = NSPoint(x:bubbleFrame.minX+buttonFrame.midX,y:bubbleFrame.minY+buttonFrame.midY)
            let cornerPoint = NSPoint(x:bubbleFrame.minX+1,y:bubbleFrame.minY+1)
            try require(statusBubble.interactive(at:buttonPoint) && !statusBubble.interactive(at:cornerPoint),
                        "状态框透明区命中失败")
            checks.append("capsule circle accepts clicks while transparent corners pass through")
            for screen in [NSRect(x:0,y:0,width:1440,height:900), negative,
                           NSRect(x:0,y:0,width:300,height:200)] {
                for px in [screen.minX,screen.midX,screen.maxX-160] {
                    for py in [screen.minY,screen.midY,screen.maxY-160] {
                        let geometry = StatusBubbleLayout(pet:NSRect(x:px,y:py,width:160,height:160),screen:screen)
                        try require(screen.contains(geometry.expandedFrame) && screen.contains(geometry.collapsedFrame),
                                    "状态框屏幕边界失败")
                    }
                }
            }
            checks.append("27 capsule placements fit screen corners, negative display coordinates and small screens")
            let bottomPet = NSRect(x:100,y:0,width:160,height:160)
            let topPet = NSRect(x:100,y:740,width:160,height:160)
            let screen = NSRect(x:0,y:0,width:1440,height:900)
            try require(StatusBubbleLayout(pet:bottomPet,screen:screen).expandedFrame.minY > bottomPet.maxY &&
                        StatusBubbleLayout(pet:topPet,screen:screen).expandedFrame.maxY < topPet.minY,
                        "状态框上下避让失败")
            checks.append("capsule flips above/below at screen edges without repositioning pet")
            let compactSizes: [(CGFloat, CGFloat)] = [(160,208),(240,240),(320,280),(400,280)]
            for (side, width) in compactSizes {
                let compact = StatusBubbleLayout(pet:NSRect(x:100,y:200,width:side,height:side),screen:screen)
                try require(compact.expandedFrame.width == width && compact.card.height == 60 &&
                            compact.expandedFrame.height == 96 && compact.collapsedFrame.width == 28,
                            "紧凑状态框未随人物尺寸调整")
            }
            checks.append("compact capsule scales from 208 to 280 pt across all four pet sizes")

            // Observation log: isolated temporary files only, never the real user log.
            let logRoot = URL(fileURLWithPath:NSTemporaryDirectory()).appendingPathComponent("reimu-log-qa-\(UUID().uuidString)")
            try FileManager.default.createDirectory(at:logRoot,withIntermediateDirectories:true)
            defer { try? FileManager.default.removeItem(at:logRoot) }
            let logPath = logRoot.appendingPathComponent("behavior.jsonl")
            let probe = PetLog(explicit:logPath.path,disabled:false)
            let traced = PetBehavior(now:0,randomUnit:{0})
            traced.onTrace = { kind, detail in probe.write(kind,detail) }
            traced.setBase("idle",now:0)
            _=traced.presentation(now:60)
            _=traced.presentation(now:68)
            probe.flush()
            let lines = try String(contentsOf:logPath,encoding:.utf8).split(separator:"\n").map(String.init)
            var decoded = [[String:Any]]()
            for line in lines where !line.isEmpty {
                guard let object = try JSONSerialization.jsonObject(with:Data(line.utf8)) as? [String:Any] else {
                    throw AssetFailure(message:"行为日志不是逐行 JSON")
                }
                try require(object["kind"] is String && object["at"] is String && object["uptime"] is Double,
                            "行为日志缺少必要字段")
                decoded.append(object)
            }
            let kinds = decoded.compactMap { $0["kind"] as? String }
            try require(kinds.contains("base") && kinds.contains("meal_attempt") &&
                        kinds.contains("action_start") && kinds.contains("action_end"),
                        "行为日志未记录挂机吃饭的完整生命周期")
            let attempt = decoded.first { $0["kind"] as? String == "meal_attempt" }
            try require(attempt?["hit"] as? String == "true" && attempt?["roll"] as? String == "0.000",
                        "行为日志未记录真实的随机结果")
            checks.append("behavior log records the real idle-meal lifecycle as one JSON object per line")

            let cap = 4096
            let bulk = PetLog(explicit:logPath.path,disabled:false,limit:cap)
            for index in 0..<400 { bulk.write("fill",["index":String(index)]) }
            bulk.flush()
            let rolled = logPath.appendingPathExtension("1")
            try require(FileManager.default.fileExists(atPath:rolled.path), "行为日志未轮转")
            let live = (try FileManager.default.attributesOfItem(atPath:logPath.path)[.size] as? Int) ?? -1
            let kept = (try FileManager.default.attributesOfItem(atPath:rolled.path)[.size] as? Int) ?? -1
            try require(live >= 0 && live <= cap + 1024 && kept > 0 && kept <= cap + 1024,
                        "轮转后的行为日志仍超出上限")
            bulk.write("after-roll",["ok":"true"]); bulk.flush()
            let resumed = try String(contentsOf:logPath,encoding:.utf8)
            try require(resumed.contains("after-roll"), "轮转后无法继续记录")
            checks.append("behavior log rotates at one bounded generation and keeps recording")

            let silent = PetLog(explicit:logRoot.appendingPathComponent("never.jsonl").path,disabled:true)
            silent.write("ignored"); silent.flush()
            try require(silent.url == nil && !FileManager.default.fileExists(atPath:logRoot.appendingPathComponent("never.jsonl").path),
                        "--no-behavior-log 未关闭记录")
            checks.append("--no-behavior-log writes nothing at all")

            let summaryModel = PetBehavior(now:0)
            behaviorNode = "idle_relaxed"
            workStatus = WorkStatus(state:"working",active:2,unknown:0,providers:["claude"])
            try require(idleMealSummary().contains("仅在已观察的闲置状态"), "非闲置摘要错误")
            workStatus = WorkStatus(state:"idle",active:0,unknown:0,providers:["claude"])
            behavior.setBase("idle",now:now)
            try require(idleMealSummary().contains("秒后尝试") || idleMealSummary().contains("下次检查即可尝试"),
                        "闲置摘要未报告真实倒计时")
            for node in PetBehavior.autonomousEpisodeNodes.sorted() {
                behaviorNode = node
                try require(idleMealSummary() == "挂机吃饭：正在进行", "进行中摘要错误：" + node)
            }
            try require(PetBehavior.autonomousEpisodeNodes == [PetAction.idleMeal.rawValue,
                                                               PetAction.pauseChew.rawValue, PetAction.tableSlouch.rawValue],
                        "挂机动作集合与动作池不一致")
            behaviorNode = "idle_relaxed"
            _=summaryModel
            checks.append("menu reports the real autonomy timer without predicting the random roll")

            let report: [String: Any] = ["status":"pass","checks":checks,"count":checks.count,
                "scope":"Native window/menu/timer behavior exercised programmatically; physical desktop review separate",
                "system_reduced_motion":NSWorkspace.shared.accessibilityDisplayShouldReduceMotion]
            if let path = option("--qa-report") { try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted,.sortedKeys]).write(to:URL(fileURLWithPath:path)) }
            print(String(data:try JSONSerialization.data(withJSONObject:report,options:[.sortedKeys]),encoding:.utf8)!)
            NSApp.terminate(nil)
        } catch { fputs("SELF TEST FAILED: \(error)\n",stderr); exit(2) }
    }
}

func option(_ name: String) -> String? {
    guard let i = CommandLine.arguments.firstIndex(of:name), i+1 < CommandLine.arguments.count else { return nil }
    return CommandLine.arguments[i+1]
}
if let path = option("--status-snapshot") {
    let now = option("--at").flatMap(Double.init) ?? Date().timeIntervalSince1970
    let status = WorkStatus.load(URL(fileURLWithPath:path),now:now)
    let result: [String:Any] = ["state":status.state,"active":status.active,"unknown":status.unknown,"providers":status.providers]
    print(String(data:try! JSONSerialization.data(withJSONObject:result,options:.sortedKeys),encoding:.utf8)!)
    exit(0)
}
let qa = CommandLine.arguments.contains("--self-test")
let resources = Bundle.main.resourceURL!
let reactionRoot = option("--reaction-root").map { URL(fileURLWithPath:$0) } ?? resources.appendingPathComponent("Reactions")
let reactionSHA = Bundle.main.object(forInfoDictionaryKey:"PetAnnoyedSHA256") as? String ?? ""
let reaction = ReactionArt.load(root:reactionRoot,sha:reactionSHA)
do {
    var loaded = [PetArtwork: Clip]()
    for spec in ClipSpec.registry {
        let root = option(spec.option).map { URL(fileURLWithPath:$0) } ?? resources.appendingPathComponent(spec.directory)
        do {
            loaded[spec.artwork] = try Clip.load(root:root,spec:spec,
                baseSHA:Bundle.main.object(forInfoDictionaryKey:spec.baseKey) as? String ?? "",
                manifestSHA:Bundle.main.object(forInfoDictionaryKey:spec.manifestKey) as? String ?? "")
        } catch where spec.artwork == .workEatingTier2 || spec.artwork == .workEatingTier3 || spec.artwork == .workEatingTier4 {
            guard let standing = loaded[.standing] else { throw error }
            loaded[spec.artwork] = Clip(base:standing.base,alpha:standing.alpha,images:[standing.base],
                                           durations:[0],fallback:error.localizedDescription)
        }
    }
    let clips = ClipSet(loaded)
    let clip = clips[.eating], standing = clips[.standing]
    if CommandLine.arguments.contains("--validate-assets") {
        let report:[String:Any] = ["status":clip.fallback == nil ? "animated" : "static-fallback","frames":clip.images.count,"duration":clip.total,"reason":clip.fallback ?? "none", "annoyed":reaction.image == nil ? "unavailable" : "verified", "annoyed_reason":reaction.failure ?? "none",
            "sleep_frames":ClipSpec.registry.contains(where:{$0.artwork == .sleeping}) ? clips[.sleeping].images.count : 0,
            "sleep_reason":ClipSpec.registry.contains(where:{$0.artwork == .sleeping}) ? (clips[.sleeping].fallback ?? "none") : "not packaged",
            "slouch_frames":ClipSpec.registry.contains(where:{$0.artwork == .slouch}) ? clips[.slouch].images.count : 0,
            "slouch_reason":ClipSpec.registry.contains(where:{$0.artwork == .slouch}) ? (clips[.slouch].fallback ?? "none") : "not packaged",
            "work_tier_2_frames":clips.contains(.workEatingTier2) ? clips[.workEatingTier2].images.count : 0,
            "work_tier_2_duration":clips.contains(.workEatingTier2) ? clips[.workEatingTier2].total : 0,
            "work_tier_2_reason":clips.contains(.workEatingTier2) ? (clips[.workEatingTier2].fallback ?? "none") : "not packaged",
            "work_tier_3_frames":clips.contains(.workEatingTier3) ? clips[.workEatingTier3].images.count : 0,
            "work_tier_3_duration":clips.contains(.workEatingTier3) ? clips[.workEatingTier3].total : 0,
            "work_tier_3_reason":clips.contains(.workEatingTier3) ? (clips[.workEatingTier3].fallback ?? "none") : "not packaged",
            "work_tier_4_frames":clips.contains(.workEatingTier4) ? clips[.workEatingTier4].images.count : 0,
            "work_tier_4_duration":clips.contains(.workEatingTier4) ? clips[.workEatingTier4].total : 0,
            "work_tier_4_reason":clips.contains(.workEatingTier4) ? (clips[.workEatingTier4].fallback ?? "none") : "not packaged",
            "standing_frames":standing.images.count,"standing_duration":standing.total,"standing_reason":standing.fallback ?? "none"]
        print(String(data:try JSONSerialization.data(withJSONObject:report,options:[.sortedKeys]),encoding:.utf8)!)
    } else {
        let prefs = qa ? UserDefaults(suiteName:option("--qa-domain") ?? appID + ".qa")! : UserDefaults.standard
        let app = NSApplication.shared
        let delegate = PetApp(clips:clips,reaction:reaction,preferences:prefs,qa:qa)
        app.delegate = delegate; app.run()
    }
} catch {
    fputs("ASSET ERROR: \(error.localizedDescription)\n",stderr)
    if !CommandLine.arguments.contains("--validate-assets") {
        _ = NSApplication.shared
        let alert = NSAlert(); alert.messageText = "灵梦桌宠无法启动"
        alert.informativeText = "静态基准图片缺失或损坏。请重新复制完整的应用。\n\n\(error.localizedDescription)"
        alert.runModal()
    }
    exit(1)
}
