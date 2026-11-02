"use client";
import { useRef, useState } from "react";
import type { AnalysisResult, ContentType } from "@/lib/types";
import { CONTENT_LABELS } from "@/lib/types";
import { LIMITS, formatBytes, validateFile, validateText } from "@/lib/validation";
import { buildDemoResult } from "@/lib/demo";
import ResultView from "@/components/ResultView";

type Phase = "input" | "loading" | "result";
interface Step { label: string; done: boolean }

const TABS: ContentType[] = ["text", "image", "video"];

export default function AnalyzeWorkspace() {
  const [tab, setTab] = useState<ContentType>("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>("input");
  const [steps, setSteps] = useState<Step[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function switchTab(t: ContentType) {
    setTab(t); setFile(null); setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  function onFile(f: File | null) {
    setError(null); setFile(f);
    if (f && tab !== "text") setError(validateFile(tab, f));
  }

  async function start() {
    const err = tab === "text" ? validateText(text) : file ? validateFile(tab, file) : "Choisissez un fichier.";
    if (err) { setError(err); return; }

    // Étapes réellement effectuées — jamais de fausse progression (cahier des charges, page 3).
    setPhase("loading");
    setSteps([
      { label: tab === "text" ? "Vérification de la longueur du texte" : "Vérification du format et de la taille", done: true },
      { label: "Préparation du rapport de démonstration (aucun moteur connecté)", done: false },
    ]);
    await new Promise((r) => setTimeout(r, 600));
    setSteps((s) => s.map((x) => ({ ...x, done: true })));
    setResult(buildDemoResult(tab));
    setPhase("result");
  }

  function restart() {
    setPhase("input"); setResult(null); setText(""); setFile(null); setError(null);
  }

  if (phase === "result" && result) return <ResultView result={result} onRestart={restart} />;

  if (phase === "loading")
    return (
      <section className="card">
        <p className="muted small">Analyse : {CONTENT_LABELS[tab]}</p>
        <h2>Traitement en cours</h2>
        <ul className="steps">
          {steps.map((s) => (
            <li key={s.label} className={s.done ? "done" : ""}>
              <span className="dot" /> {s.label}
            </li>
          ))}
        </ul>
      </section>
    );

  const accept = tab === "text" ? undefined : LIMITS[tab].mime.join(",");

  return (
    <section className="card">
      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? "tab active" : "tab"} onClick={() => switchTab(t)}>
            {CONTENT_LABELS[t]}
          </button>
        ))}
      </div>

      {tab === "text" ? (
        <>
          <label htmlFor="txt" className="label">Collez votre texte</label>
          <textarea id="txt" rows={10} value={text} onChange={(e) => { setText(e.target.value); setError(null); }}
            placeholder="Collez ici le texte à analyser…" />
          <p className="muted small">{text.trim().length} / {LIMITS.text.maxChars} caractères · minimum {LIMITS.text.minChars}</p>
        </>
      ) : (
        <>
          <label className="drop" htmlFor="file">
            <input id="file" ref={inputRef} type="file" accept={accept} onChange={(e) => onFile(e.target.files?.[0] ?? null)} />
            <strong>{file ? file.name : `Importer une ${tab === "image" ? "photo" : "vidéo"}`}</strong>
            <span className="muted small">
              {file
                ? formatBytes(file.size)
                : `${LIMITS[tab].mime.map((m) => m.split("/")[1].toUpperCase()).join(", ")} · ${formatBytes(LIMITS[tab].maxBytes)} max`}
            </span>
          </label>
          {tab === "video" && (
            <p className="muted small">L&apos;analyse vidéo arrivera après les analyses photo et texte (Phase 6).</p>
          )}
        </>
      )}

      {error && <p className="error" role="alert">{error}</p>}

      <button className="btn btn-primary full" onClick={start}>Lancer l&apos;analyse</button>
      <p className="muted small center">Vos fichiers ne sont envoyés nulle part dans ce prototype : tout reste dans votre navigateur.</p>
    </section>
  );
}
