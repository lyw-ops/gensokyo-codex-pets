import Foundation

// Behavior owns only timing/input arbitration. Work observation and food tiers stay outside.
enum PetArtwork: String { case standing, eating, slouch, sleeping }

/// Frame selection is data, not code. A new action declares the program it plays
/// instead of adding another branch to the presentation switch.
enum FramePlan {
    /// One held drawing for the whole action.
    case still(Int)
    /// Explicit per-frame selections; the last entry holds if the action outlives the table.
    case table([Int], fps: Double)
    /// Plays forward once and holds the final frame.
    case ramp(fps: Double, limit: Int)
    /// Repeats a whole clip for as long as the action runs.
    case loop(fps: Double, count: Int)

    func index(at elapsed: Double) -> Int {
        let tick = max(0, Int(max(0, elapsed) * rate))
        switch self {
        case .still(let frame): return frame
        case .table(let frames, _): return frames[min(frames.count - 1, tick)]
        case .ramp(_, let limit): return min(limit, tick)
        case .loop(_, let count): return count > 0 ? tick % count : 0
        }
    }

    private var rate: Double {
        switch self {
        case .still: return 0
        case .table(_, let fps), .ramp(let fps, _), .loop(let fps, _): return fps
        }
    }
}

/// Everything the arbitration loop needs to know about one action.
/// Adding an action is one enum case plus one row of this table.
struct ActionSpec {
    /// `nil` holds the action until something interrupts it or `maxHold` elapses.
    let duration: Double?
    let maxHold: Double?
    let priority: Int
    let caption: String
    let artwork: PetArtwork
    /// Seconds this action rests before it may be chosen again.
    let cooldown: Double
    /// Seconds the whole pool rests after this action — the pacing floor between any two
    /// self-started behaviors. Kept separate from `cooldown` so a cheap frequent beat can
    /// rest briefly for everyone while still waiting a long time for its own repeat.
    let globalRest: Double
    /// A locked action refuses every peer, not just lower priorities.
    let locked: Bool
    let usesReactionArt: Bool
    let frames: FramePlan
    /// Default continuation when this action completes; a pool entry may override it.
    let then: PetAction?

    init(duration: Double?, maxHold: Double? = nil, priority: Int, caption: String = "",
         artwork: PetArtwork = .standing, cooldown: Double = 0, globalRest: Double = 0,
         locked: Bool = false, usesReactionArt: Bool = false, frames: FramePlan,
         then: PetAction? = nil) {
        self.duration = duration; self.maxHold = maxHold; self.priority = priority
        self.caption = caption; self.artwork = artwork; self.cooldown = cooldown
        self.globalRest = globalRest; self.locked = locked; self.usesReactionArt = usesReactionArt
        self.frames = frames; self.then = then
    }
}

enum PetAction: String, CaseIterable {
    case notice = "react_notice", poke = "react_poke", annoyed = "react_annoyed"
    case feed = "eat_onigiri", idleMeal = "idle_meal", landing = "drag_land"
    case pauseChew = "pause_chew"
    case tableSlouch = "idle_table_slouch"
    case sleepPreview = "sleep_table_preview"
    case sleepChainPreview = "sleep_chain_preview"

