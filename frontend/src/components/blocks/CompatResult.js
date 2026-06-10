import React, { useState } from "react";

const VERDICTS = {
  verified_fit: { icon: "✓", cls: "ok", title: "Verified fit" },
  no_match_found: { icon: "⚠", cls: "warn", title: "Not in our verified list" },
  unknown_model: { icon: "?", cls: "warn", title: "Model not found" },
  unknown_part: { icon: "✗", cls: "bad", title: "Part not found" },
};

export default function CompatResult({ block, onSend }) {
  const [showModels, setShowModels] = useState(false);
  const v = VERDICTS[block.verdict] || VERDICTS.unknown_model;
  return (
    <div className={`card compat compat-${v.cls}`}>
      <div className="compat-head">
        <span className={`compat-icon ${v.cls}`} aria-hidden="true">{v.icon}</span>
        <div>
          <div className="compat-title">{v.title}</div>
          <div className="muted small">
            Part <span className="mono">{block.part}</span> · Model <span className="mono">{block.model}</span>
          </div>
        </div>
      </div>
      {block.verdict === "verified_fit" && (
        <p className="small">Verified against PartSelect's cross-reference — this part is
          confirmed for {block.evidence_count} model{block.evidence_count === 1 ? "" : "s"} including yours.</p>
      )}
      {block.verdict === "no_match_found" && (
        <>
          <p className="small">{block.honesty_note?.split(" - ")[0] || "Not in our verified compatibility list."} That
            doesn't necessarily mean it won't fit — our list covers {block.evidence_count} verified
            model{block.evidence_count === 1 ? "" : "s"} for this part.</p>
          <button className="btn btn-link" onClick={() => {
            setShowModels(true);
            onSend?.(`Which parts do you have verified for model ${block.model}?`);
          }} disabled={showModels}>
            Show parts verified for my model
          </button>
        </>
      )}
    </div>
  );
}
