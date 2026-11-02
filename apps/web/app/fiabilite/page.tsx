import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Fiabilité et limites — VEYRA" };

export default function Fiabilite() {
  return (
    <div className="container narrow page">
      <h1>Fiabilité et limites</h1>
      <p>
        Aucun outil ne peut dire avec certitude si un contenu a été créé par IA. VEYRA présente des{" "}
        <strong>indices</strong>, jamais des preuves. Voici ce que nos propres tests montrent, erreurs comprises.
      </p>

      <section className="card">
        <h2>Texte : indice faible seulement</h2>
        <p>
          Modèle expérimental CamemBERTa, conçu pour le français. Testé le 2 novembre 2026 sur 40 textes humains
          (Wikinews, Wikivoyage, Wikibooks, Wikisource, tous écrits avant 2021) et 40 textes générés par trois petits
          modèles d&apos;IA (Qwen 2.5, Llama 3.2, Gemma 2).
        </p>
        <table className="rel-table">
          <tbody>
            <tr><th>Textes IA repérés</th><td>34 sur 40</td></tr>
            <tr><th>Textes humains pris à tort pour de l&apos;IA</th><td>3 sur 40 (des dépêches de presse)</td></tr>
          </tbody>
        </table>
        <p className="muted small">
          Ces erreurs sur des textes humains sont trop fréquentes pour une conclusion ferme. Un score élevé est donc
          présenté comme « indice faible » et la conclusion reste « Indéterminé ». Les textes courts (emails), les
          textes retravaillés et ceux d&apos;IA récentes sont les plus difficiles. Un score bas ne prouve jamais
          qu&apos;un texte est humain.
        </p>
      </section>

      <section className="card">
        <h2>Photo</h2>
        <p>
          VEYRA lit d&apos;abord les déclarations présentes dans le fichier (C2PA, IPTC, paramètres de génération), puis
          utilise un service d&apos;analyse d&apos;image (Sightengine). Testé sur 54 images de Wikimedia Commons.
        </p>
        <table className="rel-table">
          <tbody>
            <tr><th>Images IA repérées</th><td>28 sur 28</td></tr>
            <tr><th>Photos réelles prises à tort pour de l&apos;IA</th><td>0 sur 26 (1 « Indéterminé »)</td></tr>
          </tbody>
        </table>
        <p className="muted small">
          Échantillon petit et facile : surtout des illustrations IA, aucune photo réelle retouchée par IA, aucune
          image IA récente très réaliste. Ces chiffres ne garantissent pas la même réussite sur vos photos.
          L&apos;absence de métadonnées ne signifie pas qu&apos;une image est artificielle.
        </p>
      </section>

      <section className="card">
        <h2>Vidéo</h2>
        <p>
          Votre téléphone ou ordinateur extrait 6 images de la vidéo ; seules ces images sont analysées. La vidéo
          elle-même n&apos;est jamais envoyée. Le son, les métadonnées et le montage ne sont pas analysés.
        </p>
        <p className="muted small">
          Pas encore d&apos;évaluation sur de vraies vidéos : traitez ce résultat avec une prudence particulière.
        </p>
      </section>

      <section className="card">
        <h2>À retenir</h2>
        <ul className="checks">
          <li>Un contenu humain peut être classé à tort, et un contenu IA peut passer inaperçu.</li>
          <li>Aucun score n&apos;est affiché : sa signification n&apos;est pas encore assez validée.</li>
          <li>Ne prenez jamais de décision importante sur la seule base de VEYRA.</li>
          <li>Les photos et vidéos dépendent d&apos;un quota quotidien : au-delà, l&apos;analyse est refusée et le site le dit.</li>
        </ul>
        <p className="muted small">Tests réalisés par l&apos;équipe VEYRA, novembre 2026. Ils seront refaits sur des jeux plus larges.</p>
      </section>

      <p className="center">
        <Link href="/analyser" className="btn btn-primary">Analyser un contenu</Link>
      </p>
    </div>
  );
}
