import type { Metadata } from "next";
import DemoBanner from "@/components/DemoBanner";
import AnalyzeWorkspace from "./AnalyzeWorkspace";

export const metadata: Metadata = { title: "Analyser — VEYRA" };

export default function AnalyserPage() {
  return (
    <div className="container narrow page">
      <h1>Espace d&apos;analyse</h1>
      <p className="muted">Choisissez un type de contenu : texte, photo ou vidéo.</p>
      <DemoBanner />
      <AnalyzeWorkspace />
    </div>
  );
}
