import type { AnalysisResult } from "@/lib/types";
import { CONTENT_LABELS, conclusionClass, conclusionLabel } from "@/lib/types";
import Link from "next/link";

const STATUS_LABEL = { found: "Trouvé", not_found: "Absent", uncertain: "Incertain", not_performed: "Non effectué" } as const;

export default function ResultView({ result, onRestart }: { result: AnalysisResult; onRestart: () => void }) {
  const date = new Date(result.created_at).toLocaleString("fr-FR", { dateStyle: "long", timeStyle: "short" });
  return (
    <section className="card result">
      {!result.detection_available && <span className="tag tag-demo">Détection pas encore active</span>}
      <p className="muted small">
        {CONTENT_LABELS[result.content_type]} · {date}
      </p>
      <h2 className={`conclusion ${conclusionClass(result)}`}>{conclusionLabel(result)}</h2>
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

      <p className="muted small">
        <Link href="/fiabilite">Fiabilité et limites de VEYRA</Link>
      </p>

      <button className="btn btn-primary" onClick={onRestart}>
        Nouvelle analyse
      </button>
    </section>
  );
}
