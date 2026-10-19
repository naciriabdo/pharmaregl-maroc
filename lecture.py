"""
lecture.py — ÉTAPE 1 du RAG : lire les documents et en extraire le texte.

Un PDF n'est pas du texte « brut » : il faut l'ouvrir avec une bibliothèque (pypdf)
qui sait récupérer le texte page par page. On garde le numéro de page, pour que
le chatbot puisse citer sa source (« Résultats PFE, p. 12 »).
"""
from pathlib import Path
import io
import re
import unicodedata

from pypdf import PdfReader
from docx import Document


def _nettoyer(texte: str) -> str:
    """Supprime les espaces en trop et recolle les mots coupés en fin de ligne."""
    texte = unicodedata.normalize("NFKC", texte)        # arabe : formes de présentation -> lettres normales
    texte = re.sub("[\u200e\u200f\u202a-\u202e\u00ad]", "", texte)  # marques de direction, traits invisibles
    texte = re.sub(r"-\n(\w)", r"\1", texte)            # mot coupé : « régle-\nmentation »
    texte = re.sub(r"[ \t]+", " ", texte)
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    return texte.strip()


def _cle_ligne(ligne: str) -> str:
    """Forme simplifiée d'une ligne (sans chiffres ni espaces) pour repérer les en-têtes répétés."""
    return re.sub(r"[\d\s]+", "", ligne)


def _lignes_repetees(pages_brutes: list[str]) -> set:
    """
    En-têtes et pieds de page : une ligne présente sur plus de la moitié des pages
    (« M.S – Direction de la réglementation… », numéro de page) n'apporte rien et
    fausse la recherche par mots-clés. On la retire.
    """
    if len(pages_brutes) < 4:
        return set()
    compte = {}
    for brut in pages_brutes:
        for cle in {_cle_ligne(l) for l in brut.split("\n")}:
            if len(cle) >= 6:
                compte[cle] = compte.get(cle, 0) + 1
    return {cle for cle, n in compte.items() if n > len(pages_brutes) / 2}


def lire_document(nom: str, contenu: bytes) -> list[dict]:
    """
    Renvoie une liste de pages : [{"source": nom, "page": 1, "texte": "..."}, ...]
    nom     : nom du fichier (sert à connaître le format et à citer la source)
    contenu : le fichier lui-même, sous forme d'octets
    """
    extension = Path(nom).suffix.lower()
    pages = []

    if extension == ".pdf":
        lecteur = PdfReader(io.BytesIO(contenu))
        bruts = [page.extract_text() or "" for page in lecteur.pages]
        repetees = _lignes_repetees(bruts)
        for numero, brut in enumerate(bruts, start=1):
            lignes = [l for l in brut.split("\n") if _cle_ligne(l) not in repetees]
            texte = _nettoyer("\n".join(lignes))
            if texte:
                pages.append({"source": nom, "page": numero, "texte": texte})

    elif extension == ".docx":
        doc = Document(io.BytesIO(contenu))
        texte = "\n".join(p.text for p in doc.paragraphs)
        # Un fichier Word n'a pas de pages fixes : on le traite comme une seule « page »
        pages.append({"source": nom, "page": None, "texte": _nettoyer(texte)})

    elif extension in (".txt", ".md"):
        texte = contenu.decode("utf-8", errors="ignore")
        # Un texte peut contenir des repères « === Page 3 === » (transcription d'un PDF) : on les respecte
        morceaux = re.split(r"^=+\s*Page\s+(\d+)\s*=+\s*$", texte, flags=re.M)
        if len(morceaux) > 1:
            for numero, bloc in zip(morceaux[1::2], morceaux[2::2]):
                if bloc.strip():
                    pages.append({"source": nom, "page": int(numero), "texte": _nettoyer(bloc)})
        else:
            pages.append({"source": nom, "page": None, "texte": _nettoyer(texte)})

    else:
        raise ValueError(f"Format non pris en charge : {extension} (formats acceptés : PDF, DOCX, TXT)")

    return pages


def qualite_texte(pages: list[dict]) -> float:
    """
    Proportion de « vrais mots » (lettres latines ou arabes, nombres) parmi les mots extraits.
    Certains PDF (souvent en arabe) utilisent des polices sans table de caractères : le texte extrait
    est alors du charabia (« R:¹³P47±Òº »). Une valeur inférieure à 0,7 signale ce problème.
    """
    mots = " ".join(p["texte"] for p in pages).split()
    if not mots:
        return 0.0
    motif = re.compile(r"^[«»(\[\"'“-]*([A-Za-zÀ-ÖØ-öø-ÿŒœ\u0621-\u064A\u0671-\u06D3’'-]+|[\d.,/%-]+)[»)\]\"'”.,;:!?…-]*$")
    return sum(1 for m in mots if motif.match(m)) / len(mots)
