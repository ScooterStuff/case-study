import React from "react";

function ytId(url) {
  const m = /[?&]v=([A-Za-z0-9_-]{6,})/.exec(url || "");
  return m ? m[1] : null;
}

export default function InstallGuide({ block }) {
  const vid = ytId(block.video_url);
  return (
    <div className="card install-guide">
      <div className="block-title">Installation — {block.part?.title}</div>
      <div className="chip-row">
        {block.difficulty && <span className="chip">Difficulty: {block.difficulty}</span>}
        {block.time && <span className="chip">Time: {block.time}</span>}
      </div>
      {vid && (
        <a className="video-thumb" href={block.video_url} target="_blank" rel="noreferrer"
           aria-label="Open installation video on YouTube">
          <img src={`https://i.ytimg.com/vi/${vid}/mqdefault.jpg`} alt="Installation video thumbnail" />
          <span className="play" aria-hidden="true">▶</span>
        </a>
      )}
      {(block.stories || []).slice(0, 2).map((s, i) => (
        <blockquote key={i} className="story">“{s.slice(0, 280)}{s.length > 280 ? "…" : ""}”</blockquote>
      ))}
    </div>
  );
}
