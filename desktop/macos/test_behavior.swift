import Foundation

var checks = [String]()
func check(_ name: String, _ body: () -> Bool) {
    guard body() else { fputs("FAILED: \(name)\n",stderr); exit(1) }
    checks.append(name)
}
func working() -> PetBehavior {
    let model = PetBehavior(now:0)
    model.setBase("working",now:0)
    return model
}

let a = working()
a.click(now:1)
check("click interrupts working with an immediate response") { a.presentation(now:1.1).node == "react_notice" }
a.setBase("needs_input",now:1.2)
check("work changes during a reaction do not erase the reaction") { a.presentation(now:1.3).node == "react_notice" }
check("reaction returns to the latest waiting base") { a.presentation(now:1.6).node == "needs_input" }

let b = working()
b.click(now:0); b.click(now:0.1)
check("double click escalates to poke") { b.presentation(now:0.11).node == "react_poke" }
b.click(now:0.2); b.click(now:0.3)
check("four rapid clicks escalate once") { b.presentation(now:0.31).node == "react_annoyed" }
check("annoyed selects authored art for the full reaction hold") { b.presentation(now:0.31).usesAnnoyedArt && b.presentation(now:1.49).usesAnnoyedArt }
check("reduced motion suppresses annoyed art but keeps its caption") { let p=b.presentation(now:1.49,motionAllowed:false); return !p.usesAnnoyedArt && p.frame == 0 && p.caption == "让我吃完嘛" }
for t in [0.4,0.5,0.6,1.0,1.4] { b.click(now:t) }
check("click spam does not extend or queue locked reactions") { b.presentation(now:1.6).node == "work_standing" }
check("annoyed art is cleared on return to work") { !b.presentation(now:1.6).usesAnnoyedArt }
b.click(now:2)
check("annoyed reaction has a cooldown") { b.presentation(now:2.1).node == "work_standing" }
b.click(now:3.6)
check("clicks recover after cooldown") { b.presentation(now:3.61).node == "react_notice" }

let c = working()
c.feed(now:0)
c.beginDrag(now:0.2)
check("physical drag immediately owns the body") { c.presentation(now:0.3).node == "drag_float" && c.presentation(now:0.3).frame == 0 }
c.setBase("needs_input",now:0.4)
c.endDrag(now:0.5); c.click(now:0.6)
check("landing is not replaced by a queued click") { c.presentation(now:0.7).node == "drag_land" }
check("drag release returns to latest work state") { c.presentation(now:0.9).node == "needs_input" }
c.endDrag(now:1)
check("repeated release cannot replay landing") { c.presentation(now:1.1).node == "needs_input" }

let d = working()
d.click(now:0); d.setBase("failed",now:0.1); d.feed(now:0.2); d.click(now:0.3)
check("failure preempts and suppresses reactions") { d.presentation(now:0.4).node == "failed" }
d.beginDrag(now:0.5); d.endDrag(now:0.6)
check("failure remains visible during pointer relocation") { d.presentation(now:0.7).node == "failed" }

let e = working()
e.setBase("working",now:0.7)
check("same base metadata updates do not reset phase") { e.presentation(now:0.8).frame == 16 }
e.feed(now:1); e.feed(now:2); e.setBase("idle",now:3)
check("feeding runs exactly once despite repeat requests") { e.presentation(now:4.9).node == "eat_onigiri" && e.presentation(now:5.1).node == "idle_relaxed" }

let f = PetBehavior(now:0)
check("unobserved work never looks like observed idle") { f.presentation(now:100).node == "disconnected" }
f.setBase("unknown",now:101); f.click(now:102)
check("reduced motion preserves feedback without image motion") { let p=f.presentation(now:102.2,motionAllowed:false); return p.frame == 0 && p.caption == "嗯？" }
check("reaction preserves unknown coverage on return") { f.presentation(now:103).node == "unknown" }

