import React, { useState } from "react";

function Stars({ rating }) {
  if (rating == null) return null;
  return (
    <span className="stars" aria-label={`${rating} out of 5 stars`}>
      {"★".repeat(Math.round(rating))}
      <span className="stars-off">{"★".repeat(5 - Math.round(rating))}</span>
    </span>
  );
}

export default function ProductCard({
  product,
  description,
  symptoms,
  onSend,
  compact,
}) {
  const [modelOpen, setModelOpen] = useState(false);
  const [model, setModel] = useState("");
  const p = product;
  if (!p) return null;
  const inStock = (p.availability || "").toLowerCase().includes("in stock");

  return (
    <div className={`card product-card${compact ? " compact" : ""}`}>
      {p.image_url && (
        <img
          className="product-img"
          src={p.image_url}
          alt={p.title}
          loading="lazy"
        />
      )}
      <div className="product-body">
        <div className="product-title">{p.title}</div>
        <div className="product-meta">
          <span className="mono">{p.ps_number}</span>
          {p.mpn && <span className="muted"> · Mfr # {p.mpn}</span>}
          {p.brand && <span className="muted"> · {p.brand}</span>}
        </div>
        <div className="product-row">
          {p.price != null && (
            <span className="price">${p.price.toFixed(2)}</span>
          )}
          <span className={`badge ${inStock ? "badge-green" : "badge-amber"}`}>
            {p.availability || "—"}
          </span>
          {p.install_difficulty && (
            <span className="chip">{p.install_difficulty} install</span>
          )}
          <Stars rating={p.rating} />
          {p.review_count != null && (
            <span className="muted small">({p.review_count})</span>
          )}
        </div>
        {description && <p className="product-desc">{description}</p>}
        {symptoms?.length > 0 && (
          <div className="muted small">
            Fixes: {symptoms.slice(0, 3).join(", ")}
          </div>
        )}
        <div className="product-actions">
          <button
            className="btn btn-outline"
            onClick={() => setModelOpen((v) => !v)}
          >
            Check fits my model
          </button>
          <button
            className="btn btn-outline"
            onClick={() =>
              onSend?.(`How do I install part number ${p.ps_number}?`)
            }
          >
            Install guide
          </button>
        </div>
        {modelOpen && (
          <form
            className="model-check"
            onSubmit={(e) => {
              e.preventDefault();
              if (!model.trim()) return;
              onSend?.(
                `Is part ${p.ps_number} compatible with my model ${model.trim()}?`,
              );
              setModelOpen(false);
              setModel("");
            }}
          >
            <input
              autoFocus
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="Your model number (e.g. WDT780SAEM1)"
              aria-label="Model number"
            />
            <button className="btn btn-teal" type="submit">
              Check
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export function ProductList({ products, onSend }) {
  return (
    <div className="product-list">
      {(products || []).slice(0, 4).map((p) => (
        <ProductCard key={p.ps_number} product={p} onSend={onSend} compact />
      ))}
    </div>
  );
}
