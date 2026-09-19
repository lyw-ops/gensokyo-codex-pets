import AppKit

// Presentation only: uses the same observed snapshot as the character, never writes it.
struct StatusBubbleText {
    let title: String
    let detail: String
    init(_ status: WorkStatus) {
        title = status.providers == ["codex"] ? "Codex 工作状态" :
            status.providers == ["claude"] ? "Claude Code 工作状态" : "工作状态"
        detail = status.label + (status.unknown > 0 && status.state != "unknown"
            ? " · 另有 \(status.unknown) 项待确认" : "")
    }
}

struct StatusBubbleLayout {
    let expandedFrame: NSRect
    let card: NSRect
    let button: NSRect
    var collapsedFrame: NSRect {
        button.offsetBy(dx: expandedFrame.minX, dy: expandedFrame.minY)
    }
    init(pet: NSRect, screen: NSRect) {
        let width = min(max(pet.width, 208), 280, screen.width), height = min(96, screen.height)
        let buttonSide = min(28, width, height), cardHeight = min(60, max(0, height - 36))
        var x = pet.midX - width / 2
        var y = pet.minY - height - 8
        var buttonAtTop = true
        if y < screen.minY {
            y = pet.maxY + 8
            buttonAtTop = false
            if y + height > screen.maxY {
                // When vertical space runs out, use the roomier side before clamping.
                x = pet.minX - screen.minX >= screen.maxX - pet.maxX
                    ? pet.minX - width - 8 : pet.maxX + 8
                y = pet.midY - height / 2
                buttonAtTop = true
            }
        }
        x = min(max(x, screen.minX), screen.maxX - width)
        y = min(max(y, screen.minY), screen.maxY - height)
        expandedFrame = NSRect(x: x, y: y, width: width, height: height)
        button = NSRect(x: (width - buttonSide) / 2,
                        y: buttonAtTop ? height - buttonSide : 0,
                        width: buttonSide, height: buttonSide)
        card = NSRect(x: 0, y: buttonAtTop ? 0 : height - cardHeight,
                      width: width, height: cardHeight)
    }
}

final class StatusChevron: NSButton {
    var expanded = true { didSet { needsDisplay = true } }
    private(set) var trackingPress = false
    override var isOpaque: Bool { false }
    override func mouseDown(with event: NSEvent) {
        trackingPress = true
        defer { trackingPress = false }
        super.mouseDown(with: event)
    }
    override func draw(_ dirtyRect: NSRect) {
        let circle = NSBezierPath(ovalIn: bounds.insetBy(dx: 0.75, dy: 0.75))
        NSColor(white: isHighlighted ? 0.23 : 0.14, alpha: 0.97).setFill(); circle.fill()
        NSColor(white: 0.30, alpha: 1).setStroke(); circle.lineWidth = 1; circle.stroke()
        let path = NSBezierPath(), mid = bounds.midY
        let direction: CGFloat = (expanded ? 1 : -1) * (isFlipped ? -1 : 1)
        path.move(to: NSPoint(x: bounds.midX - 5, y: mid - 2 * direction))
        path.line(to: NSPoint(x: bounds.midX, y: mid + 4 * direction))
        path.line(to: NSPoint(x: bounds.midX + 5, y: mid - 2 * direction))
        path.lineWidth = 1.7; path.lineCapStyle = .round; path.lineJoinStyle = .round
        NSColor(white: 0.94, alpha: 1).setStroke(); path.stroke()
    }
}