    /// Frame numbers index the packaged clip that the action's artwork names.
    /// Standing 96-100 are the approved eyelid poses; eating 4-7 are the chew pulse and
    /// 27/31 the half-lidded drift, so no action invents a drawing that is not shipped.
    // Compressed editorial preview only. Production sleep scheduling is deliberately absent.
    static let sleepPreviewFrames = Array(repeating:1,count:5) + Array(repeating:2,count:5)
        + Array(repeating:3,count:5) + Array(repeating:0,count:5) + Array(repeating:3,count:3)
        + Array(repeating:0,count:22) + Array(repeating:3,count:5) + Array(repeating:1,count:10)
    static let production: [PetAction: ActionSpec] = [
        .sleepChainPreview: ActionSpec(duration: 12, priority: 20, artwork: .sleeping,
                                       frames: .table(sleepPreviewFrames,fps:5)),
        .sleepPreview: ActionSpec(duration: 60, priority: 20, artwork: .sleeping, frames: .still(0)),
        .tableSlouch: ActionSpec(duration: 14, priority: 20, artwork: .slouch, cooldown: 900, globalRest: 180, frames: .loop(fps:20,count:140)),
        .notice: ActionSpec(duration: 0.55, priority: 70, caption: "嗯？",
                            frames: .table([96, 97, 98, 99, 100, 0], fps: 20)),
        .poke: ActionSpec(duration: 0.85, priority: 71, caption: "戳到啦",
                          frames: .table([96, 97, 98, 99, 100, 0, 0, 0, 96, 97, 98, 99, 100, 0], fps: 20)),
        .annoyed: ActionSpec(duration: 1.2, priority: 72, caption: "让我吃完嘛", artwork: .eating,
                             locked: true, usesReactionArt: true, frames: .still(0)),
        .landing: ActionSpec(duration: 0.3, priority: 60, caption: "站好了",
                             locked: true, frames: .still(0)),
        .feed: ActionSpec(duration: 4, priority: 30, caption: "再吃一口", artwork: .eating,
                          cooldown: 180, globalRest: 180, frames: .ramp(fps: 10, limit: 39)),
        .idleMeal: ActionSpec(duration: 8, priority: 29, artwork: .eating, cooldown: 180,
                              globalRest: 180, frames: .loop(fps: 10, count: 40)),
        // Chewing slows to two pulses, the gaze drifts behind half-lidded eyes, then she
        // looks up again. Retimed shipped drawings only; nothing new was authored for it.
        .pauseChew: ActionSpec(duration: 2, priority: 28, artwork: .eating, cooldown: 180,
                               globalRest: 180, frames: .table([4, 4, 5, 5, 6, 6, 7, 7,
                                               27, 27, 27, 27, 27, 27,
                                               31, 31, 0, 0, 0, 0], fps: 10)),
    ]
}

/// One weighted outcome of an autonomy tick. Weights are absolute probabilities and
/// deliberately do not sum to 1: the remainder is Reimu doing nothing, which stays
/// the most likely outcome of every tick.
struct PoolEntry {
    let action: PetAction
    let weight: Double
    let minimumQuiet: Double
    /// Overrides the action's own `then` for this outcome.
    let then: PetAction?
    /// Extra eligibility beyond the observed-idle gate and the per-action cooldown.
    let requires: (String) -> Bool

    init(action: PetAction, weight: Double, minimumQuiet: Double = 0, then: PetAction? = nil,
         requires: @escaping (String) -> Bool = { _ in true }) {
        self.minimumQuiet = minimumQuiet
        self.action = action; self.weight = weight; self.then = then; self.requires = requires
    }

    /// The approved meal keeps its 25% total. Splitting that same 25% into a plain meal and
    /// a meal that trails off into a chewing pause adds a beat without making Reimu eat more
    /// often, and costs no extra random draw.
    static let production: [PoolEntry] = [
        PoolEntry(action: .idleMeal, weight: 0.15),
        PoolEntry(action: .idleMeal, weight: 0.10, then: .pauseChew),
        PoolEntry(action: .tableSlouch, weight: 0.05, minimumQuiet: 180),
    ]
}

final class PetBehavior {
    private(set) var base = "disconnected"
    private(set) var action: PetAction?
    private(set) var dragging = false
    private var baseStarted: Double
    private var actionStarted = 0.0
    private var lastClick = -Double.infinity
    private var clickCount = 0
    private var clickBlockedUntil = -Double.infinity
    private var pendingChain: PetAction?
    /// Earliest next autonomy tick. Kept under the old name so the log stays readable.
    private(set) var nextMealAttempt: Double
    /// Pool-wide rest after any action that carries a cooldown.
    private(set) var mealBlockedUntil = -Double.infinity
    /// Per-action rest, so one action resting never silences the others.
    private var blockedUntil = [PetAction: Double]()
    private var autonomyEnabled = true
    private var slouchAvailable = true
    private var quietStarted: Double
    private(set) var autonomousEpisodeActive = false
    private let randomUnit: () -> Double
    private let specs: [PetAction: ActionSpec]
    private let pool: [PoolEntry]
    // Observation sink only. It never chooses a pose and stays nil for pure logic tests.
    var onTrace: ((String, [String: String]) -> Void)?

    init(now: Double, randomUnit: @escaping () -> Double = { Double.random(in: 0..<1) },
         specs: [PetAction: ActionSpec] = PetAction.production,
         pool: [PoolEntry] = PoolEntry.production) {
        baseStarted = now
        quietStarted = now
        nextMealAttempt = now + 60
        self.randomUnit = randomUnit
        self.specs = specs
        self.pool = pool
    }

    private func spec(_ action: PetAction) -> ActionSpec {
        specs[action] ?? PetAction.production[action]!
    }

