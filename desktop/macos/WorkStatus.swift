import Foundation

struct WorkSession: Decodable {
    let provider: String
    let session: String
    let state: String
    let updated_at: Double
}
struct WorkSnapshot: Decodable {
    let schema_version: Int
    let stale_seconds: Double
    let sessions: [WorkSession]
}
struct WorkStatus: Equatable {
    var state = "disconnected"
    var active = 0
    var unknown = 0
    var providers = [String]()
    var label: String {
        switch state {
        case "working": return "工作中 · \(active) 项"
        case "needs_input": return "检测到输入或审批请求"
        case "round_ended": return "这一轮已结束"
        case "interrupted": return "已中断"
        case "failed": return "这一轮遇到错误"
        case "unknown": return "工作状态待确认"
        case "idle": return "已观察的任务暂未运行"
        default: return "尚未收到工作事件"
        }
    }
    static func load(_ path: URL, now: Double = Date().timeIntervalSince1970) -> WorkStatus {
        guard FileManager.default.fileExists(atPath: path.path) else { return WorkStatus() }
        do {
            let bytes = try Data(contentsOf: path)
            guard bytes.count <= 1024*1024 else { throw CocoaError(.fileReadTooLarge) }
            let snapshot = try JSONDecoder().decode(WorkSnapshot.self, from: bytes)
            guard snapshot.schema_version == 1, snapshot.stale_seconds == 600, snapshot.sessions.count <= 256 else {
                throw CocoaError(.fileReadCorruptFile)
            }
            let allowed = Set(["idle","working","needs_input","round_ended","interrupted","failed","closed"])
            var states = [String](), providers = Set<String>(), keys = Set<String>()
            for session in snapshot.sessions {
                guard ["codex","claude"].contains(session.provider), allowed.contains(session.state),
                      session.updated_at.isFinite, session.updated_at <= now+5,
                      keys.insert(session.provider + ":" + session.session).inserted else {
                    throw CocoaError(.fileReadCorruptFile)
                }
                providers.insert(session.provider)
                let age = max(0,now-session.updated_at)
                var state = session.state
                if ["working","needs_input"].contains(state) && age > snapshot.stale_seconds { state = "unknown" }
                if ["round_ended","interrupted","failed"].contains(state) && age > 30 { state = "idle" }
                states.append(state)
            }
            let priority = ["needs_input","failed","working","unknown","round_ended","interrupted"]
            return WorkStatus(state: priority.first(where:states.contains) ?? (states.isEmpty ? "disconnected" : "idle"),
                              active: states.filter{$0 == "working"}.count,
                              unknown: states.filter{$0 == "unknown"}.count, providers: providers.sorted())
        } catch { return WorkStatus(state:"unknown",unknown:1) }
    }
}
