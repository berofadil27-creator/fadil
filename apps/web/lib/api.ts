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

export async function analyze(type: ContentType, input: string | File): Promise<AnalysisResult> {
  const headers: Record<string, string> = { "X-Client-Id": clientId() };
  let body: BodyInit;
  if (type === "text") {
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
    throw new Error("Fichier trop lourd pour le serveur de test (environ 4 Mo maximum pour l'instant).");
  let message = `Erreur du serveur (${res.status}).`;
  try {
    const data = await res.json();
    if (data?.error?.message) message = data.error.message;
  } catch {}
  throw new Error(message);
}
