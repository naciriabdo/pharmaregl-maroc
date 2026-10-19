"""
app.py — Point d'entrée de l'application (lancer :  streamlit run app.py).

L'application a deux espaces, choisis dans la barre latérale :
  • Espace utilisateur (page d'accueil, public) : poser des questions au chatbot ;
  • Espace administrateur (protégé par mot de passe) : déposer et gérer les supports.

Le contenu de chaque espace est dans le dossier interface/ ; l'habillage (inspiré de la couverture de la soutenance) dans interface/theme.py.
"""
import streamlit as st

import config
from interface import espace_admin, espace_utilisateur, theme

st.set_page_config(page_title="PharmaRégl Maroc — Assistant de réglementation",
                   page_icon=str(config.DOSSIER_ASSETS / "icone_gelule.png"), layout="wide")
theme.appliquer_style()

pages = [
    st.Page(espace_utilisateur.afficher, title="Espace utilisateur", icon="💬", url_path="chat", default=True),
    st.Page(espace_admin.afficher, title="Espace administrateur", icon="🔐", url_path="admin"),
]
st.navigation(pages).run()