final class StatusCapsule: NSView {
    let titleField = NSTextField(labelWithString: "")
    let detailField = NSTextField(labelWithString: "")
    override var isOpaque: Bool { false }
    override init(frame: NSRect) {
        super.init(frame: frame)
        titleField.font = .systemFont(ofSize: 14, weight: .semibold)
        titleField.textColor = NSColor(white: 0.96, alpha: 1)
        detailField.font = .systemFont(ofSize: 12)
        detailField.textColor = NSColor(white: 0.66, alpha: 1)
        for field in [titleField, detailField] {
            field.lineBreakMode = .byTruncatingTail
            field.maximumNumberOfLines = 1
            field.isSelectable = false
            addSubview(field)
        }
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }
    override func layout() {
        super.layout()
        titleField.frame = NSRect(x: 18, y: bounds.midY, width: max(0, bounds.width - 36), height: 20)
        detailField.frame = NSRect(x: 18, y: bounds.midY - 20, width: max(0, bounds.width - 36), height: 19)
    }
    override func draw(_ dirtyRect: NSRect) {
        let shape = NSBezierPath(roundedRect: bounds.insetBy(dx: 0.75, dy: 0.75),
                                 xRadius: bounds.height / 2, yRadius: bounds.height / 2)
        NSColor(white: 0.13, alpha: 0.97).setFill(); shape.fill()
        NSColor(white: 0.25, alpha: 0.95).setStroke(); shape.lineWidth = 1; shape.stroke()
    }
}

final class StatusBubbleView: NSView {
    var contextMenu: (() -> NSMenu)?
    override var isOpaque: Bool { false }
    override func rightMouseDown(with event: NSEvent) {
        if let menu = contextMenu?() { NSMenu.popUpContextMenu(menu, with: event, for: self) }
    }
}

final class StatusBubbleController: NSObject {
    let panel: PetPanel
    let content = StatusBubbleView(frame: .zero)
    let card = StatusCapsule(frame: .zero)
    let button = StatusChevron(frame: .zero)
    private(set) var expanded: Bool
    private var geometry: StatusBubbleLayout?
    var onToggle: (() -> Void)?
    init(expanded: Bool) {
        self.expanded = expanded
        panel = PetPanel(contentRect: .zero, styleMask: [.borderless, .nonactivatingPanel],
                         backing: .buffered, defer: false)
        super.init()
        panel.title = "灵梦任务状态框"
        panel.isOpaque = false; panel.backgroundColor = .clear; panel.hasShadow = false
        panel.level = .floating; panel.hidesOnDeactivate = false; panel.isReleasedWhenClosed = false
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.contentView = content
        button.title = ""; button.isBordered = false; button.setButtonType(.momentaryChange)
        button.target = self; button.action = #selector(toggle)
        content.addSubview(card); content.addSubview(button)
    }
    @objc private func toggle() { onToggle?() }
    func update(_ status: WorkStatus) {
        let text = StatusBubbleText(status)
        card.titleField.stringValue = text.title
        card.detailField.stringValue = text.detail
        card.titleField.toolTip = text.title; card.detailField.toolTip = text.detail
    }
    func place(pet: NSRect, screen: NSRect) {
        geometry = StatusBubbleLayout(pet: pet, screen: screen)
        applyLayout()
    }
    func setExpanded(_ value: Bool) { expanded = value; applyLayout() }
    private func applyLayout() {
        guard let geometry = geometry else { return }
        panel.setFrame(expanded ? geometry.expandedFrame : geometry.collapsedFrame, display: true)
        button.frame = expanded ? geometry.button : content.bounds
        card.frame = geometry.card; card.isHidden = !expanded
        card.needsLayout = true
        button.expanded = expanded
        let label = expanded ? "收起任务状态框" : "展开任务状态框"
        button.setAccessibilityLabel(label); button.toolTip = label
        updateHitTest()
    }
    func interactive(at point: NSPoint) -> Bool {
        let local = NSPoint(x: point.x - panel.frame.minX, y: point.y - panel.frame.minY)
        if NSBezierPath(ovalIn: button.frame).contains(local) { return true }
        return expanded && NSBezierPath(roundedRect: card.frame, xRadius: card.frame.height / 2,
                                         yRadius: card.frame.height / 2).contains(local)
    }
    func updateHitTest() {
        if !button.trackingPress { panel.ignoresMouseEvents = !interactive(at: NSEvent.mouseLocation) }
    }
}
