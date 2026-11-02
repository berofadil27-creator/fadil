"use client";
import { useRef, useState } from "react";
import type { AnalysisResult, ContentType } from "@/lib/types";
import { CONTENT_LABELS } from "@/lib/types";
import { LIMITS, formatBytes, validateFile, validateText } from "@/lib/validation";
import { analyze } from "@/lib/api";
import { extractFrames } from "@/lib/videoFrames";
import { saveToHistory } from "@/lib/history";
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
  const [saved, setSaved] = useState(false);
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

    // Étapes réellement effectuées — jamais de fausse progression (cahier des charges).
    setPhase("loading");
    const first = { label: tab === "text" ? "Vérification de la longueur du texte" : "Vérification du format et de la taille", done: true };
    const send = { label: tab === "video" ? "Envoi des images au serveur VEYRA et analyse" : "Envoi au serveur VEYRA et vérification", done: false };
    const extract = { label: "Extraction de 6 images dans votre navigateur", done: false };
    setSteps(tab === "video" ? [first, extract, send] : [first, send]);
    try {
      let input: Parameters<typeof analyze>[1] = tab === "text" ? text : (file as File);
      if (tab === "video") {
        input = await extractFrames(file as File, 6);
        setSteps([first, { ...extract, done: true }, send]);
      }
      const r = await analyze(tab, input);
      setSteps((s) => s.map((x) => ({ ...x, done: true })));
      setSaved(await saveToHistory(r).catch(() => false));
      setResult(r);
      setPhase("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Une erreur est survenue.");
      setPhase("input");
    }
  }

  function restart() {
    setPhase("input"); setResult(null); setText(""); setFile(null); setError(null);
  }

  if (phase === "result" && result)
    return (
      <>
        <ResultView result={result} onRestart={restart} />
        <p className="muted small center">
          {saved ? "Rapport enregistré dans votre historique." : "Rapport non conservé : connectez-vous pour garder un historique."}
        </p>
      </>
    );

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
            <p className="muted small">La vidéo reste sur votre appareil : seules 6 images extraites sont envoyées et analysées. Le son n&apos;est pas analysé.</p>
          )}
        </>
      )}

      {error && <p className="error" role="alert">{error}</p>}

      <button className="btn btn-primary full" onClick={start}>Lancer l&apos;analyse</button>
      <p className="muted small center">Votre contenu est envoyé au serveur VEYRA pour vérification. Les fichiers ne sont jamais conservés ; si vous êtes connecté, seul le rapport est gardé dans votre historique.</p>
    </section>
  );
}
