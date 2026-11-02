export default function DemoBanner() {
  return (
    <div className="demo-banner" role="note">
      <strong>Prototype</strong> — Photo : VEYRA lit les métadonnées, vérifie la provenance C2PA et utilise un modèle
      d&apos;analyse visuelle (Sightengine). Ces résultats restent des indices, jamais une certitude. Texte
      (expérimental, français) : un modèle open source repère certaines tournures typiques de l&apos;IA ; il peut
      en laisser passer. Vidéo (expérimental) : 6 images extraites sont analysées par le même modèle visuel.
    </div>
  );
}
