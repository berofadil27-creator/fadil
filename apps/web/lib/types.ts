// Structure des résultats — cahier des charges, section 7.
export type ContentType = "text" | "image" | "video";

export type Conclusion = "likely_ai" | "likely_human" | "inconclusive";

export type IndicatorStatus = "found" | "not_found" | "uncertain" | "not_performed";

export interface Indicator {
  name: string;
  status: IndicatorStatus;
  explanation: string;
}

export interface AnalysisResult {
  analysis_id: string;
  content_type: ContentType;
  status: "pending" | "processing" | "completed" | "failed";
  conclusion: Conclusion;
  /** null tant que la signification du score n'a pas été validée par des tests. */
  confidence: number | null;
  indicators: Indicator[];
  limitations: string[];
  created_at: string;
  /** false tant qu'aucun module de détection réel n'est actif pour ce type de contenu. */
  detection_available: boolean;
  engine_version: string;
}

export const CONCLUSION_LABELS: Record<Conclusion, string> = {
  likely_ai: "Indices compatibles avec une génération IA",
  likely_human: "Indices compatibles avec une origine humaine ou réelle",
  inconclusive: "Indéterminé",
};

export const CONTENT_LABELS: Record<ContentType, string> = {
  text: "Texte",
  image: "Photo",
  video: "Vidéo",
};

/** Étape 8.3 : le texte ne donne jamais de conclusion ferme, seulement un « indice faible ». */
export function isWeakTextSignal(r: Pick<AnalysisResult, "content_type" | "conclusion" | "indicators">): boolean {
  if (r.content_type !== "text") return false;
  if (r.conclusion === "likely_ai") return true; // anciens rapports, avant 8.3
  return r.conclusion === "inconclusive" && r.indicators?.some((i) => i.name === "statistical_signals" && i.status === "found");
}

/** Étape 8.6 : vidéo dont au moins la moitié des images ont des traces IA, sans atteindre 2/3. */
export function isVideoAiHint(r: Pick<AnalysisResult, "content_type" | "conclusion" | "indicators">): boolean {
  return r.content_type === "video" && r.conclusion === "inconclusive" &&
    !!r.indicators?.some((i) => i.name === "ai_hint" && i.status === "found");
}

/** 2026-11-23 : vidéo sans indice et sans image IA nette → « Aucune trace d'IA détectée » (jamais « humain »). */
export function isVideoNoTrace(r: Pick<AnalysisResult, "content_type" | "conclusion" | "indicators">): boolean {
  if (r.content_type !== "video" || r.conclusion !== "inconclusive" || isVideoAiHint(r)) return false;
  const kf = r.indicators?.find((i) => i.name === "keyframes");
  return !!kf && (kf.status === "not_found" || kf.status === "uncertain");
}

export function conclusionLabel(r: Pick<AnalysisResult, "content_type" | "conclusion" | "indicators">): string {
  if (isWeakTextSignal(r)) return "Indéterminé — indice faible d’écriture IA";
  if (isVideoAiHint(r)) return "Indéterminé — indice d’IA";
  if (isVideoNoTrace(r)) return "Aucune trace d’IA détectée";
  return CONCLUSION_LABELS[r.conclusion];
}

export function conclusionClass(r: Pick<AnalysisResult, "content_type" | "conclusion" | "indicators">): string {
  return isWeakTextSignal(r) || isVideoAiHint(r) ? "c-weak" : `c-${r.conclusion}`;
}
