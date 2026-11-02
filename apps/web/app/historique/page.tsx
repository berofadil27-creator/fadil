import type { Metadata } from "next";
export const metadata: Metadata = { title: "Historique — VEYRA" };
export default function Historique() {
  return (
    <div className="container narrow page">
      <h1>Historique</h1>
      <div className="card empty">
        <h2>Bientôt disponible</h2>
        <p className="muted">
          L&apos;historique arrivera avec les comptes utilisateurs (Phase 7). Vous retrouverez vos analyses, leur date,
          leur résultat et leur rapport, et pourrez les supprimer avec leurs fichiers.
        </p>
      </div>
    </div>
  );
}
