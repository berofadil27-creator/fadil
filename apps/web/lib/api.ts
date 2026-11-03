// Client de l'API VEYRA (services/analyzer). Les appels passent par /api/... :
// Next.js les redirige vers le serveur FastAPI (voir next.config.ts, variable VEYRA_API_URL).
import type { AnalysisResult, ContentType } from "./types";

function clientId(): string {
  // Identifiant anonyme du navigateur, en attendant les comptes. Ce n'est pas une authentification.
  const KEY = "veyra-client-id";
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KEY, id);
  }
  return id;
}

import type { ExtractedFrames } from "./videoFrames";
import type { ClientProvenance } from "./videoProvenance";

export type VideoInput = ExtractedFrames & { provenance?: ClientProvenance };

export async function analyze(type: ContentType, input: string | File | VideoInput): Promise<AnalysisResult> {
  const headers: Record<string, string> = { "X-Client-Id": clientId() };
  let body: BodyInit;
  if (type === "video") {
    const v = input as VideoInput;
    const form = new FormData();
    v.frames.forEach((f, i) => form.append("frames", f, `frame-${i}.jpg`));
    form.append("timestamps", v.timestamps.join(","));
    form.append("duration", String(v.duration));
    if (v.provenance) form.append("provenance", JSON.stringify(v.provenance));
    body = form;
  } else if (type === "text") {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify({ text: input as string });
  } else {
    const form = new FormData();
    form.append("file", input as File);
    body = form;
  }

  let res: Response;
  try {
    res = await fetch(`/api/analyze/${type}`, { method: "POST", headers, body });
  } catch {
    throw new Error("Le serveur VEYRA est injoignable. Vérifiez votre connexion et réessayez.");
  }
  if (res.ok) return (await res.json()) as AnalysisResult;

  if (res.status === 413)
    throw new Error("Fichier trop lourd pour le serveur de test (4 Mo maximum).");
  let message = `Erreur du serveur (${res.status}).`;
  try {
    const data = await res.json();
    if (data?.error?.message) message = data.error.message;
  } catch {}
  throw new Error(message);
}
