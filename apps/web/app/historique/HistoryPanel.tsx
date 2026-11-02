"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { currentUserId, deleteFromHistory, listHistory, type HistoryRow } from "@/lib/history";
import { CONTENT_LABELS, conclusionClass, conclusionLabel } from "@/lib/types";
import ResultView from "@/components/ResultView";

export default function HistoryPanel() {
  const [state, setState] = useState<"loading" | "anon" | "ready">("loading");
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [open, setOpen] = useState<HistoryRow | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      if (!(await currentUserId())) return setState("anon");
      try { setRows(await listHistory()); } catch (e) { setError((e as Error).message); }
      setState("ready");
    })();
  }, []);

  async function remove(id: string) {
    if (!confirm("Supprimer définitivement cette analyse ?")) return;
    setError(null);
    try {
      await deleteFromHistory(id);
      setRows((r) => r.filter((x) => x.id !== id));
      setOpen(null);
    } catch (e) { setError((e as Error).message); }
  }

  if (state === "loading") return <div className="card empty"><p className="muted">Chargement…</p></div>;
  if (state === "anon")
    return (
      <div className="card empty">
        <h2>Connectez-vous</h2>
        <p className="muted">L&apos;historique est réservé aux comptes. Les analyses faites sans compte ne sont pas conservées.</p>
        <Link href="/compte" className="btn btn-primary full center">Se connecter</Link>
      </div>
    );

  if (open)
    return (
      <>
        <ResultView result={open.result} onRestart={() => setOpen(null)} />
        <button className="btn full danger" onClick={() => remove(open.id)}>Supprimer cette analyse</button>
        {error && <p className="error" role="alert">{error}</p>}
      </>
    );

  return (
    <>
      {error && <p className="error" role="alert">{error}</p>}
      {rows.length === 0 ? (
        <div className="card empty">
          <h2>Aucune analyse</h2>
          <p className="muted">Vos prochaines analyses, faites en étant connecté, apparaîtront ici.</p>
        </div>
      ) : (
        <ul className="history">
          {rows.map((r) => (
            <li key={r.id} className="card history-row">
              <button className="history-open" onClick={() => setOpen(r)}>
                <span className="muted small">
                  {CONTENT_LABELS[r.content_type]} · {new Date(r.created_at).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" })}
                </span>
                <strong className={conclusionClass(r.result)}>{conclusionLabel(r.result)}</strong>
              </button>
              <button className="history-del" aria-label="Supprimer" onClick={() => remove(r.id)}>Supprimer</button>
            </li>
          ))}
        </ul>
      )}
      <p className="muted small center">Seuls les rapports sont conservés, jamais le texte, la photo ou la vidéo analysés.</p>
    </>
  );
}
