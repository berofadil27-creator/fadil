"use client";

import { useRef, useState } from "react";
import { INPUT_SIZE, preprocess, sigmoid } from "@/lib/labo/preprocess";

// Page de test interne : le modèle Community Forensics (ViT-S 384, licence MIT) tourne
// entièrement dans le navigateur. La vidéo n'est jamais envoyée.

const ORT_VERSION = "1.31.1"; // doit rester identique à la version de onnxruntime-web dans package.json
const WASM_PATHS = `https://cdn.jsdelivr.net/npm/onnxruntime-web@${ORT_VERSION}/dist/`;
const MODEL_URL = "/models/commfor384.onnx";
const MODEL_LABEL = "Community Forensics ViT-S 384 (fp32)";
const CACHE_NAME = "veyra-labo-model-v1";
const MAX_FRAMES = 60;
const THUMB_W = 160;

const UNREADABLE =
  "Votre navigateur ne parvient pas à lire cette vidéo (format ou codec non pris en charge, par exemple HEVC). " +
  "Essayez une vidéo MP4 (H.264) ou un autre navigateur.";

type OrtModule = typeof import("onnxruntime-web/wasm");
type Session = Awaited<ReturnType<OrtModule["InferenceSession"]["create"]>>;

interface FrameResult { t: number; score: number; thumb: string }
interface Progress { label: string; value: number }

let sessionPromise: Promise<{ ort: OrtModule; session: Session }> | null = null;

async function downloadModel(onProgress: (loaded: number, total: number) => void): Promise<ArrayBuffer> {
  let cache: Cache | null = null;
  try {
    if (typeof caches !== "undefined") cache = await caches.open(CACHE_NAME);
  } catch {
    cache = null;
  }
  if (cache) {
    const hit = await cache.match(MODEL_URL);
    if (hit) {
      const buf = await hit.arrayBuffer();
      onProgress(buf.byteLength, buf.byteLength);
      return buf;
    }
  }
  const res = await fetch(MODEL_URL);
  if (!res.ok || !res.body) throw new Error(`Téléchargement du modèle impossible (HTTP ${res.status}).`);
  const total = Number(res.headers.get("content-length")) || 87_377_477;
  const reader = res.body.getReader();
  const chunks: Uint8Array[] = [];
  let loaded = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    loaded += value.byteLength;
    onProgress(loaded, total);
  }
  if (res.headers.get("content-length") && loaded !== total) {
    throw new Error("Téléchargement du modèle incomplet, réessayez.");
  }
  const buf = new Uint8Array(loaded);
  let off = 0;
  for (const c of chunks) { buf.set(c, off); off += c.byteLength; }
  if (cache) {
    try {
      await cache.put(MODEL_URL, new Response(buf.slice(0), { headers: { "content-type": "application/octet-stream" } }));
    } catch {
      // stockage plein ou refusé : le modèle sera retéléchargé la prochaine fois
    }
  }
  return buf.buffer;
}

function loadSession(onProgress: (loaded: number, total: number) => void) {
  if (!sessionPromise) {
    sessionPromise = (async () => {
      const ort = await import("onnxruntime-web/wasm");
      ort.env.wasm.wasmPaths = WASM_PATHS;
      ort.env.wasm.numThreads =
        typeof crossOriginIsolated !== "undefined" && crossOriginIsolated
          ? Math.min(4, navigator.hardwareConcurrency || 1)
          : 1;
      const model = await downloadModel(onProgress);
      const session = await ort.InferenceSession.create(new Uint8Array(model), {
        executionProviders: ["wasm"],
        graphOptimizationLevel: "all",
      });
      return { ort, session };
    })();
    sessionPromise.catch(() => { sessionPromise = null; });
  }
  return sessionPromise;
}

function waitFor(el: HTMLVideoElement, ok: string, ms: number): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { cleanup(); reject(new Error("timeout")); }, ms);
    const onOk = () => { cleanup(); resolve(); };
    const onErr = () => { cleanup(); reject(new Error("decode")); };
    function cleanup() {
      clearTimeout(timer);
      el.removeEventListener(ok, onOk);
      el.removeEventListener("error", onErr);
    }
    el.addEventListener(ok, onOk);
    el.addEventListener("error", onErr);
  });
}

