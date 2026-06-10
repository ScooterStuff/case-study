import React from "react";

export default function ModelHelpModal({ onClose }) {
  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog"
           aria-label="Where to find your model number">
        <div className="drawer-head"><strong>Where do I find my model number?</strong>
          <button className="btn btn-link" onClick={onClose} aria-label="Close">✕</button></div>
        <p className="small">It's printed on a sticker or metal plate, not in the manual:</p>
        <ul className="small">
          <li><strong>Refrigerator</strong> — inside the fresh-food compartment: on the side wall,
            ceiling, or near the crisper drawers.</li>
          <li><strong>Dishwasher</strong> — on the door edge or the frame/tub lip, visible when
            the door is open.</li>
        </ul>
        <svg viewBox="0 0 280 110" className="model-illustration" aria-hidden="true">
          <rect x="10" y="10" width="100" height="90" rx="6" fill="none" stroke="#337778" strokeWidth="3"/>
          <line x1="10" y1="50" x2="110" y2="50" stroke="#337778" strokeWidth="3"/>
          <rect x="22" y="58" width="30" height="12" rx="2" fill="#f3c04c"/>
          <text x="60" y="68" fontSize="9" fill="#555453">label</text>
          <rect x="160" y="10" width="110" height="90" rx="6" fill="none" stroke="#337778" strokeWidth="3"/>
          <rect x="160" y="10" width="110" height="22" fill="none" stroke="#337778" strokeWidth="3"/>
          <rect x="175" y="36" width="34" height="12" rx="2" fill="#f3c04c"/>
          <text x="216" y="46" fontSize="9" fill="#555453">label</text>
          <text x="35" y="105" fontSize="10" fill="#555453">fridge</text>
          <text x="190" y="105" fontSize="10" fill="#555453">dishwasher</text>
        </svg>
      </div>
    </div>
  );
}
