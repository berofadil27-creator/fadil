// Structure des résultats — cahier des charges, section 7.
export type ContentType = "text" | "image" | "video";

export type Conclusion = "likely_ai" | "likely_human" | "inconclusive";

export type IndicatorStatus = "found" | "not_found" | "not_performed";

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
