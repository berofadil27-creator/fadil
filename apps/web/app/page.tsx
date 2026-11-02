import Link from "next/link";

const TYPES = [
  { icon: "Aa", title: "Texte", text: "Collez un texte. VEYRA examine les formulations, les répétitions et les régularités statistiques." },
  { icon: "◐", title: "Photo", text: "Importez une image. VEYRA lit les métadonnées, la provenance C2PA et les traces visuelles." },
  { icon: "▶", title: "Vidéo", text: "Importez une vidéo. VEYRA analyse des images représentatives et leur cohérence." },
];

export default function Home() {
  return (
    <>
      <section className="hero">
        <div className="container">
          <p className="eyebrow">Analyse de contenus générés ou modifiés par IA</p>
          <h1 className="hero-title">Discover What&apos;s Real.</h1>
          <p className="hero-sub">
            VEYRA vous aide à comprendre si un contenu pourrait avoir été créé ou modifié par une intelligence
            artificielle, avec des explications claires sur chaque indice.
          </p>
          <Link href="/analyser" className="btn btn-primary btn-lg">Commencer une analyse</Link>
        </div>
      </section>

      <section className="container section">
        <h2 className="section-title">Trois types d&apos;analyse</h2>
        <div className="grid3">
          {TYPES.map((t) => (
            <article key={t.title} className="card feature">
              <span className="feature-icon">{t.icon}</span>
              <h3>{t.title}</h3>
              <p className="muted">{t.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="container section">
        <div className="card trust">
          <h2>Fiabilité et limites</h2>
          <p>
            Aucun outil ne peut dire avec certitude d&apos;où vient un contenu. VEYRA présente des <strong>indices</strong>,
            jamais des preuves : un texte humain peut être classé à tort, et un contenu IA peut passer inaperçu.
          </p>
          <ul className="checks">
            <li>Trois conclusions possibles : indices IA, indices humains ou réels, ou indéterminé.</li>
            <li>Chaque résultat explique ce qui a été vérifié, et ce qui ne l&apos;a pas été.</li>
            <li>L&apos;absence de signature de provenance ne signifie pas qu&apos;un contenu est artificiel.</li>
          </ul>
        </div>
      </section>
    </>
  );
}
