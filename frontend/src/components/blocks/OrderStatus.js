import React from "react";

const STEPS = ["processing", "shipped", "in transit", "delivered"];

export default function OrderStatus({ block }) {
  const idx = STEPS.indexOf(block.status);
  return (
    <div className="card order-status">
      <div className="block-title">Order {block.order_id}</div>
      <div className="timeline">
        {STEPS.map((s, i) => (
          <div key={s} className={`step ${i <= idx ? "done" : ""}`}>
            <span className="dot" aria-hidden="true" />
            <span className="small">{s}</span>
          </div>
        ))}
      </div>
      {block.eta && <div className="small">Arriving around {block.eta} via {block.carrier}</div>}
      <div className="muted tiny">Demo data — order support is mocked in this case study.</div>
    </div>
  );
}
