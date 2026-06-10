"""Pretty-print an SSE /chat stream (used by smoke.sh)."""

import json
import sys

event = ""
text = []
for line in sys.stdin:
    line = line.strip()
    if line.startswith("event:"):
        event = line.split(":", 1)[1].strip()
    elif line.startswith("data:") and line != "data:":
        data = json.loads(line.split(":", 1)[1])
        if event == "token":
            text.append(data["delta"])
        elif event == "tool_start":
            print(f"  [tool] {data['name']}: {data['label']}")
        elif event == "ui_block":
            print(f"  [ui_block] {data['type']}")
        elif event == "done":
            print(f"  [done] {data['latency_ms']}ms")
print()
print("".join(text))
