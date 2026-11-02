import type { Metadata } from "next";
export const metadata: Metadata = { title: "Compte — VEYRA" };
export default function Compte() {
  return (
    <div className="container narrow page">
      <h1>Compte</h1>
      <div className="card empty">
        <h2>Bientôt disponible</h2>
        <p className="muted">
          Inscription, connexion, informations personnelles, paramètres, confidentialité et suppression du compte
          arriveront en Phase 7 avec Supabase.
        </p>
      </div>
    </div>
  );
}
