import React, { useEffect, useRef, useState } from "react";
import { marked } from "marked";
import { getSessionId, newSession, streamChat } from "../lib/api";
import ProductCard, { ProductList } from "./blocks/ProductCard";
import CompatResult from "./blocks/CompatResult";
import Diagnosis from "./blocks/Diagnosis";
import InstallGuide from "./blocks/InstallGuide";
import ModelHelpModal from "./ModelHelpModal";
import PhotoUploader from "./PhotoUploader";

// The exact spec queries are seeded as suggestion chips on purpose.
const SUGGESTIONS = [
  "How can I install part number PS11752778?",
  "Is part PS11752778 compatible with my WDT780SAEM1?",
  "My Whirlpool fridge ice maker isn't working",
  "Find a replacement wheel for my dishwasher's bottom rack",
];

const GREETING =
  "Hi! I'm the PartSelect assistant for **refrigerator and dishwasher parts**. " +
  "Tell me a symptom, a part number, or your model number and I'll help you " +
  "diagnose it, find the right part, check it fits, and get it installed.";

function Block({ block, onSend }) {
  switch (block.type) {
    case "product_list": return <ProductList products={block.products} onSend={onSend} />;
    case "product_card": return <ProductCard product={block.product} description={block.description}
                                             symptoms={block.symptoms} onSend={onSend} />;
    case "compat_result": return <CompatResult block={block} onSend={onSend} />;
    case "diagnosis": return <Diagnosis block={block} onSend={onSend} />;
    case "install_guide": return <InstallGuide block={block} />;
    default: return null;
  }
}

function Prose({ text, streaming }) {
  // NOTE: agent output is markdown from our own backend; marked + this app's
  // CSP is acceptable for the case study (template used the same approach).
  return (
    <div className="prose" dangerouslySetInnerHTML={{ __html: marked.parse(text || "") }}
         data-streaming={streaming || undefined} />
  );
}

export default function ChatWindow() {
  const [sessionId, setSessionId] = useState(getSessionId);
  const [messages, setMessages] = useState([]);   // {role, text, blocks[], pills[], error}
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const endRef = useRef(null);
  const composerRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  const patchLast = (fn) =>
    setMessages((prev) => {
      const next = [...prev];
      next[next.length - 1] = fn(next[next.length - 1]);
      return next;
    });

  const send = async (text) => {
    const message = (text ?? input).trim();
    if (!message || busy) return;
    setInput("");
    setBusy(true);
    setMessages((prev) => [...prev,
      { role: "user", text: message },
      { role: "assistant", text: "", blocks: [], pills: [] }]);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await streamChat(sessionId, message, {
        token: (d) => patchLast((m) => ({ ...m, text: m.text + d.delta })),
        tool_start: (d) => patchLast((m) => ({ ...m, pills: [...m.pills, d] })),
        tool_end: (d) => patchLast((m) => ({ ...m, pills: m.pills.filter((p) => p.name !== d.name) })),
        ui_block: (d) => patchLast((m) => ({ ...m, blocks: [...m.blocks, d] })),
        done: () => patchLast((m) => ({ ...m, pills: [] })),
      }, controller.signal);
    } catch (err) {
      if (err.name !== "AbortError") {
        patchLast((m) => ({ ...m, error: true,
          text: m.text || "I couldn't reach the parts service. Is the backend running?" }));
      }
    } finally {
      setBusy(false);
      abortRef.current = null;
      composerRef.current?.focus();
    }
  };

  const stop = () => {
    abortRef.current?.abort();
  };

  const reset = () => {
    stop();
    setSessionId(newSession());
    setMessages([]);
  };

  const handleDetectedModel = (model) => {
    if (!model) return;
    // Smart prefill: if the user has already discussed a part, propose a
    // compatibility check; otherwise propose a parts search for the model.
    const conv = messages.map((m) => m.text).join(" ");
    const ps = (conv.match(/PS\d{5,9}/i) || [])[0];
    const draft = ps
      ? `Is part ${ps.toUpperCase()} compatible with my ${model}?`
      : `My model number is ${model} — what parts do you stock for it?`;
    setInput(draft);
    composerRef.current?.focus();
  };

  return (
    <div className="chat">
      <div className="messages" aria-live="polite">
        <div className="msg assistant">
          <Prose text={GREETING} />
          {messages.length === 0 && (
            <>
              <div className="chip-row suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="chip chip-btn" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
              <button className="btn btn-link small" onClick={() => setHelpOpen(true)}>
                Where do I find my model number?
              </button>
            </>
          )}
        </div>
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}${m.error ? " error" : ""}`}>
            {m.pills?.length > 0 && (
              <div className="pills">
                {m.pills.map((p) => (
                  <span key={p.name} className="pill"><span className="spinner" aria-hidden="true" />{p.label}</span>
                ))}
              </div>
            )}
            {m.blocks?.map((b, j) => <Block key={j} block={b} onSend={send} />)}
            {m.role === "assistant"
              ? <Prose text={m.text} streaming={busy && i === messages.length - 1} />
              : <div className="user-text">{m.text}</div>}
            {m.error && (
              <button className="btn btn-outline small" onClick={() => send(messages[i - 1]?.text)}>
                Retry
              </button>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <form className="composer" onSubmit={(e) => { e.preventDefault(); send(); }}>
        <textarea
          ref={composerRef}
          value={input}
          rows={1}
          placeholder="Describe the problem, or paste a part / model number…"
          aria-label="Message"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
          }}
        />
        <PhotoUploader disabled={busy} onModelDetected={handleDetectedModel} />
        {busy
          ? <button type="button" className="btn btn-outline" onClick={stop}>Stop</button>
          : <button type="submit" className="btn btn-teal" disabled={!input.trim()}>Send</button>}
        <button type="button" className="btn btn-link" onClick={reset} title="Start a new conversation">
          New chat
        </button>
      </form>
      {helpOpen && <ModelHelpModal onClose={() => setHelpOpen(false)} />}
    </div>
  );
}
