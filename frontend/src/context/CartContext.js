import React, { createContext, useContext, useEffect, useState } from "react";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => {
    try { return JSON.parse(localStorage.getItem("ps_cart") || "[]"); }
    catch { return []; }
  });
  const [open, setOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem("ps_cart", JSON.stringify(items));
  }, [items]);

  const add = (product) =>
    setItems((prev) => {
      const found = prev.find((i) => i.ps_number === product.ps_number);
      if (found) {
        return prev.map((i) =>
          i.ps_number === product.ps_number ? { ...i, qty: i.qty + 1 } : i);
      }
      return [...prev, { ...product, qty: 1 }];
    });
  const setQty = (ps, qty) =>
    setItems((prev) => qty <= 0
      ? prev.filter((i) => i.ps_number !== ps)
      : prev.map((i) => (i.ps_number === ps ? { ...i, qty } : i)));
  const clear = () => setItems([]);
  const count = items.reduce((n, i) => n + i.qty, 0);
  const subtotal = items.reduce((s, i) => s + (i.price || 0) * i.qty, 0);

  return (
    <CartContext.Provider value={{ items, add, setQty, clear, count, subtotal, open, setOpen }}>
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
