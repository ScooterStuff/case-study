import React from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";
import CartDrawer from "./components/CartDrawer";
import { CartProvider, useCart } from "./context/CartContext";

function CartButton() {
  const { count, setOpen } = useCart();
  return (
    <button className="cart-btn" onClick={() => setOpen(true)} aria-label={`Open cart, ${count} items`}>
      🛒{count > 0 && <span className="cart-badge">{count}</span>}
    </button>
  );
}

export default function App() {
  return (
    <CartProvider>
      <div className="app">
        <header className="header">
          <span className="wordmark">Part<span>Select</span></span>
          <span className="assistant-badge">Part Assistant</span>
          <span className="spacer" />
          <CartButton />
        </header>
        <ChatWindow />
        <CartDrawer />
      </div>
    </CartProvider>
  );
}
