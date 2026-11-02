# VEYRA — site web (Phase 2)

Next.js (App Router) + TypeScript.

Pages : `/` Accueil · `/analyser` Analyse, chargement et résultat · `/historique` (Phase 7) · `/compte` (Phase 7) · `/tarifs` (plus tard).

Réel : vérification du format, de la taille et de la longueur (`lib/validation.ts`).
Démo : le résultat (`lib/demo.ts`) renvoie toujours « Indéterminé » avec des indicateurs « Non effectué », clairement signalé. Il sera remplacé par l'API FastAPI en Phase 3.
La structure du résultat (`lib/types.ts`) suit la section 7 du cahier des charges.

    npm install
    npm run dev     # http://localhost:3000
    npm run build   # vérifier que tout compile
