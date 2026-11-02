import type { Metadata } from "next";
export const metadata: Metadata = { title: "Tarifs — VEYRA" };
export default function Tarifs() {
  return (
    <div className="container narrow page">
      <h1>Tarifs</h1>
      <div className="card empty">
        <h2>Pas encore de formule payante</h2>
        <p className="muted">
          Les tarifs seront publiés une fois les coûts et la qualité du service mesurés. La priorité est d&apos;abord un
          produit fiable.
        </p>
      </div>
    </div>
  );
}
