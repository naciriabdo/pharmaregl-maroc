"""
config.py — Tous les réglages du chatbot, au même endroit.
Pour changer de modèle, de sites officiels ou de dossier, on ne modifie QUE ce fichier.
"""
from pathlib import Path

# --- Dossiers du projet -----------------------------------------------------
DOSSIER_PROJET = Path(__file__).parent
DOSSIER_DOCUMENTS = DOSSIER_PROJET / "documents"      # vos PDF/Word de référence (lus au démarrage)
DOSSIER_INDEX = DOSSIER_PROJET / "data" / "index"     # l'index construit à partir des documents
DOSSIER_ASSETS = DOSSIER_PROJET / "assets"            # illustration et icônes reprises de la couverture

# --- Modèle d'intelligence artificielle (hébergé par Groq, clé gratuite) ----
# Autres choix possibles : "openai/gpt-oss-20b" (plus rapide), "llama-3.3-70b-versatile" (sans recherche web).
MODELE_GROQ = "openai/gpt-oss-120b"
MAX_TOKENS_REPONSE = 1500              # longueur maximale d'une réponse (≈ 1 000 mots)

# --- Modèle d'« embeddings » (transforme un texte en vecteur de sens) -------
# Modèle multilingue (français, arabe, anglais), gratuit, exécuté sur votre ordinateur.
MODELE_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# --- Découpage des documents ------------------------------------------------
TAILLE_PASSAGE = 1200       # nombre de caractères par passage (≈ 200 mots)
CHEVAUCHEMENT = 200         # caractères repris d'un passage au suivant, pour ne pas couper une idée
NB_PASSAGES = 6             # nombre de passages envoyés au modèle pour chaque question

# Les fichiers dont le nom commence par ces mots sont des TEXTES OFFICIELS (lois, décrets…) :
# au moins la moitié des passages envoyés au modèle en proviennent, s'ils sont pertinents.
PREFIXES_TEXTES_OFFICIELS = ("Loi", "Decret", "Dahir", "Arrete", "Circulaire", "Decision")

# --- Titres affichés pour les documents fournis ----------------------------
# (nom du fichier -> titre lisible, utilisé dans les sources citées)
TITRES_DOCUMENTS = {
    "Resultats_PFE.pdf": "Résultats du PFE — Réforme de la régulation pharmaceutique au Maroc",
    "Loi_17-04_Code_du_medicament_FR.pdf": "Loi n° 17-04 portant Code du médicament et de la pharmacie (BO n° 5480, 2006) — version française",
    "Loi_17-04_Code_du_medicament_AR.txt": "Loi n° 17-04 portant Code du médicament et de la pharmacie (BO n° 5480, 2006) — texte arabe (transcrit par OCR)",
    "Loi_27-26_texte_officiel_AR.txt": "Loi n° 27-26 modifiant la loi 17-04 (BO n° 7526, 16 juillet 2026) — texte arabe officiel, transcription vérifiée",
    "Loi_27-26_traduction_FR_non_officielle.txt": "Loi n° 27-26 modifiant la loi 17-04 (BO n° 7526, 16 juillet 2026) — traduction française de travail, non officielle",
}


def titre(nom: str) -> str:
    return TITRES_DOCUMENTS.get(nom, nom)


# --- Sites officiels (liste blanche) -----------------------------------------
# Utilisée de deux façons : (1) donnée au modèle comme seule source web autorisée ;
# (2) pour TRIER les liens de la réponse : seuls ceux de ces sites sont affichés comme sources officielles.
SITES_OFFICIELS = [
    "sgg.gov.ma",               # Secrétariat général du gouvernement : Bulletin officiel
    "sante.gov.ma",             # Ministère de la Santé ET tous ses sous-domaines, dont l'AMMPS
                                # (les sous-domaines sont inclus automatiquement)
    "cg.gov.ma",                # Conseil de gouvernement (communiqués, projets de loi)
    "chambredesrepresentants.ma",
    "chambredesconseillers.ma",
    "who.int",                  # Organisation mondiale de la santé (GBT, WLA)
    "ema.europa.eu",            # Agence européenne des médicaments
    "eur-lex.europa.eu",        # Textes juridiques de l'Union européenne
    "health.ec.europa.eu",      # Commission européenne – Santé
    "edqm.eu",                  # Pharmacopée européenne, OCABR
]
