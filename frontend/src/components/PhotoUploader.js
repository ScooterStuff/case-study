import React, { useRef, useState } from "react";
import { extractModelNumber, runOcr } from "../lib/ocr";

// "Show me your sticker" — drag-and-drop / camera capture / file picker, then
// run OCR client-side and surface the most likely model number for one-click
// reuse in the conversation. All client-side; zero API keys.
export default function PhotoUploader({ onModelDetected, disabled }) {
  const fileRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [preview, setPreview] = useState(null);
  const [text, setText] = useState("");
  const [model, setModel] = useState(null);
  const [error, setError] = useState(null);

  const reset = () => {
    setBusy(false);
    setProgress(0);
    setPreview((url) => {
      if (url) URL.revokeObjectURL(url);
      return null;
    });
    setText("");
    setModel(null);
    setError(null);
  };

  const handlePick = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    reset();
    setPreview(URL.createObjectURL(file));
    setBusy(true);
    try {
      const ocrText = await runOcr(file, { onProgress: setProgress });
      setText(ocrText);
      setModel(extractModelNumber(ocrText));
    } catch (err) {
      setError("Couldn't read that photo. Try a clearer shot of the sticker.");
    } finally {
      setBusy(false);
    }
  };

  const accept = () => {
    onModelDetected && onModelDetected(model);
    reset();
  };

  return (
    <>
      <input
        type="file"
        accept="image/*"
        capture="environment"
        ref={fileRef}
        onChange={handlePick}
        style={{ display: "none" }}
        aria-hidden="true"
      />
      <button
        type="button"
        className="btn btn-photo"
        onClick={() => fileRef.current && fileRef.current.click()}
        disabled={disabled}
        aria-label="Upload a photo of your appliance's model number sticker"
        title="Photo of your model sticker"
      >
        📷
      </button>
      {(preview || busy || error) && (
        <div
          className="ocr-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Model number from photo"
          onClick={(e) => e.target === e.currentTarget && reset()}
        >
          <div className="ocr-modal">
            <button type="button" className="ocr-close" onClick={reset} aria-label="Close">
              ✕
            </button>
            {preview && (
              <img src={preview} alt="Uploaded model sticker" className="ocr-preview" />
            )}
            {busy && (
              <div className="ocr-progress" role="status">
                Reading sticker… {progress}%
                <div className="ocr-bar">
                  <div className="ocr-bar-fill" style={{ width: `${progress}%` }} />
                </div>
              </div>
            )}
            {!busy && error && <div className="ocr-error">{error}</div>}
            {!busy && !error && model && (
              <>
                <div className="ocr-found">
                  <div className="muted small">Detected model number</div>
                  <div className="ocr-model mono">{model}</div>
                </div>
                <div className="ocr-actions">
                  <button type="button" className="btn btn-teal" onClick={accept}>
                    Use this model
                  </button>
                  <button type="button" className="btn btn-outline" onClick={reset}>
                    Try another photo
                  </button>
                </div>
              </>
            )}
            {!busy && !error && !model && text && (
              <>
                <div className="ocr-error">
                  No model number detected in that photo. Try framing the sticker more closely.
                </div>
                <pre className="ocr-text mono small">{text.trim().slice(0, 200)}</pre>
                <button type="button" className="btn btn-outline" onClick={reset}>
                  Try another photo
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
