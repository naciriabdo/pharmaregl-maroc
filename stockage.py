"""
stockage.py — Où sont rangés les supports déposés par l'administrateur.

Règle simple : LA BASE DOCUMENTAIRE = LE DOSSIER documents/.
  - Ajouter un support  = enregistrer le fichier dans documents/ (puis l'indexer).
  - Supprimer un support = effacer le fichier de documents/ (puis le retirer de l'index).

Sur votre ordinateur, ce dossier est permanent. En ligne (Streamlit Community Cloud), le
disque est effacé à chaque redémarrage de l'application : les fichiers qui ne sont pas dans
GitHub disparaissent. D'où l'option « synchronisation GitHub » : si vous donnez un jeton
GitHub (GITHUB_TOKEN) dans les secrets, chaque support ajouté ou supprimé dans l'espace
administrateur est aussi ajouté ou supprimé dans le dossier documents/ de votre dépôt.
"""
import base64
from pathlib import Path
from urllib.parse import quote

import requests

import config

EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def nom_sur(nom: str) -> str:
    """Garde uniquement le nom du fichier (jamais un chemin comme ../../secret)."""
    return "".join(c for c in Path(nom).name if c.isprintable() and c not in '<>:"/\\|?*').strip()


def lister() -> list[Path]:
    config.DOSSIER_DOCUMENTS.mkdir(exist_ok=True)
    return sorted(f for f in config.DOSSIER_DOCUMENTS.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONS)


def enregistrer(nom: str, contenu: bytes) -> Path:
    config.DOSSIER_DOCUMENTS.mkdir(exist_ok=True)
    chemin = config.DOSSIER_DOCUMENTS / nom_sur(nom)
    chemin.write_bytes(contenu)
    return chemin


def supprimer(nom: str):
    (config.DOSSIER_DOCUMENTS / nom_sur(nom)).unlink(missing_ok=True)


# ----------------------------------------------------------------------------- GitHub (optionnel)
def _url_github(depot: str, nom: str) -> str:
    return f"https://api.github.com/repos/{depot}/contents/documents/{quote(nom_sur(nom))}"


def _entetes(jeton: str) -> dict:
    return {"Authorization": f"Bearer {jeton}", "Accept": "application/vnd.github+json"}


def _sha_existant(depot, nom, jeton, branche):
    r = requests.get(_url_github(depot, nom), headers=_entetes(jeton), params={"ref": branche}, timeout=30)
    return r.json().get("sha") if r.status_code == 200 else None


def github_envoyer(nom: str, contenu: bytes, jeton: str, depot: str, branche: str = "main") -> tuple[bool, str]:
    """Ajoute (ou remplace) le fichier dans le dossier documents/ du dépôt GitHub."""
    try:
        donnees = {"message": f"Ajout du support {nom_sur(nom)} (espace administrateur)",
                   "content": base64.b64encode(contenu).decode(), "branch": branche}
        sha = _sha_existant(depot, nom, jeton, branche)
        if sha:
            donnees["sha"] = sha
        r = requests.put(_url_github(depot, nom), headers=_entetes(jeton), json=donnees, timeout=120)
        if r.status_code in (200, 201):
            return True, "copié dans GitHub"
        return False, f"GitHub a refusé l'envoi ({r.status_code}) : {r.json().get('message', '')}"
    except Exception as e:
        return False, f"GitHub injoignable : {e}"


def github_supprimer(nom: str, jeton: str, depot: str, branche: str = "main") -> tuple[bool, str]:
    try:
        sha = _sha_existant(depot, nom, jeton, branche)
        if not sha:
            return True, "absent de GitHub"
        r = requests.delete(_url_github(depot, nom), headers=_entetes(jeton), timeout=60,
                            json={"message": f"Suppression du support {nom_sur(nom)}", "sha": sha, "branch": branche})
        if r.status_code == 200:
            return True, "supprimé de GitHub"
        return False, f"GitHub a refusé la suppression ({r.status_code}) : {r.json().get('message', '')}"
    except Exception as e:
        return False, f"GitHub injoignable : {e}"
