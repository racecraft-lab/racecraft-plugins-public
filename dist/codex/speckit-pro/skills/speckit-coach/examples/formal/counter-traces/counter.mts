import { argv, stdout } from "node:process";

type Snapshot = { action: "increment" | "hold"; count: bigint };
type State = { "#meta": { index: number; action?: Snapshot["action"] }; count: { "#bigint": string } };

class Counter {
  private count: bigint;
  private readonly limit: bigint;

  constructor(start: bigint, limit: bigint) {
    if (start > limit) throw new Error("start must not exceed limit");
    this.count = start;
    this.limit = limit;
  }

  advance(): Snapshot {
    let action: Snapshot["action"] = "hold";
    if (this.count < this.limit) {
      this.count += 1n;
      action = "increment";
    }
    return { action, count: this.count };
  }
}

const [startText = "0", limitText = "2"] = argv.slice(2);
if (![startText, limitText].every(text => /^-?(0|[1-9][0-9]*)$/.test(text))) {
  throw new Error("counter arguments must be decimal integers");
}
const start = BigInt(startText);
const counter = new Counter(start, BigInt(limitText));
const states: State[] = [{ "#meta": { index: 0 }, count: { "#bigint": start.toString() } }];
for (let index = 1; index <= 3; index++) {
  const snapshot = counter.advance();
  states.push({ "#meta": { index, action: snapshot.action }, count: { "#bigint": snapshot.count.toString() } });
}
stdout.write(JSON.stringify({ vars: ["count"], states }) + "\n");
