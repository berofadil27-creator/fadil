import type { Metadata } from "next";
import LaboRunner from "./LaboRunner";

export const metadata: Metadata = {
  title: "Labo — VEYRA",
  robots: { index: false, follow: false },
};

export default function Labo() {
  return (
    <div className="container narrow page">
      <h1>Labo : détecteur vidéo expérimental</h1>
      <p className="muted">
        Page de test interne – le score est un indice expérimental, pas un verdict.
      </p>
      <LaboRunner />
    </div>
  );
}
