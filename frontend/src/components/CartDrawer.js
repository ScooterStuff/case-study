import React, { useState } from "react";
import { useCart } from "../context/CartContext";

export default function CartDrawer() {
  const { items, setQty, clear, subtotal, open, setOpen } = useCart();
  const [toast, setToast] = useState(false);
  if (!open) return null;
  return (
    <div className="drawer-overlay" onClick={() => setOpen(false)}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()} aria-label="Shopping cart">
        <div className="drawer-head">
          <strong>Your cart</strong>
          <button className="btn btn-link" onClick={() => setOpen(false)} aria-label="Close cart">✕</button>
        </div>
        {items.length === 0 && <p className="muted">Cart is empty — ask me to find a part!</p>}
        {items.map((i) => (
          <div className="cart-line" key={i.ps_number}>
            {i.image_url && <img src={i.image_url} alt="" width="44" height="44" />}
            <div className="cart-line-body">
              <div className="small">{i.title}</div>
              <div className="muted tiny mono">{i.ps_number}</div>
            </div>
            <div className="qty">
              <button onClick={() => setQty(i.ps_number, i.qty - 1)} aria-label="Decrease quantity">−</button>
              <span>{i.qty}</span>
              <button onClick={() => setQty(i.ps_number, i.qty + 1)} aria-label="Increase quantity">+</button>
            </div>
            <div className="price small">${((i.price || 0) * i.qty).toFixed(2)}</div>
          </div>
        ))}
        {items.length > 0 && (
          <>
            <div className="cart-subtotal"><span>Subtotal</span><strong>${subtotal.toFixed(2)}</strong></div>
            <button className="btn btn-teal wide" onClick={() => { setToast(true); setTimeout(() => setToast(false), 3500); }}>
              Checkout
            </button>
            <button className="btn btn-link" onClick={clear}>Clear cart</button>
          </>
        )}
        {toast && <div className="toast" role="status">Demo checkout — this is where the real PartSelect flow takes over.</div>}
      </aside>
    </div>
  );
}
