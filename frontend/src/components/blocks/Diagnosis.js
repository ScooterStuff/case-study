import React, { useState } from "react";
import { ProductList } from "./ProductCard";

const BRANDS = ["Whirlpool", "GE", "Samsung", "LG", "Other"];

export default function Diagnosis({ block, onSend }) {
  const [openRank, setOpenRank] = useState(null);
  const causes = block.causes || [];
  return (
    <div className="card diagnosis">
      <div className="block-title">Most likely causes, in order</div>
      <ol className="cause-list">
        {causes.map((c) => (
          <li key={`${c.rank}-${c.cause}`}>
            <button className="cause-toggle"
                    onClick={() => setOpenRank(openRank === c.rank ? null : c.rank)}
                    aria-expanded={openRank === c.rank}>
              <span className="cause-rank">{c.rank}</span> {c.cause}
            </button>
            {openRank === c.rank && (
              <div className="cause-detail small">
                {c.detail || "Ask me for the step-by-step check for this cause."}
              </div>
            )}
          </li>
        ))}
      </ol>
      {block.suggested_parts?.length > 0 && (
        <>
          <div className="block-subtitle">Parts that commonly fix this</div>
          <ProductList products={block.suggested_parts} onSend={onSend} />
        </>
      )}
      {block.ask_brand && (
        <div className="chip-row">
          {BRANDS.map((b) => (
            <button key={b} className="chip chip-btn" onClick={() => onSend?.(b)}>{b}</button>
          ))}
        </div>
      )}
    </div>
  );
}
