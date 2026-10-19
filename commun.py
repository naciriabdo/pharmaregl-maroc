"""
commun.py — Ce que les deux espaces (utilisateur et administrateur) partagent :
la lecture des secrets et l'index documentaire.

L'index est créé UNE seule fois pour tous les visiteurs (st.cache_resource) : quand
l'administrateur ajoute un support, tous les utilisateurs en profitent immédiatement.
"""
import os
import threading

import streamlit as st

import config
from rag import stockage
from rag.decoupage import decouper
from rag.index import Index
from rag.lecture import lire_document


def lire_secret(nom: str, defaut: str = "") -> str:
    """Cherche une valeur : 1) fichier .streamlit/secrets.toml (ou Secrets en ligne), 2) variable d'environnement."""
    try:
        if nom in st.secrets:
            return str(st.secrets[nom]).strip()
    except Exception:
        pass
    return os.environ.get(nom, defaut).strip()


def diagnostic_secrets() -> str | None:
    """Explique pourquoi le fichier secrets.toml n'est pas lu (affiché dans l'espace administrateur)."""
    dossier = config.DOSSIER_PROJET / ".streamlit"
    if (dossier / "secrets.toml.txt").exists():
        return ("Le fichier s'appelle « secrets.toml.txt » : renommez-le en « secrets.toml » "
                "(commande : Rename-Item .streamlit\\secrets.toml.txt secrets.toml), puis relancez.")
    try:
        st.secrets.to_dict()
    except FileNotFoundError:
        return None
    except Exception as e:
        return f"Le fichier .streamlit/secrets.toml est mal écrit (guillemets, signe = …) : {e}"
    return None


@st.cache_resource
def verrou() -> threading.Lock:
    """Empêche deux modifications simultanées de l'index."""
    return threading.Lock()


def synchroniser(index: Index) -> bool:
    """L'index reflète exactement le dossier documents/ : ajoute les nouveaux fichiers, retire les supprimés."""
    presents = {f.name: f for f in stockage.lister()}
    modifie = False
    for nom in list(index.sources()):
        if nom not in presents:
            index.retirer(nom)
            modifie = True
    deja = set(index.sources())
    for nom, fichier in presents.items():
        if nom not in deja:
            index.ajouter(decouper(lire_document(nom, fichier.read_bytes())))
            modifie = True
    if modifie:
        index.sauvegarder()
    return modifie


@st.cache_resource(show_spinner="Préparation de la base documentaire (la première fois : quelques minutes)…")
def charger_index() -> Index:
    index = Index()
    index.charger()
    synchroniser(index)
    return index


def cle_groq() -> str:
    return lire_secret("GROQ_API_KEY")
