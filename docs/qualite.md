# VEYRA — Phase 8 : tests et qualité

## 8.1 Erreurs et limites (testé en ligne le 2026-11-02, 14:20)

| Cas testé | Attendu | Obtenu |
|---|---|---|
| Texte vide / < 300 caractères | refus 422 | 422 |
| Texte > 20 000 caractères | refus 413 | 413 |
| JSON invalide | refus 422 | 422 |
| Photo > 4 Mo (API et via le site) | refus 413, message clair | 413 |
| Faux JPEG (contenu texte) | refus 415 | 415 |
| Fichier vide | refus 422 | 422 |
| Requête sans X-Client-Id | refus 400 | 400 |
| Analyse inexistante | 404 | 404 |
| Vidéo : 2 images ou 7 images | refus 422 | 422 |
| Vidéo : image non JPEG | refus 415 | 415 |
| Historique d'un autre client (API) | vide | vide |
| Historique Supabase sans connexion (lecture, écriture) | refus | 401 permission denied |
| Suppression de compte sans connexion | refus | 401 permission denied |
| Pages du site (/, /analyser, /historique, /compte, /tarifs) | 200 | 200 |
| Page inexistante | 404 | 404 |
| Tests automatiques backend | tous verts | 45/45 |

## Limites connues
- Limite d'usage (30 analyses/heure) et historique API : en mémoire, par instance Vercel ; les requêtes invalides ne sont pas comptées.
- Rapports de l'historique enregistrés par le navigateur : un utilisateur peut modifier son propre historique (pas celui des autres).
- Emails Supabase (confirmation, mot de passe) : SMTP par défaut, quelques emails par heure.
- Vidéo : vidéos HEVC parfois illisibles selon le navigateur ; son, métadonnées et C2PA vidéo non analysés.
- Seuils de décision provisoires, non validés sur un jeu large (étape 8.2).
