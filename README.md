# PharmaRégl Maroc — assistant de réglementation pharmaceutique (chatbot RAG)

Axe 4 du PFE « Réforme du système de régulation pharmaceutique au Maroc ».
Le chatbot répond aux questions de réglementation pharmaceutique à partir :
1. de vos documents de référence (dossier `documents/` ou téléversement dans la page) ;
2. en option, de recherches en ligne orientées vers les **sites officiels** (Bulletin officiel, AMMPS, Ministère de la Santé, OMS, EMA, EUR-Lex…) ; les liens hors liste sont signalés à part.

Le modèle d'IA est hébergé par **Groq** (clé API gratuite). Chaque réponse cite ses sources : `[D1]` pour un passage de vos documents, lien cliquable pour une source web.

## Installation en un double-clic (Windows)
1. Décompresser le zip (par exemple sur le Bureau).
2. Double-cliquer sur **INSTALLER.bat** : il installe Python 3.12 si besoin, l'environnement `.venv`,
   les bibliothèques, enregistre la clé Groq et le mot de passe administrateur, puis crée l'icône
   **PharmaRégl Maroc** sur le Bureau et dans le menu Démarrer.
3. Ensuite, il suffit de double-cliquer sur l'icône : l'application s'ouvre dans sa propre fenêtre.
   `Arreter PharmaRegl.bat` arrête le serveur en arrière-plan.

## Deux espaces
- **Espace utilisateur** (page d'accueil, public) : poser des questions ; aucun dépôt ni suppression possible.
- **Espace administrateur** (`/admin`, mot de passe `ADMIN_PASSWORD`) : déposer, remplacer, supprimer les supports.
  La base documentaire = le dossier `documents/` ; chaque changement met l'index à jour pour tous les utilisateurs.

Sans clé API, l'application fonctionne en **mode démonstration** : elle affiche les passages trouvés, sans réponse rédigée.

## Installer comme une application
Chrome/Edge sur ordinateur : icône « Installer » dans la barre d'adresse. Android : menu ⋮ → *Ajouter à l'écran d'accueil*.
iPhone : Partager → *Sur l'écran d'accueil*.

## Organisation du code
| Fichier | Rôle |
|---|---|
| `config.py` | Tous les réglages : modèle Groq, sites officiels, taille des passages |
| `rag/lecture.py` | Étape 1 — lire les PDF / Word / TXT, page par page |
| `rag/decoupage.py` | Étape 2 — découper en passages de ~200 mots |
| `rag/index.py` | Étapes 3-4 — indexer (mots-clés BM25 + sens) et retrouver les passages pertinents |
| `rag/assistant.py` | Étape 5 — rédiger la réponse avec le modèle Groq, recherche web en option, tri des liens officiels |
| `rag/stockage.py` | Enregistrer / supprimer les supports dans `documents/` (+ copie GitHub optionnelle) |
| `app.py` | Point d'entrée : les deux espaces |
| `interface/espace_utilisateur.py` | Page publique du chatbot |
| `interface/espace_admin.py` | Espace administrateur (mot de passe) |
| `interface/theme.py` | Habillage façon application, inspiré de la couverture de la soutenance |
| `outils/` | Installateur, lanceur et arrêt pour Windows (PowerShell) |
| `assets/` | Illustration et icônes reprises de la couverture |

## Mise en ligne
GitHub (sans le fichier `secrets.toml`, dépôt **privé** si les supports ne sont pas publics) puis Streamlit Community Cloud :
`GROQ_API_KEY` et `ADMIN_PASSWORD` se collent dans *Advanced settings → Secrets*.
En ligne, le disque est effacé à chaque redémarrage : pour conserver les supports déposés dans l'espace administrateur,
ajoutez aussi `GITHUB_TOKEN` (jeton « fine-grained », droit *Contents : Read and write* sur ce seul dépôt) et `GITHUB_REPO`.
Voir le guide PDF, étapes 16 et 17.

## Avertissement
Outil d'aide à la recherche documentaire : il ne remplace ni le texte publié au Bulletin officiel, ni un avis de l'AMMPS.
