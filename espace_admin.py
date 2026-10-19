"""
espace_admin.py — L'espace réservé à l'administrateur (vous), protégé par un mot de passe.

On y dépose, remplace ou supprime les supports de référence. Chaque changement met à jour
l'index partagé : les utilisateurs en profitent immédiatement, sans redémarrer.
Le mot de passe se règle dans .streamlit/secrets.toml (ADMIN_PASSWORD) — jamais dans le code.
"""
import hmac
import shutil
import time

import streamlit as st

import config
from interface import theme
from interface.commun import charger_index, cle_groq, diagnostic_secrets, lire_secret, verrou
from rag import stockage
from rag.decoupage import decouper
from rag.lecture import lire_document, qualite_texte


def _github():
    """(jeton, dépôt, branche) si la synchronisation GitHub est configurée, sinon None."""
    jeton, depot = lire_secret("GITHUB_TOKEN"), lire_secret("GITHUB_REPO")
    return (jeton, depot, lire_secret("GITHUB_BRANCH", "main")) if jeton and depot else None


def _journal(texte: str):
    st.session_state.setdefault("journal", []).append(texte)


def connexion(mot_de_passe: str) -> bool:
    if st.session_state.get("admin_ok"):
        return True
    with st.form("connexion"):
        st.markdown("##### 🔐 Connexion administrateur")
        saisie = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Se connecter", type="primary"):
            # compare_digest : comparaison qui ne laisse pas deviner le mot de passe lettre par lettre
            if hmac.compare_digest(saisie.encode(), mot_de_passe.encode()):
                st.session_state.admin_ok = True
                st.rerun()
            time.sleep(1.5)  # ralentit les essais au hasard
            st.error("Mot de passe incorrect.")
    return False


def ajouter_supports(index, fichiers, github):
    with verrou(), st.spinner("Lecture, découpage et indexation…"):
        for f in fichiers:
            nom, contenu = stockage.nom_sur(f.name), f.getvalue()
            pages = lire_document(nom, contenu)
            passages = decouper(pages)
            if not passages:
                _journal(f"⚠️ {nom} : aucun texte lisible (PDF scanné ?) — non ajouté. Faites d'abord une reconnaissance de caractères (OCR).")
                continue
            if qualite_texte(pages) < 0.7:
                _journal(f"⚠️ {nom} : le texte extrait est illisible (police sans table de caractères, fréquent pour les PDF "
                         "en arabe) — non ajouté. Déposez une version texte (.txt) ou un PDF passé à l'OCR.")
                continue
            remplace = nom in index.sources()
            if remplace:
                index.retirer(nom)
            stockage.enregistrer(nom, contenu)
            index.ajouter(passages)
            ligne = f"✅ {nom} : {len(passages)} passages {'mis à jour' if remplace else 'indexés'}"
            if github:
                ok, info = stockage.github_envoyer(nom, contenu, *github)
                ligne += f" · {info}" if ok else f" · ⚠️ {info}"
            _journal(ligne)
        index.sauvegarder()


def supprimer_support(index, nom, github):
    with verrou():
        index.retirer(nom)
        stockage.supprimer(nom)
        index.sauvegarder()
    ligne = f"🗑️ {nom} supprimé de la base"
    if github:
        ok, info = stockage.github_supprimer(nom, *github)
        ligne += f" · {info}" if ok else f" · ⚠️ {info}"
    _journal(ligne)


def afficher():
    theme.barre_application()
    theme.entete_compact("Espace administrateur", "Gestion des supports de référence du chatbot", "icone_bouclier.png")

    probleme = diagnostic_secrets()
    if probleme:
        st.error(probleme, icon="🛠️")
    mot_de_passe = lire_secret("ADMIN_PASSWORD")
    if not mot_de_passe:
        st.warning("Aucun mot de passe administrateur n'est défini : l'espace est verrouillé.", icon="🔒")
        st.markdown("Ajoutez cette ligne dans **.streamlit/secrets.toml** (ou dans *Secrets* sur Streamlit Cloud), "
                    "puis relancez l'application :")
        st.code('ADMIN_PASSWORD = "choisissez-un-mot-de-passe-long"', language="toml")
        return
    if not connexion(mot_de_passe):
        return

    index = charger_index()
    github = _github()
    with st.sidebar:
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.admin_ok = False
            st.rerun()

    # --- tableau de bord ---------------------------------------------------------
    sources = index.sources()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Supports", len(sources))
    c2.metric("Passages indexés", sum(sources.values()))
    c3.metric("Recherche", "Hybride" if index.modele is not None else "Mots-clés")
    c4.metric("Service d'IA", "Actif" if cle_groq() else "Clé absente")
    if not cle_groq():
        st.warning("Clé Groq introuvable : les utilisateurs sont en mode démonstration. "
                   'Ajoutez GROQ_API_KEY = "gsk_…" dans les secrets.', icon="🔑")

    for ligne in st.session_state.pop("journal", []):
        st.toast(ligne)
        st.write(ligne)

    # --- ajout ---------------------------------------------------------------------
    theme.titre_section("Déposer des supports")
    st.caption("PDF (avec texte sélectionnable), Word ou TXT. Un fichier portant le même nom remplace l'ancien. "
               "⚠️ Les passages sont visibles par les utilisateurs : ne déposez ni données patients ni documents confidentiels.")
    n = st.session_state.setdefault("televersement", 0)
    fichiers = st.file_uploader("Choisir les fichiers", type=["pdf", "docx", "txt", "md"],
                                accept_multiple_files=True, key=f"televersement_{n}", label_visibility="collapsed")
    if fichiers and st.button(f"Analyser et indexer {len(fichiers)} fichier(s)", type="primary"):
        ajouter_supports(index, fichiers, github)
        st.session_state.televersement += 1  # vide la zone de dépôt
        st.rerun()

    # --- liste ----------------------------------------------------------------------
    theme.titre_section(f"Supports en ligne ({len(sources)})")
    if not sources:
        st.info("Aucun support pour l'instant.")
    for nom, nb in sources.items():
        chemin = config.DOSSIER_DOCUMENTS / nom
        taille = f"{chemin.stat().st_size / 1e6:.1f} Mo" if chemin.exists() else "—"
        col_nom, col_info, col_action = st.columns([6, 2, 1.4], vertical_alignment="center")
        col_nom.markdown(f"📄 **{nom}**  \n{config.titre(nom) if config.titre(nom) != nom else ''}")
        col_info.caption(f"{nb} passages · {taille}")
        with col_action.popover("Supprimer", icon="🗑️", use_container_width=True):
            st.write(f"Supprimer **{nom}** de la base ?")
            if st.button("Oui, supprimer", key=f"suppr_{nom}", type="primary"):
                supprimer_support(index, nom, github)
                st.rerun()

    # --- maintenance ----------------------------------------------------------------
    theme.titre_section("Maintenance")
    if github:
        st.success(f"Synchronisation GitHub active : chaque dépôt est aussi copié dans {github[1]}/documents.", icon="🔄")
    else:
        st.info("Les supports sont conservés dans le dossier documents/ de cet ordinateur. En ligne "
                "(Streamlit Cloud), ajoutez GITHUB_TOKEN et GITHUB_REPO dans les secrets pour qu'ils "
                "survivent aux redémarrages (voir README).", icon="💾")
    if st.button("🔁 Reconstruire tout l'index",
                 help="À utiliser si vous avez copié ou supprimé des fichiers directement dans le dossier documents/."):
        with verrou():
            shutil.rmtree(config.DOSSIER_INDEX, ignore_errors=True)
            charger_index.clear()
        st.rerun()
