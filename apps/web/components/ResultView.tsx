import type { AnalysisResult } from "@/lib/types";
import { CONCLUSION_LABELS, CONTENT_LABELS } from "@/lib/types";

const STATUS_LABEL = { found: "Trouvé", not_found: "Absent", not_performed: "Non effectué" } as const;

export default function ResultView({ result, onRestart }: { result: AnalysisResult; onRestart: () => void }) {
  const date = new Date(result.created_at).toLocaleString("fr-FR", { dateStyle: "long", timeStyle: "short" });
  return (
    <section className="card result">
      {result.is_demo && <span className="tag tag-demo">Résultat de démonstration</span>}
      <p className="muted small">
        {CONTENT_LABELS[result.content_type]} · {date}
      </p>
      <h2 className={`conclusion c-${result.conclusion}`}>{CONCLUSION_LABELS[result.conclusion]}</h2>
      {result.confidence === null && (
        <p className="muted small">Aucun score affiché : sa signification n&apos;a pas encore été validée par des tests.</p>
      )}

      <h3>Indicateurs</h3>
      <ul className="indicators">
        {result.indicators.map((i) => (
          <li key={i.name}>
            <span className={`pill p-${i.status}`}>{STATUS_LABEL[i.status]}</span>
            <span>{i.explanation}</span>
          </li>
        ))}
      </ul>

      <h3>Limites de l&apos;analyse</h3>
      <ul className="limits">
        {result.limitations.map((l) => (
          <li key={l}>{l}</li>
        ))}
      </ul>

      <button className="btn btn-primary" onClick={onRestart}>
        Nouvelle analyse
      </button>
    </section>
  );
}
