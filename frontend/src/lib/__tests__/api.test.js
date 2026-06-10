import { streamChat } from "../api";

function sseResponse(chunks) {
  const encoder = new TextEncoder();
  let i = 0;
  return {
    ok: true,
    body: {
      getReader: () => ({
        read: async () =>
          i < chunks.length
            ? { done: false, value: encoder.encode(chunks[i++]) }
            : { done: true, value: undefined },
      }),
    },
  };
}

test("reassembles events split across network chunks", async () => {
  global.fetch = jest.fn().mockResolvedValue(sseResponse([
    "event: token\ndata: {\"del",          // split mid-JSON
    "ta\": \"Hel\"}\n\nevent: tok",         // split mid-event-name
    "en\ndata: {\"delta\": \"lo\"}\n\n",
    "event: done\ndata: {\"latency_ms\": 5}\n\n",
  ]));
  const tokens = [];
  let done = null;
  await streamChat("s", "hi", { token: (d) => tokens.push(d.delta), done: (d) => (done = d) });
  expect(tokens.join("")).toBe("Hello");
  expect(done.latency_ms).toBe(5);
});

test("tolerates malformed data lines and unknown events", async () => {
  global.fetch = jest.fn().mockResolvedValue(sseResponse([
    "event: mystery\ndata: {\"x\":1}\n\nevent: token\ndata: not-json\n\n",
    "event: token\ndata: {\"delta\": \"ok\"}\n\n",
  ]));
  const tokens = [];
  await streamChat("s", "hi", { token: (d) => tokens.push(d.delta) });
  expect(tokens).toEqual(["ok"]);
});

test("backend error rejects", async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 500 });
  await expect(streamChat("s", "hi", {})).rejects.toThrow("backend error (500)");
});
