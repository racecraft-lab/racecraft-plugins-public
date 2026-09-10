import Foundation

struct IntegerValue: Codable, Sendable {
    let decimal: String
    enum CodingKeys: String, CodingKey { case decimal = "#bigint" }
}

struct Metadata: Codable, Sendable {
    let index: Int
    let action: String?
}

struct State: Codable, Sendable {
    let metadata: Metadata
    let count: IntegerValue
    enum CodingKeys: String, CodingKey { case metadata = "#meta", count }
}

struct Trace: Codable { let vars: [String]; let states: [State] }

actor Counter {
    private var count: Int64
    private let limit: Int64

    init(start: Int64, limit: Int64) {
        precondition(start <= limit, "start must not exceed limit")
        self.count = start
        self.limit = limit
    }

    // Capture event and state in the same actor turn, with no intervening await.
    func advance(index: Int) -> State {
        var action = "hold"
        if count < limit {
            count += 1
            action = "increment"
        }
        return State(metadata: Metadata(index: index, action: action), count: IntegerValue(decimal: String(count)))
    }
}

enum ArgumentError: Error { case expectedStartAndLimit }

func emitCounterTrace() async throws {
        let args = Array(CommandLine.arguments.dropFirst())
        guard args.isEmpty || args.count == 2,
              let start = args.isEmpty ? Int64(0) : Int64(args[0]),
              let limit = args.isEmpty ? Int64(2) : Int64(args[1]), start <= limit else {
            throw ArgumentError.expectedStartAndLimit
        }
        let counter = Counter(start: start, limit: limit)
        var states = [State(metadata: Metadata(index: 0, action: nil), count: IntegerValue(decimal: String(start)))]
        for index in 1...3 { states.append(await counter.advance(index: index)) }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(Trace(vars: ["count"], states: states))
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([10]))
}

try await emitCounterTrace()
