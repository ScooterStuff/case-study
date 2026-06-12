import React from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <span className="wordmark">Part<span>Select</span></span>
        <span className="assistant-badge">Part Assistant</span>
      </header>
      <ChatWindow />
    </div>
  );
}
