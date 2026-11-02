// RÉSULTAT DE DÉMONSTRATION — Phase 2.
// Aucun moteur d'analyse n'est encore branché. Ce module ne prétend donc rien détecter :
// il renvoie toujours "Indéterminé", avec des indicateurs "non effectués".
// Il sera remplacé par un appel à l'API FastAPI (POST /api/analyze/...) en Phase 3.
import type { AnalysisResult, ContentType, Indicator } from "./types";

const PLANNED: Record<ContentType, { name: string; label: string }[]> = {
  text: [
    { name: "linguistic_features", label: "Caractéristiques linguistiques" },
    { name: "repetition", label: "Répétitivité des formulations" },
    { name: "statistical_signals", label: "Indices statistiques" },
  ],
  image: [
    { name: "metadata", label: "Métadonnées" },
    { name: "content_provenance", label: "Provenance (C2PA / Content Credentials)" },
    { name: "visual_traces", label: "Traces visuelles de génération ou de modification" },
  ],
  video: [
    { name: "metadata", label: "Métadonnées" },
    { name: "keyframes", label: "Analyse d'images représentatives" },
    { name: "content_provenance", label: "Provenance (C2PA / Content Credentials)" },
    { name: "temporal_consistency", label: "Cohérence entre les images" },
  ],
};

export function buildDemoResult(type: ContentType): AnalysisResult {
  const indicators: Indicator[] = PLANNED[type].map((p) => ({
    name: p.name,
    status: "not_performed",
    explanation: `${p.label} : vérification prévue, pas encore disponible dans ce prototype.`,
  }));
  return {
    analysis_id: `demo-${Date.now().toString(36)}`,
    content_type: type,
    status: "completed",
    conclusion: "inconclusive",
    confidence: null,
    indicators,
    limitations: [
      "Ceci est une démonstration : aucun moteur d'analyse n'a examiné votre contenu.",
      "VEYRA ne permet jamais de déterminer avec certitude l'origine d'un contenu.",
    ],
    created_at: new Date().toISOString(),
    is_demo: true,
  };
}