    /// Earliest moment an automatic action could be attempted, as seconds from `now`.
    /// Negative means an attempt is already due; eligibility still needs observed idle.
    func mealEta(now: Double) -> Double { max(nextMealAttempt, mealBlockedUntil) - now }
    var autonomySuppressed: Bool { !autonomyEnabled }
    /// Node names that belong to a self-started episode, derived from the pool so a new
    /// outcome shows up in the menu without anyone editing a second list.
    static let autonomousEpisodeNodes: Set<String> = Set(
        PoolEntry.production.flatMap { entry in
            [entry.action.rawValue] + (entry.then.map { [$0.rawValue] } ?? [])
        })
    private func trace(_ kind: String, _ detail: [String: String] = [:]) { onTrace?(kind, detail) }
    private static func seconds(_ value: Double) -> String { String(format: "%.3f", value) }

    private func resetQuiet(now: Double) {
        quietStarted = now
        nextMealAttempt = max(now + 60, mealBlockedUntil)
    }

    private func finishAction(now: Double, reason: String) {
        // Only a natural end continues an episode; every interruption returns to the base.
        var successor: PetAction?
        if reason == "completed", let current = action {
            successor = pendingChain ?? spec(current).then
        }
        if let ended = action {
            let limits = spec(ended)
            if limits.cooldown > 0 { blockedUntil[ended] = now + limits.cooldown }
            if limits.globalRest > 0 { mealBlockedUntil = max(mealBlockedUntil, now + limits.globalRest) }
            trace("action_end", ["action": ended.rawValue, "reason": reason,
                                 "elapsed": PetBehavior.seconds(max(0, now - actionStarted))])
        }
        action = nil
        autonomousEpisodeActive = false
        pendingChain = nil
        // A continuation starts from here, so the episode never flashes back to standing.
        if let successor, start(successor, now: now) { autonomousEpisodeActive = true; return }
        resetQuiet(now: now)
        baseStarted = now // Direct return begins on the approved open-eye standing pose.
        trace("quiet_reset", ["reason": reason, "meal_eta": PetBehavior.seconds(mealEta(now: now))])
    }

    func setBase(_ state: String, now: Double) {
        guard state != base else { return } // Counts and provider metadata never restart motion.
        let previous = base
        base = state
        baseStarted = now
        trace("base", ["from": previous, "to": state])
        if state == "failed" || (autonomousEpisodeActive && state != "idle") {
            finishAction(now: now, reason: state == "failed" ? "failed" : "left_idle")
        }
        resetQuiet(now: now)
        // A reaction returns to this newly selected base when it ends.
    }

    private func expire(now: Double) {
        guard let current = action else { return }
        let limits = spec(current)
        if let duration = limits.duration {
            if now >= actionStarted + duration { finishAction(now: now, reason: "completed") }
        } else if let hold = limits.maxHold, now >= actionStarted + hold {
            finishAction(now: now, reason: "max_hold")
        }
    }

    @discardableResult
    private func start(_ next: PetAction, now: Double) -> Bool {
        expire(now: now)
        guard base != "failed", !dragging else { return false }
        if let current = action {
            if spec(current).locked || spec(current).priority >= spec(next).priority { return false }
            finishAction(now: now, reason: "preempted_by_" + next.rawValue)
        }
        action = next
        actionStarted = now
        trace("action_start", ["action": next.rawValue, "base": base,
                               "duration": PetBehavior.seconds(spec(next).duration ?? 0)])
        return true
    }

    func previewSleepChain(now: Double) {
        resetQuiet(now: now)
        _ = start(.sleepChainPreview, now: now)
    }

    func previewSleep(now: Double) {
        resetQuiet(now: now)
        _ = start(.sleepPreview, now: now)
    }

    func previewSlouch(now: Double) {
        resetQuiet(now: now)
        _ = start(.tableSlouch, now: now)
    }

    func click(now: Double) {
        expire(now: now)
        resetQuiet(now: now)
        guard !dragging, base != "failed", now >= clickBlockedUntil else { return }
        if let current = action, spec(current).locked { return }
        clickCount = now - lastClick <= 0.5 ? min(4, clickCount + 1) : 1
        lastClick = now
        let next: PetAction = clickCount >= 4 ? .annoyed : clickCount >= 2 ? .poke : .notice
        if start(next, now: now), next == .annoyed {
            clickBlockedUntil = now + (spec(next).duration ?? 0) + 2
            clickCount = 0
        }
    }