let g = PetBehavior(now:0)
g.setBase("working",now:0)
check("working uses standing without changing observed base") { g.presentation(now:19.9).node == "work_standing" && g.base == "working" }
check("long working periods never start an automatic meal") { g.presentation(now:200).artwork == .standing && g.action == nil }
g.setBase("needs_input",now:201)
check("waiting remains standing and never triggers autonomous eating") { let p=g.presentation(now:400); return p.node == "needs_input" && p.artwork == .standing && !p.wantsAnimation }

let h = working(); h.click(now:1); h.cancelTransient(now:1.1)
check("pausing cancels reactions without a deferred queue") { h.presentation(now:1.2).node == "work_standing" }
let i = working(); i.beginDrag(now:0); i.endDrag(now:0.1); i.click(now:0.2); i.click(now:0.41)
check("clicks discarded during landing do not count toward the next burst") { i.presentation(now:0.42).node == "react_notice" }
let j = working(); for t in [0.0,0.1,0.2,0.3] { j.click(now:t) }; j.setBase("failed",now:0.4)
check("failure immediately clears annoyed art") { !j.presentation(now:0.4).usesAnnoyedArt }
let idle = PetBehavior(now:0); idle.setBase("idle",now:0)
check("approved idle sequence uses original 20 fps frame indices") {
    [0.0,4.75,4.8,4.85,4.95,5.0,5.05,6.95,7.0].map { idle.presentation(now:$0).frame } == [0,95,96,97,99,100,101,139,0]
}
check("standing click uses only the approved eye frames") {
    idle.click(now:8)
    return idle.presentation(now:8.1).artwork == .standing && idle.presentation(now:8.1).frame >= 96
}
let meal = PetBehavior(now:0); meal.setBase("idle",now:0); meal.feed(now:1)
check("manual feeding selects eating with no work-state mutation") { meal.presentation(now:2).artwork == .eating && meal.base == "idle" }
meal.setBase("unknown",now:3)
check("feeding returns to standing with latest unknown state") { let p=meal.presentation(now:5.1); return p.node == "unknown" && p.artwork == .standing }
let failMeal = PetBehavior(now:0); failMeal.feed(now:1); failMeal.setBase("failed",now:2)
check("failure interrupts feeding to a static standing pose") { let p=failMeal.presentation(now:2.1); return p.node == "failed" && p.artwork == .standing && !p.wantsAnimation }
let pausedMeal = PetBehavior(now:0); pausedMeal.feed(now:1)
check("reduced feeding keeps standing and text only") { let p=pausedMeal.presentation(now:2,motionAllowed:false); return p.artwork == .standing && p.frame == 0 && !p.caption.isEmpty }
pausedMeal.cancelTransient(now:2)
check("pause cancels meal without replaying it later") { pausedMeal.presentation(now:100).artwork == .standing && pausedMeal.action == nil }
let dragIdle = PetBehavior(now:0); dragIdle.setBase("idle",now:0); dragIdle.beginDrag(now:1)
check("standing drag holds artwork without a made-up flight frame") { let p=dragIdle.presentation(now:1.1); return p.artwork == .standing && p.frame == 0 }
dragIdle.setBase("working",now:1.2); dragIdle.endDrag(now:1.3)
check("standing landing resolves the latest working state") { let p=dragIdle.presentation(now:1.7); return p.artwork == .standing && p.node == "work_standing" }
// Deterministic clock/random injection stays inside isolated model tests.
func quiet() -> PetBehavior {
    let m = PetBehavior(now:0,randomUnit:{0}); m.setBase("idle",now:0); return m
}
let auto = quiet()
check("observed idle must remain quiet for 60 seconds") { auto.presentation(now:59.99).artwork == .standing }
check("eligible attempt starts an eight-second meal without mutating idle") { auto.presentation(now:60).node == "idle_meal" && auto.base == "idle" }
check("automatic meal plays two exact 40-frame cycles") {
    [60.0,63.99,64.0,67.99].map { auto.presentation(now:$0).frame } == [0,39,0,39]
}
check("eight-second deadline returns directly to open-eye standing") { let p=auto.presentation(now:68); return p.artwork == .standing && p.frame == 0 && auto.action == nil }
check("meal completion enforces at least 180 seconds of cooldown") { auto.presentation(now:247.99).artwork == .standing && auto.presentation(now:248).node == "idle_meal" }
for state in ["working","needs_input","failed","round_ended","unknown","disconnected"] {
    let m=quiet(); _=m.presentation(now:60); m.setBase(state,now:61)
    check("new \(state) state preempts automatic meal and never schedules one") {
        m.presentation(now:61).artwork == .standing && m.presentation(now:1000).artwork == .standing && m.base == state
    }
}
let interrupted=quiet(); _=interrupted.presentation(now:60); interrupted.click(now:61)
check("click preempts automatic meal") { interrupted.presentation(now:61).node == "react_notice" }
check("interrupted meal also gets the full cooldown") { interrupted.presentation(now:62).artwork == .standing && interrupted.presentation(now:240.9).artwork == .standing && interrupted.presentation(now:241).node == "idle_meal" }
let dragged=quiet(); _=dragged.presentation(now:60); dragged.beginDrag(now:61)
check("drag preempts meal without scheduling while held") { dragged.presentation(now:1000).node == "drag_float" }
dragged.endDrag(now:1000); _=dragged.presentation(now:1000.4)
check("release requires a fresh quiet interval") { dragged.presentation(now:1060).artwork == .standing }
for gate in [false,true] {
    let m=quiet(); _=m.presentation(now:60)
    let held=m.presentation(now:61,motionAllowed:gate,mealsAllowed:!gate)
    check("motion or invalid-assets gate cancels autonomous meal") { held.artwork == .standing && m.action == nil }
    _=m.presentation(now:1000,motionAllowed:gate,mealsAllowed:!gate)
    check("resume never catches up missed meal attempts") { m.presentation(now:1001).artwork == .standing && m.presentation(now:1060).artwork == .standing && m.presentation(now:1061).node == "idle_meal" }
}
let paused=quiet(); _=paused.presentation(now:60); paused.cancelTransient(now:61)
_=paused.presentation(now:61,motionAllowed:false)
check("pause cancels meal throughout a long sleep") { paused.presentation(now:10000,motionAllowed:false).artwork == .standing }
check("wake starts a fresh quiet interval") { paused.presentation(now:10001).artwork == .standing && paused.presentation(now:10060.99).artwork == .standing }
let manual=quiet(); manual.feed(now:1); _=manual.presentation(now:5)
check("manual meal keeps four-second duration and delays autonomy") { manual.action == nil && manual.presentation(now:184.99).artwork == .standing && manual.presentation(now:185).node == "idle_meal" }
let replace=quiet(); _=replace.presentation(now:60); replace.feed(now:61)
check("explicit feeding replaces automatic meal once") { replace.presentation(now:61).node == "eat_onigiri" && replace.presentation(now:65).artwork == .standing }
var draws=0
let skip=PetBehavior(now:0,randomUnit:{draws += 1; return 0.5}); skip.setBase("idle",now:0)
check("most random attempts do nothing") { skip.presentation(now:60).artwork == .standing && draws == 2 }
_=skip.presentation(now:97.49)
check("rejected attempts wait the selected 30-45 second interval") { draws == 2 }
_=skip.presentation(now:97.5)
check("one retry draws one interval and one decision") { draws == 4 && skip.action == nil }
_=skip.presentation(now:100000)
check("delayed ticks never replay a backlog of attempts") { draws == 6 && skip.action == nil }
let metadata=quiet(); metadata.setBase("idle",now:59)
check("same-state metadata updates preserve the idle clock") { metadata.presentation(now:60).node == "idle_meal" }
let nearClick=quiet(); nearClick.click(now:59); _=nearClick.presentation(now:60)
check("late user interaction restarts the quiet interval") { nearClick.presentation(now:119.9).artwork == .standing && nearClick.presentation(now:120).node == "idle_meal" }

