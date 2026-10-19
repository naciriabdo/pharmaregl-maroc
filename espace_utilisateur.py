"""
espace_utilisateur.py — La page publique : on pose une question, le chatbot répond en citant ses sources.
L'utilisateur ne peut NI ajouter NI supprimer de documents (c'est le rôle de l'administrateur).
"""
import html

import streamlit as st

import config
from interface import theme
from interface.commun import charger_index, cle_groq
from rag.assistant import repondre

AVATAR_IA = str(config.DOSSIER_ASSETS / "icone_gelule.png")
AVATAR_UTILISATEUR = "🧑‍⚕️"

EXEMPLES = [
    "Quelles sont les cinq conditions de l'AMM conditionnelle prévue par l'article 8 bis ?",
    "Qu'est-ce qui change pour la pharmacovigilance avec la loi 27-26 ?",
    "Quelles amendes la loi 27-26 prévoit-elle pour les manquements aux bonnes pratiques ?",
    "Comment l'article premier de la loi 17-04 définit-il le médicament ?",
]


def message_erreur(e: Exception) -> str:
    """Traduit les erreurs de Groq en consignes claires."""
    nom, texte = type(e).__name__, str(e)
    if "Authentication" in nom or "401" in texte:
        return "❌ Le service est momentanément indisponible (clé API refusée). Prévenez l'administrateur."
    if "RateLimit" in nom or "429" in texte:
        return ("⏳ Trop de questions en même temps pour le quota gratuit. Patientez une minute, "
                "ou désactivez la recherche Internet.")
    if "413" in texte or "too large" in texte.lower():
        return "📏 Question trop volumineuse pour le quota gratuit : reformulez-la plus brièvement."
    if "Connection" in nom:
        return "🌐 Pas de connexion avec le service d'IA : vérifiez votre accès Internet."
    return f"❌ Erreur lors de l'appel au modèle : {texte}"


def afficher_sources(message: dict):
    if message.get("passages"):
        with st.expander(f"📄 {len(message['passages'])} passages des documents de référence"):
            for i, p in enumerate(message["passages"], start=1):
                page = f", p. {p['page']}" if p.get("page") else ""
                st.markdown(f"**[D{i}] {config.titre(p['source'])}{page}**")
                extrait = html.escape(p["texte"][:700] + ("…" if len(p["texte"]) > 700 else ""))
                # dir="auto" : un passage en arabe s'affiche de droite à gauche
                st.html(f'<div dir="auto" style="color:#5F6F82;font-size:14px;line-height:1.6">{extrait}</div>')
    if message.get("sources_web"):
        with st.expander(f"🌐 {len(message['sources_web'])} sources officielles consultées en ligne"):
            for s in message["sources_web"]:
                st.markdown(f"- [{s['titre']}]({s['url']})")
    if message.get("autres_liens"):
        with st.expander(f"⚠️ {len(message['autres_liens'])} liens hors sites officiels (à vérifier)"):
            for s in message["autres_liens"]:
                st.markdown(f"- [{s['titre']}]({s['url']})")


def barre_laterale(index) -> bool:
    with st.sidebar:
        sources = index.sources()
        st.markdown("##### 📚 Base documentaire")
        if sources:
            liste = "".join(f'<div dir="auto" style="margin-bottom:6px">• {html.escape(config.titre(nom))}</div>' for nom in sources)
            st.html(f'<div class="carte-laterale">{liste}<small>{sum(sources.values())} passages indexés</small></div>')
        else:
            st.info("La base est vide : l'administrateur n'a pas encore déposé de supports.")
        web = st.toggle("Vérifier aussi sur les sites officiels (BO, AMMPS, OMS, EMA)", value=True,
                        help="Le chatbot complète et vérifie les documents sur les sites officiels. Réponse plus lente ; "
                             "si le quota gratuit est dépassé, il répond automatiquement à partir des documents seuls.")
        if st.button("🧹 Nouvelle conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        with st.expander("📲 Installer l'application"):
            st.markdown(
                "**Ordinateur (Chrome ou Edge)** : icône ⊕ « Installer » à droite de la barre d'adresse "
                "(ou menu ⋮ → *Caster, enregistrer et partager* → *Installer la page en tant qu'application*).\n\n"
                "**Android (Chrome)** : menu ⋮ → *Ajouter à l'écran d'accueil* → *Installer*.\n\n"
                "**iPhone (Safari)** : bouton Partager → *Sur l'écran d'accueil*.\n\n"
                "L'application s'ouvre alors dans sa propre fenêtre, avec son icône, comme une application téléchargée.")
        st.caption("Outil d'aide à la recherche documentaire : il ne remplace ni le texte publié au "
                   "Bulletin officiel, ni un avis de l'AMMPS.")
    return web


def afficher():
    index = charger_index()
    st.session_state.setdefault("messages", [])
    web = barre_laterale(index)
    cle_api = cle_groq()

    # Question tapée, ou exemple cliqué (le clic est mémorisé avant le réaffichage de la page)
    question = st.chat_input("Posez votre question (ex. : que change la loi 27-26 pour la pharmacovigilance ?)")
    question = question or st.session_state.pop("question_choisie", None)

    if not st.session_state.messages and not question:
        theme.page_accueil()
        theme.titre_section("Questions suggérées")
        with st.container(key="exemples"):
            colonnes = st.columns(2)
            for i, ex in enumerate(EXEMPLES):
                colonnes[i % 2].button(ex, use_container_width=True, key=f"ex{i}",
                                       on_click=st.session_state.update, kwargs={"question_choisie": ex})
    else:
        theme.barre_application()

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar=AVATAR_UTILISATEUR if m["role"] == "user" else AVATAR_IA):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                afficher_sources(m)

    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=AVATAR_UTILISATEUR):
        st.markdown(question)

    with st.chat_message("assistant", avatar=AVATAR_IA):
        passages = index.rechercher(question, k=config.NB_PASSAGES)
        if not cle_api:
            texte = ("**Mode démonstration** (le service d'IA n'est pas encore configuré par l'administrateur). "
                     f"Voici les {len(passages)} passages les plus pertinents trouvés dans les documents :")
            resultat = {"texte": texte, "sources_web": [], "autres_liens": [], "recherches": []}
        else:
            with st.spinner("Recherche dans les documents" + (" et sur les sites officiels…" if web else "…")):
                historique = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                try:
                    resultat = repondre(question, passages, historique, cle_api, recherche_web=web)
                except Exception as e:
                    trop_gros = "413" in str(e) or "429" in str(e) or "RateLimit" in type(e).__name__
                    if web and trop_gros:
                        # Quota gratuit dépassé par la recherche web : on répond avec les documents seuls
                        try:
                            resultat = repondre(question, passages, historique[-2:], cle_api, recherche_web=False)
                            resultat["texte"] = ("*Vérification en ligne impossible pour cette question (quota gratuit atteint) : "
                                                 "réponse fondée sur les documents de référence uniquement.*\n\n" + resultat["texte"])
                        except Exception as e2:
                            resultat = {"texte": message_erreur(e2), "sources_web": [], "autres_liens": [], "recherches": []}
                    else:
                        resultat = {"texte": message_erreur(e), "sources_web": [], "autres_liens": [], "recherches": []}
        message = {"role": "assistant", "content": resultat["texte"], "passages": passages,
                   "sources_web": resultat["sources_web"], "autres_liens": resultat["autres_liens"]}
        st.markdown(message["content"])
        afficher_sources(message)
    st.session_state.messages.append(message)