    func feed(now: Double) { resetQuiet(now: now); _ = start(.feed, now: now) }

    func beginDrag(now: Double) {
        finishAction(now: now, reason: "drag") // Physical pointer movement owns the body immediately.
        dragging = true
        clickCount = 0
    }

    func endDrag(now: Double) {
        guard dragging else { return }
        resetQuiet(now: now)
        dragging = false
        _ = start(.landing, now: now)
    }

    func cancelTransient(now: Double) {
        finishAction(now: now, reason: "cancelled")
        clickCount = 0
    }

    /// One weighted draw decides between doing nothing and one pool outcome, so adding an
    /// outcome never adds a random draw or changes another outcome's probability.
    private func attemptAutonomy(now: Double, slouchAllowed: Bool) {
        let interval = 30 + 15 * randomUnit()
        nextMealAttempt = now + interval
        let roll = randomUnit()
        var cumulative = 0.0
        var chosen: PoolEntry?
        for entry in pool {
            guard now >= blockedUntil[entry.action] ?? -.infinity, entry.requires(base),
                  now - quietStarted >= entry.minimumQuiet,
                  entry.action != .tableSlouch || slouchAllowed else { continue }
            cumulative += entry.weight
            if roll < cumulative { chosen = entry; break }
        }
        if let chosen {
            pendingChain = chosen.then
            if start(chosen.action, now: now) { autonomousEpisodeActive = true }
            else { pendingChain = nil }
        }
        var detail = ["roll": PetBehavior.seconds(roll), "hit": chosen != nil ? "true" : "false",
                      "retry_in": PetBehavior.seconds(interval)]
        if let chosen {
            detail["picked"] = chosen.action.rawValue
            if let then = chosen.then { detail["then"] = then.rawValue }
        }
        trace("meal_attempt", detail)
    }

    func presentation(now: Double, motionAllowed: Bool = true, mealsAllowed: Bool = true, slouchAllowed: Bool = true) -> PetPresentation {
        expire(now: now)
        let enabled = motionAllowed && mealsAllowed
        if enabled != autonomyEnabled {
            autonomyEnabled = enabled
            trace("autonomy", ["enabled": enabled ? "true" : "false",
                               "motion": motionAllowed ? "true" : "false",
                               "meals": mealsAllowed ? "true" : "false"])
            if !enabled && autonomousEpisodeActive { finishAction(now: now, reason: "autonomy_off") }
            resetQuiet(now: now)
        }
        if slouchAllowed != slouchAvailable {
            slouchAvailable = slouchAllowed
            resetQuiet(now: now)
        }
        if !slouchAllowed && autonomousEpisodeActive && action == .tableSlouch {
            finishAction(now: now, reason: "slouch_unavailable")
        }
        // Only observed idle is eligible. No catch-up attempts after a delayed tick.
        if enabled && base == "idle" && action == nil && !dragging && now >= nextMealAttempt {
            attemptAutonomy(now: now, slouchAllowed: slouchAllowed)
        }
        if base == "failed" { return PetPresentation(node: "failed", frame: 0, caption: "", wantsAnimation: false) }
        if dragging { return PetPresentation(node: "drag_float", frame: 0, caption: "被你挪走了", wantsAnimation: false) }
        if let current = action {
            let plan = spec(current)
            return PetPresentation(node: current.rawValue,
                                   frame: motionAllowed ? plan.frames.index(at: now - actionStarted) : 0,
                                   caption: plan.caption, wantsAnimation: true,
                                   usesAnnoyedArt: motionAllowed && plan.usesReactionArt,
                                   artwork: (motionAllowed || current == .tableSlouch || current == .sleepPreview || current == .sleepChainPreview) ? plan.artwork : .standing)
        }
        let t = max(0, now - baseStarted)
        // Work metadata stays in the status card, independent of finite character actions.
        if ["working", "idle", "round_ended"].contains(base) {
            return PetPresentation(node: base == "working" ? "work_standing" : "idle_relaxed",
                                   frame: motionAllowed ? Int(t * 20) % 140 : 0,
                                   caption: "", wantsAnimation: true)
        }
        return PetPresentation(node: base, frame: 0, caption: "", wantsAnimation: false)
    }
}

struct PetPresentation {
    let node: String
    let frame: Int
    let caption: String
    let wantsAnimation: Bool
    var usesAnnoyedArt: Bool = false
    var artwork: PetArtwork = .standing
}