// --- Observation trace: records what happened, never decides what happens. ---
final class Trace {
    var entries = [(kind: String, detail: [String: String])]()
    func attach(_ model: PetBehavior) { model.onTrace = { [weak self] k, d in self?.entries.append((k,d)) } }
    func kinds() -> [String] { entries.map(\.kind) }
    func first(_ kind: String) -> [String: String]? { entries.first { $0.kind == kind }?.detail }
    func all(_ kind: String) -> [[String: String]] { entries.filter { $0.kind == kind }.map(\.detail) }
}

let traceBase = PetBehavior(now:0)
let baseTrace = Trace(); baseTrace.attach(traceBase)
traceBase.setBase("working",now:0)
check("base transitions are recorded with both sides") { baseTrace.first("base")?["from"] == "disconnected" && baseTrace.first("base")?["to"] == "working" }
traceBase.setBase("working",now:1)
check("unchanged state records no transition") { baseTrace.all("base").count == 1 }

let traceFeed = PetBehavior(now:0); traceFeed.setBase("working",now:0)
let feedTrace = Trace(); feedTrace.attach(traceFeed)
traceFeed.feed(now:1)
check("action start records the action and its duration") { feedTrace.first("action_start")?["action"] == "eat_onigiri" && feedTrace.first("action_start")?["duration"] == "4.000" }
_=traceFeed.presentation(now:5)
check("completed action records the completion reason") { feedTrace.first("action_end")?["reason"] == "completed" && feedTrace.first("action_end")?["action"] == "eat_onigiri" }
check("a finished meal reports its own 180 second block") { traceFeed.mealEta(now:5) == 180 }

