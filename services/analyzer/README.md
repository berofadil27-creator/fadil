# VEYRA — moteur d'analyse (FastAPI)

Phase 3 : serveur, routes API, validation des données, système d'erreurs et système de tâches.
**Aucun module de détection n'est encore actif** : chaque analyse renvoie « inconclusive »
avec des indicateurs « not_performed ». Photo : Phase 4. Texte : Phase 5. Vidéo : Phase 6.

En ligne : https://veyra-api.vercel.app — documentation interactive : https://veyra-api.vercel.app/docs

## Lancer en local (Windows / PowerShell)
```powershell
cd services\analyzer
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```
Tests : `python -m pytest -q` (15 tests).
Le site (apps/web) appelle `/api/...`, redirigé vers `VEYRA_API_URL` (par défaut http://localhost:8000).

## Routes (cahier, section 8)
| Route | Fonction |
|---|---|
| POST /api/analyze/text | Analyser un texte (JSON `{"text": "..."}`) |
| POST /api/analyze/image | Analyser une photo (formulaire, champ `file`) |
| POST /api/analyze/video | Analyser une vidéo (formulaire, champ `file`) |
| GET /api/analysis/{id} | Consulter un résultat |
| GET /api/history | Consulter son historique |
| DELETE /api/analysis/{id} | Supprimer une analyse |
| GET /api/health | Vérifier que le serveur fonctionne |

Toutes les routes (sauf health) exigent l'en-tête `X-Client-Id` : identifiant anonyme du navigateur
qui sépare les historiques. Ce n'est **pas** une authentification (Supabase Auth, phase ultérieure).
Erreurs : `{"error": {"code": "...", "message": "..."}}`.

## Limites provisoires (choix techniques, non fixés par le cahier)
- Texte : 300 à 20 000 caractères. Photo : 10 Mo (JPEG, PNG, WebP, HEIC). Vidéo : 100 Mo (MP4, MOV, WebM).
- Le type réel est vérifié par la signature du fichier, pas par son extension.
- Hébergement Vercel : requêtes limitées à ~4,5 Mo. Les gros fichiers passeront par Supabase Storage.
- Historique et limite d'usage (30 analyses/heure) **en mémoire** : effacés au redémarrage,
  et pas partagés entre instances du serveur. Base PostgreSQL / Supabase prévue ensuite.
- Aucun fichier n'est conservé, seulement le rapport.
