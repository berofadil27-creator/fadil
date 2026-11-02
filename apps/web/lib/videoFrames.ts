// Extraction d'images représentatives dans le navigateur (Phase 6).
// La vidéo n'est jamais envoyée : seules quelques images JPEG partent au serveur VEYRA.

export interface ExtractedFrames {
  frames: Blob[];
  timestamps: number[];
  duration: number;
}

const MAX_SIDE = 1024;

function once(el: HTMLVideoElement, ok: string, ms: number): Promise<void> {
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

const UNREADABLE =
  "Votre navigateur ne parvient pas à lire cette vidéo (format ou codec non pris en charge, par exemple HEVC). " +
  "Essayez une vidéo MP4 (H.264) ou un autre navigateur.";

export async function extractFrames(file: File, count = 6): Promise<ExtractedFrames> {
  const url = URL.createObjectURL(file);
  const video = document.createElement("video");
  video.muted = true;
  video.playsInline = true;
  video.preload = "auto";
  video.src = url;
  try {
    try {
      await once(video, "loadeddata", 15000);
    } catch {
      throw new Error(UNREADABLE);
    }
    const duration = video.duration;
    if (!isFinite(duration) || duration <= 0 || !video.videoWidth) throw new Error(UNREADABLE);

    const scale = Math.min(1, MAX_SIDE / Math.max(video.videoWidth, video.videoHeight));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Impossible de préparer l'extraction des images.");

    const frames: Blob[] = [];
    const timestamps: number[] = [];
    for (let i = 0; i < count; i++) {
      const t = (duration * (i + 0.5)) / count;
      video.currentTime = t;
      try {
        await once(video, "seeked", 10000);
      } catch {
        continue; // image non lisible : on ne prétend pas l'avoir analysée
      }
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, "image/jpeg", 0.88));
      if (blob && blob.size > 0) {
        frames.push(blob);
        timestamps.push(Math.round(t * 10) / 10);
      }
    }
    if (frames.length < 3) throw new Error(UNREADABLE);
    return { frames, timestamps, duration };
  } finally {
    video.removeAttribute("src");
    video.load();
    URL.revokeObjectURL(url);
  }
}