let tracePreempt = PetBehavior(now:0); tracePreempt.setBase("working",now:0)
let preemptTrace = Trace(); preemptTrace.attach(tracePreempt)
tracePreempt.feed(now:0); tracePreempt.click(now:0.5)
check("preemption names the action that took over") { preemptTrace.first("action_end")?["reason"] == "preempted_by_react_notice" }
tracePreempt.beginDrag(now:1)
check("drag records its own takeover reason") { preemptTrace.all("action_end").last?["reason"] == "drag" }

let traceIdle = PetBehavior(now:0,randomUnit:{0}); traceIdle.setBase("idle",now:0)
let idleTrace = Trace(); idleTrace.attach(traceIdle)
_=traceIdle.presentation(now:60)
check("a hit attempt records the roll and the retry interval") {
    let attempt = idleTrace.first("meal_attempt")
    return attempt?["hit"] == "true" && attempt?["roll"] == "0.000" && attempt?["retry_in"] == "30.000"
}
check("an automatic meal is recorded as a started action") { idleTrace.first("action_start")?["action"] == "idle_meal" && idleTrace.first("action_start")?["base"] == "idle" }
_=traceIdle.presentation(now:68)
check("the automatic meal end is recorded once with its elapsed time") {
    let ends = idleTrace.all("action_end")
    return ends.count == 1 && ends[0]["action"] == "idle_meal" && ends[0]["elapsed"] == "8.000"
}

let traceMiss = PetBehavior(now:0,randomUnit:{0.5}); traceMiss.setBase("idle",now:0)
let missTrace = Trace(); missTrace.attach(traceMiss)
_=traceMiss.presentation(now:60)
check("a missed attempt is recorded without starting an action") {
    missTrace.first("meal_attempt")?["hit"] == "false" && missTrace.all("action_start").isEmpty
}
_=traceMiss.presentation(now:97.49)
check("a pending retry interval records nothing") { missTrace.all("meal_attempt").count == 1 }
_=traceMiss.presentation(now:97.5); _=traceMiss.presentation(now:100000)
check("recorded attempts match the real attempt count with no backlog") { missTrace.all("meal_attempt").count == 3 }

let traceGate = PetBehavior(now:0); traceGate.setBase("idle",now:0)
let gateTrace = Trace(); gateTrace.attach(traceGate)
_=traceGate.presentation(now:10,mealsAllowed:false)
check("a suppressing gate is recorded with the responsible input") {
    gateTrace.first("autonomy")?["enabled"] == "false" && gateTrace.first("autonomy")?["meals"] == "false"
}
check("suppression is readable without waiting for a pose") { traceGate.autonomySuppressed }
_=traceGate.presentation(now:11)
check("a released gate is recorded and restarts the quiet interval") {
    gateTrace.all("autonomy").last?["enabled"] == "true" && traceGate.mealEta(now:11) == 60 && !traceGate.autonomySuppressed
}