function median(values: number[]): number {
  if (!values.length) return 0;
  const s = [...values].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

const pct = (v: number) => `${(v * 100).toFixed(1)} %`;

export default function LaboRunner() {
  const [file, setFile] = useState<File | null>(null);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [results, setResults] = useState<FrameResult[]>([]);
  const [meta, setMeta] = useState<{ duration: number; width: number; height: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const cancelRef = useRef(false);

  async function run() {
    if (!file) return;
    setRunning(true);
    setError(null);
    setNotice(null);
    setCopied(false);
    setResults([]);
    setMeta(null);
    cancelRef.current = false;

    let session: Session, ort: OrtModule;
    try {
      setProgress({ label: "Chargement du modèle…", value: 0 });
      ({ ort, session } = await loadSession((loaded, total) =>
        setProgress({
          label: `Téléchargement du modèle : ${(loaded / 1e6).toFixed(0)} / ${(total / 1e6).toFixed(0)} Mo`,
          value: Math.min(1, loaded / total),
        }),
      ));
    } catch (e) {
      setError(`Le modèle n'a pas pu être chargé : ${e instanceof Error ? e.message : String(e)}`);
      setRunning(false);
      setProgress(null);
      return;
    }

    const url = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.muted = true;
    video.playsInline = true;
    video.preload = "auto";
    video.src = url;
    const found: FrameResult[] = [];
    try {
      try {
        await waitFor(video, "loadeddata", 15000);
      } catch {
        throw new Error(UNREADABLE);
      }
      const duration = video.duration;
      const width = video.videoWidth;
      const height = video.videoHeight;
      if (!isFinite(duration) || duration <= 0 || !width || !height) throw new Error(UNREADABLE);
      if (Math.min(width, height) < 64) throw new Error("Vidéo trop petite pour être analysée.");
      setMeta({ duration, width, height });

      const count = Math.min(MAX_FRAMES, Math.max(1, Math.ceil(duration)));
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      const thumb = document.createElement("canvas");
      thumb.width = THUMB_W;
      thumb.height = Math.round((THUMB_W * height) / width);
      const tctx = thumb.getContext("2d");
      if (!ctx || !tctx) throw new Error("Impossible de préparer l'extraction des images.");

      let skipped = 0;
      for (let i = 0; i < count; i++) {
        if (cancelRef.current) break;
        setProgress({ label: `Analyse de l'image ${i + 1} / ${count}`, value: i / count });
        const t = Math.min(i + 0.05, Math.max(0, duration - 0.05));
        video.currentTime = t;
        try {
          await waitFor(video, "seeked", 10000);
        } catch {
          skipped++;
          continue;
        }
        ctx.drawImage(video, 0, 0, width, height);
        const data = ctx.getImageData(0, 0, width, height).data;
        const x = preprocess(data, width, height, 4);
        const out = await session.run({ x: new ort.Tensor("float32", x, [1, 3, INPUT_SIZE, INPUT_SIZE]) });
        const logit = (out.logit.data as Float32Array)[0];
        tctx.drawImage(video, 0, 0, thumb.width, thumb.height);
        found.push({ t: Math.round(t * 100) / 100, score: sigmoid(logit), thumb: thumb.toDataURL("image/jpeg", 0.7) });
        setResults([...found]);
      }
      if (!found.length) throw new Error(UNREADABLE);
      const notes: string[] = [];
      if (skipped) notes.push(`${skipped} image(s) illisible(s) ignorée(s).`);
      if (duration > MAX_FRAMES) notes.push(`Seules les ${MAX_FRAMES} premières secondes ont été analysées.`);
      if (cancelRef.current) notes.push("Analyse interrompue.");
      setNotice(notes.join(" ") || null);
      setProgress({ label: "Terminé", value: 1 });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setProgress(null);
    } finally {
      video.removeAttribute("src");
      video.load();
      URL.revokeObjectURL(url);
      setRunning(false);
    }
  }

  const scores = results.map((r) => r.score);
  const summary = results.length
    ? {
        images: results.length,
        imagesAuDessusDe50: scores.filter((s) => s > 0.5).length,
        scoreMax: Math.max(...scores),
        scoreMedian: median(scores),
      }
    : null;

  async function copy() {
    if (!summary || !file) return;
    const payload = {
      page: "veyra-labo",
      modele: MODEL_LABEL,
      date: new Date().toISOString(),
      navigateur: navigator.userAgent,
      fichier: {
        nom: file.name,
        type: file.type,
        tailleOctets: file.size,
        dureeSecondes: meta ? Math.round(meta.duration * 100) / 100 : null,
        largeur: meta?.width ?? null,
        hauteur: meta?.height ?? null,
      },
      resume: {
        ...summary,
        scoreMax: Number(summary.scoreMax.toFixed(4)),
        scoreMedian: Number(summary.scoreMedian.toFixed(4)),
      },
      images: results.map((r) => ({ t: r.t, score: Number(r.score.toFixed(4)) })),
    };
    const text = JSON.stringify(payload, null, 2);
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    setCopied(true);
  }

  return (
    <>
      <section className="card">
        <label className="drop">
          <input
            type="file"
            accept="video/*"
            disabled={running}
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null);
              setResults([]);
              setError(null);
              setNotice(null);
              setProgress(null);
            }}
          />
          <strong>{file ? file.name : "Choisir une vidéo"}</strong>
          <span className="muted small">
            La vidéo reste sur votre appareil : rien n&apos;est envoyé. Une image par seconde est analysée (60 au maximum).
          </span>
        </label>
        <p className="muted small" style={{ marginTop: 10 }}>
          Au premier lancement, le modèle (environ 87 Mo) est téléchargé puis gardé en cache par le navigateur.
          Comptez une à quelques secondes par image selon l&apos;appareil.
        </p>
        <div style={{ display: "flex", gap: 10, marginTop: 16, flexWrap: "wrap" }}>
          <button className="btn btn-primary" onClick={run} disabled={!file || running}>
            {running ? "Analyse en cours…" : "Lancer le test"}
          </button>
          {running && (
            <button className="btn" onClick={() => { cancelRef.current = true; }}>
              Arrêter
            </button>
          )}
        </div>
        {progress && (
          <div style={{ marginTop: 16 }}>
            <div className="muted small">{progress.label}</div>
            <div style={{ height: 8, background: "var(--border)", borderRadius: 4, overflow: "hidden", marginTop: 6 }}>
              <div style={{ width: `${Math.round(progress.value * 100)}%`, height: "100%", background: "var(--blue)", transition: "width 0.2s" }} />
            </div>
          </div>
        )}
        {error && <p className="error">{error}</p>}
        {notice && <p className="muted small" style={{ marginTop: 12 }}>{notice}</p>}
      </section>

      {summary && (
        <section className="card">
          <h2>Résumé</h2>
          <table className="rel-table">
            <tbody>
              <tr><th>Images analysées</th><td>{summary.images}</td></tr>
              <tr><th>Images au-dessus de 50 %</th><td>{summary.imagesAuDessusDe50}</td></tr>
              <tr><th>Score maximal</th><td>{pct(summary.scoreMax)}</td></tr>
              <tr><th>Score médian</th><td>{pct(summary.scoreMedian)}</td></tr>
            </tbody>
          </table>
          <p className="muted small" style={{ marginTop: 10 }}>
            Page de test interne – le score est un indice expérimental, pas un verdict.
          </p>
          <button className="btn btn-primary" style={{ marginTop: 14 }} onClick={copy} disabled={running}>
            {copied ? "Résultats copiés" : "Copier les résultats"}
          </button>
        </section>
      )}

      {results.length > 0 && (
        <section className="card">
          <h2>Images</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12 }}>
            {results.map((r) => (
              <figure key={r.t} style={{ margin: 0 }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={r.thumb} alt={`Image à ${r.t.toFixed(1)} s`} style={{ width: "100%", borderRadius: 8, display: "block" }} />
                <figcaption className="small" style={{ marginTop: 4, display: "flex", justifyContent: "space-between" }}>
                  <span className="muted">{r.t.toFixed(1)} s</span>
                  <strong>{pct(r.score)}</strong>
                </figcaption>
              </figure>
            ))}
          </div>
        </section>
      )}
    </>
  );
}