// The sink must be inert: identical inputs must produce an identical pose sequence.
func poses(traced: Bool) -> [String] {
    var draws = 0.0
    let model = PetBehavior(now:0,randomUnit:{ draws += 0.13; return draws.truncatingRemainder(dividingBy: 1) })
    if traced { let sink = Trace(); sink.attach(model) }
    model.setBase("idle",now:0)
    var out = [String]()
    var t = 0.0
    while t < 600 {
        if abs(t - 200) < 0.001 { model.click(now:t) }
        if abs(t - 300) < 0.001 { model.feed(now:t) }
        out.append(model.presentation(now:t).node)
        t += 0.5
    }
    return out
}
check("recording never changes the chosen poses") { poses(traced:false) == poses(traced:true) }
check("a nil sink stays safe across a full lifecycle") { poses(traced:false).contains("idle_meal") }

// --- Declarative action registry: pool, chain, two-level rest and held loops. ---
// A constant 0.2 draw lands in the second pool range, so the meal chains into the pause.
func chained() -> PetBehavior {
    let m = PetBehavior(now:0,randomUnit:{0.2}); m.setBase("idle",now:0); return m
}
check("the split pool keeps the approved 25 percent meal probability") {
    abs(PoolEntry.production.filter { $0.action == .idleMeal }.map(\.weight).reduce(0,+) - 0.25) < 0.000000001
}
let chain = chained()
check("the weighted pool still starts the approved eight-second meal") {
    chain.presentation(now:60).node == "idle_meal" && chain.presentation(now:67.99).frame == 39
}
check("a completed meal continues into the chewing pause without flashing to standing") {
    let p = chain.presentation(now:68)
    return p.node == "pause_chew" && p.artwork == .eating && p.frame == 4
}
check("the chewing pause plays its declared program") {
    [68.0,68.85,69.45,69.65].map { chain.presentation(now:$0).frame } == [4,27,31,0]
}
check("the chain ends on the approved open-eye standing pose") {
    let p = chain.presentation(now:70)
    return p.node == "idle_relaxed" && p.artwork == .standing && chain.action == nil
}
check("the full episode, not just the meal, earns the 180 second rest") {
    chain.mealEta(now:70) == 180 && chain.presentation(now:249.99).artwork == .standing &&
    chain.presentation(now:250).node == "idle_meal"
}
var chainDraws = 0
let counted = PetBehavior(now:0,randomUnit:{ chainDraws += 1; return 0.2 }); counted.setBase("idle",now:0)
for t in [60.0,68.0,70.0] { _=counted.presentation(now:t) }
check("a chained continuation costs no extra random draw") { chainDraws == 2 }

let cut = chained(); _=cut.presentation(now:60); cut.click(now:61)
check("an interrupted meal never plays its continuation") {
    cut.presentation(now:61.1).node == "react_notice" && cut.presentation(now:62).node == "idle_relaxed"
}
let left = chained(); _=left.presentation(now:60); _=left.presentation(now:68)
left.setBase("working",now:68.5)
check("leaving idle cancels the continuation as well as the meal") {
    left.presentation(now:68.6).node == "work_standing" && left.action == nil
}
let gated = chained(); _=gated.presentation(now:60); _=gated.presentation(now:68)
_=gated.presentation(now:68.5,motionAllowed:false)
check("a gate cancels the continuation and never resumes it") {
    gated.action == nil && gated.presentation(now:10000).artwork == .standing
}

// An injected registry: the arbitration loop must not know any action by name.
let heldSpecs = PetAction.production.merging([
    .pauseChew: ActionSpec(duration:nil,maxHold:20,priority:28,artwork:.eating,
                           cooldown:300,globalRest:20,frames:.loop(fps:10,count:40))
]) { _, replacement in replacement }
let heldPool = [PoolEntry(action:.pauseChew,weight:1),PoolEntry(action:.idleMeal,weight:1)]
let held = PetBehavior(now:0,randomUnit:{0},specs:heldSpecs,pool:heldPool)
held.setBase("idle",now:0)
check("a held action keeps playing with no fixed duration") {
    held.presentation(now:60).node == "pause_chew" && held.presentation(now:79.99).node == "pause_chew"
}
check("a held action stops at its declared maximum hold") {
    held.presentation(now:80).node == "idle_relaxed" && held.action == nil
}
check("a short global rest does not impose the long per-action cooldown") { held.mealEta(now:80) == 60 }
check("one resting action does not silence the rest of the pool") {
    held.presentation(now:140).node == "idle_meal"
}
let chewProgram = (0..<20).map { PetAction.production[.pauseChew]!.frames.index(at: Double($0) / 10) }
check("the chewing pause retimes shipped drawings and never the fully closed eye") {
    chewProgram == [4,4,5,5,6,6,7,7,27,27,27,27,27,27,31,31,0,0,0,0] &&
    chewProgram.allSatisfy { $0 >= 0 && $0 < 40 } && !chewProgram.contains(29)
}



let restPreview = PetBehavior(now:0)
restPreview.setBase("idle",now:0); restPreview.previewSlouch(now:1)
check("manual slouch selects reviewed clip") { restPreview.presentation(now:1).artwork == .slouch }
check("slouch uses expected blink frame") { restPreview.presentation(now:7.4).frame == 128 }
check("slouch reduced motion holds same pose") { let p=restPreview.presentation(now:7.5,motionAllowed:false); return p.artwork == .slouch && p.frame == 0 }
check("slouch ends at fourteen seconds") { restPreview.presentation(now:15).artwork == .standing }
restPreview.previewSlouch(now:16); restPreview.feed(now:17)
check("feeding preempts slouch") { restPreview.presentation(now:17).artwork == .eating }
restPreview.previewSlouch(now:17.1)
check("slouch cannot preempt feeding") { restPreview.presentation(now:17.2).artwork == .eating }
let failedRest=PetBehavior(now:0); failedRest.setBase("failed",now:0);failedRest.previewSlouch(now:1)
check("slouch respects failure priority") { failedRest.presentation(now:2).node == "failed" }
let draggedRest=PetBehavior(now:0);draggedRest.previewSlouch(now:1);draggedRest.beginDrag(now:2)
check("drag interrupts slouch") { draggedRest.presentation(now:2).node == "drag_float" }
check("slouch does not change approved autonomous weights") { PoolEntry.production.count == 3 && abs(PoolEntry.production.filter{$0.action == .idleMeal}.reduce(0){$0+$1.weight}-0.25)<0.0000001 }
print("Slouch integration checks passed; total \(checks.count)")

func autoRest() -> PetBehavior {
    let model=PetBehavior(now:0,randomUnit:{0.27}); model.setBase("idle",now:0); return model
}
let quietRest=autoRest()
check("slouch requires three minutes of uninterrupted quiet") { quietRest.presentation(now:179).artwork == .standing }
check("slouch enters on eligible low probability draw") { quietRest.presentation(now:214).artwork == .slouch }
check("automatic slouch plays two loops then returns") { quietRest.presentation(now:227.4).frame == 128 && quietRest.presentation(now:228).artwork == .standing }
check("slouch cooldown blocks an otherwise eligible draw") { quietRest.presentation(now:1127).artwork == .standing }
check("slouch becomes eligible after full cooldown and next tick") { quietRest.presentation(now:1162).artwork == .slouch }
for state in ["working","needs_input","failed","round_ended","unknown","disconnected"] {
    let m=autoRest(); _=m.presentation(now:180); m.setBase(state,now:181)
    check("automatic slouch is preempted by " + state) { m.action == nil && m.presentation(now:182).artwork == .standing }
}
for gate in ["motion", "assets", "slouch"] {
    let m=autoRest(); _=m.presentation(now:180)
    let p=m.presentation(now:181,motionAllowed:gate != "motion",mealsAllowed:gate != "assets",slouchAllowed:gate != "slouch")
    check("automatic slouch cancels on " + gate) { p.artwork == .standing && m.action == nil }
    check("reenabling " + gate + " never catches up") { m.presentation(now:10000).artwork == .standing }
}
let missing=autoRest()
check("missing optional package cannot select slouch") { missing.presentation(now:180,slouchAllowed:false).artwork == .standing }
let fed=autoRest(); _=fed.presentation(now:180); fed.feed(now:181)
check("feeding preempts automatic slouch") { fed.presentation(now:181).artwork == .eating }
let dragRest=autoRest(); _=dragRest.presentation(now:180); dragRest.beginDrag(now:181)
check("drag preempts automatic slouch") { dragRest.presentation(now:181).node == "drag_float" }
let pausedRest=autoRest(); _=pausedRest.presentation(now:180); pausedRest.cancelTransient(now:181)
check("pause discards automatic slouch") { pausedRest.presentation(now:10000,motionAllowed:false).artwork == .standing && pausedRest.action == nil }
let interacted=autoRest(); interacted.click(now:170); _=interacted.presentation(now:171)
check("interaction resets slouch quiet period") { interacted.presentation(now:340).artwork == .standing }
check("slouch leaves seventy percent no-op probability") { abs(PoolEntry.production.reduce(0){$0+$1.weight}-0.30)<0.0000001 }
let sleepy=PetBehavior(now:0); sleepy.setBase("idle",now:0); sleepy.previewSleep(now:1)
check("sleep preview holds selected still") { sleepy.presentation(now:20).artwork == .sleeping && sleepy.presentation(now:20).frame == 0 }
check("reduced sleep preview holds the same drawing") { sleepy.presentation(now:21,motionAllowed:false).artwork == .sleeping }
check("sleep preview expires at sixty seconds") { sleepy.presentation(now:61).artwork == .standing }
for trigger in ["feed","drag","failed","pause","click"] {
    let m=PetBehavior(now:0);m.setBase("idle",now:0);m.previewSleep(now:1)
    switch trigger {
    case "feed":m.feed(now:2)
    case "drag":m.beginDrag(now:2)
    case "failed":m.setBase("failed",now:2)
    case "pause":m.cancelTransient(now:2)
    default:m.click(now:2)
    }
    check("sleep preview yields to " + trigger) { m.action != .sleepPreview && m.presentation(now:2).artwork != .sleeping }
}
let mealFirst=PetBehavior(now:0);mealFirst.feed(now:1);mealFirst.previewSleep(now:2)
check("sleep preview cannot interrupt feeding") { mealFirst.action == .feed }
check("static sleep preview never enters autonomous pool") { !PoolEntry.production.contains{$0.action == .sleepPreview} }
let shortChain=PetBehavior(now:0);shortChain.setBase("idle",now:0);shortChain.previewSleepChain(now:1)
check("sleep preview phases match compressed timeline") {
    [(1.0,1),(2.0,2),(3.0,3),(4.0,0),(5.0,3),(5.6,0),(10.0,3),(11.0,1)].allSatisfy { shortChain.presentation(now:$0.0).frame == $0.1 }
}
check("sleep preview returns after twelve seconds") { shortChain.presentation(now:13).artwork == .standing }
for trigger in ["feed","drag","failed","pause","click"] {
    let m=PetBehavior(now:0);m.setBase("idle",now:0);m.previewSleepChain(now:1)
    switch trigger {
    case "feed":m.feed(now:2)
    case "drag":m.beginDrag(now:2)
    case "failed":m.setBase("failed",now:2)
    case "pause":m.cancelTransient(now:2)
    default:m.click(now:2)
    }
    check("short sleep chain yields immediately to " + trigger) { m.action != .sleepChainPreview && m.presentation(now:2).artwork != .sleeping }
}
let reduceChain=PetBehavior(now:0);reduceChain.previewSleepChain(now:1)
check("reduced chain uses approved sleep still") { let p=reduceChain.presentation(now:2,motionAllowed:false);return p.artwork == .sleeping && p.frame == 0 }
check("sleep chain is never an autonomous outcome") { !PoolEntry.production.contains{$0.action == .sleepChainPreview} }
print(String(data:try JSONSerialization.data(withJSONObject:["status":"pass","count":checks.count,"checks":checks],options:[.prettyPrinted,.sortedKeys]),encoding:.utf8)!)
