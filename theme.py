"""
theme.py — L'habillage visuel de l'application.

Inspiré de la couverture de la soutenance : son illustration (Ministère → AMMPS / Loi 17-04 →
établissements pharmaceutiques), ses couleurs (bleu marine, turquoise, doré, bleu ciel)
et ses icônes rondes (balance, gélule, bouclier) — mises en forme comme une application.

Tout le style est ici : pour changer une couleur, on modifie seulement la liste COULEURS.
"""
import base64
from functools import lru_cache

import streamlit as st

import config

COULEURS = {
    "marine": "#1F3A5F",     # titres
    "turquoise": "#0F7B78",  # accents, boutons
    "or": "#D4A537",         # traits, bordures
    "rose": "#E0566E",       # petites touches
    "ciel": "#A9D4E4",       # fond de l'illustration
    "fond": "#F5F9FC",
}


@lru_cache
def _b64(nom: str) -> str:
    return base64.b64encode((config.DOSSIER_ASSETS / nom).read_bytes()).decode()


def image(nom: str, classe: str = "", alt: str = "") -> str:
    """Balise <img> avec l'image intégrée (aucun fichier externe à servir)."""
    type_mime = "image/png" if nom.endswith(".png") else "image/jpeg"
    return f'<img class="{classe}" alt="{alt}" src="data:{type_mime};base64,{_b64(nom)}">'


def appliquer_style():
    c = COULEURS
    st.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.stApp {{ background: {c['fond']}; }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp p, .stApp li, .stApp label, .stApp button {{
  font-family: 'Inter', sans-serif; }}
.stApp h2, .stApp h3, .stApp h4, .stApp h5 {{ color: {c['marine']}; }}
.stAppDeployButton, #MainMenu, footer {{ display: none !important; }}
.block-container {{ padding-top: 2rem; max-width: 1180px; }}

/* --- barre d'application ------------------------------------------------- */
.barre-app {{ display:flex; align-items:center; gap: 12px; padding: 4px 2px 16px; }}
.barre-app img {{ width: 40px; height: 40px; }}
.barre-app .nom {{ font: 800 20px 'Inter', sans-serif; white-space: nowrap; color: {c['marine']}; letter-spacing: -.2px; }}
.barre-app .nom span {{ color: {c['turquoise']}; }}
.barre-app .badge {{ margin-left: auto; background: #fff; border: 1.5px solid {c['or']}; color: {c['marine']};
  border-radius: 999px; padding: 4px 12px; font: 600 12px 'Inter', sans-serif; white-space: nowrap; }}
.barre-app .badge::before {{ content: "●"; color: {c['turquoise']}; margin-right: 6px; }}

/* --- carte d'accueil ------------------------------------------------------ */
.accueil {{ display:grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); border-radius: 26px; overflow:hidden;
  background: linear-gradient(140deg, #FFFFFF 0%, #EAF3F8 100%); box-shadow: 0 18px 40px rgba(31,58,95,.12); }}
.accueil-texte {{ padding: 40px 38px 34px; display:flex; flex-direction:column; justify-content:center; }}
.surtitre {{ display:inline-flex; align-self:flex-start; align-items:center; gap: 8px; background:#fff;
  border: 1.5px solid {c['or']}; border-radius: 999px; padding: 6px 14px;
  font: 600 12px 'Inter', sans-serif; color: {c['rose']}; letter-spacing: .4px; text-transform: uppercase; }}
.accueil h1 {{ font: 800 clamp(26px, 3.2vw, 42px)/1.1 'Inter', sans-serif; color: {c['marine']};
  margin: 18px 0 0; padding: 0; letter-spacing: -.6px; }}
.accueil h1 span {{ color: {c['turquoise']}; }}
.trait-or {{ width: 72px; height: 6px; background: {c['or']}; border-radius: 3px; margin: 18px 0 14px; }}
.accroche {{ font: 400 16px/1.55 'Inter', sans-serif; color: #4A5F78; margin: 0; max-width: 520px; }}
.atouts {{ display:flex; flex-wrap: wrap; gap: 10px; margin-top: 24px; }}
.atout {{ display:flex; align-items:center; gap: 9px; background:#fff; border-radius: 14px; padding: 7px 14px 7px 7px;
  box-shadow: 0 3px 10px rgba(31,58,95,.08); font: 600 13px 'Inter', sans-serif; color: {c['marine']}; }}
.atout img {{ width: 30px; height: 30px; }}
.accueil-image {{ background: {c['ciel']}; position: relative; min-height: 420px; }}
.accueil-image img {{ position:absolute; inset:0; width:100%; height:100%; object-fit: cover; object-position: center top; }}
.accueil-image::after {{ content:""; position:absolute; inset:0;
  background: linear-gradient(90deg, rgba(234,243,248,.55) 0%, rgba(234,243,248,0) 18%); }}

/* --- en-tête compact (conversation, administrateur) ----------------------- */
.entete {{ display:flex; align-items:center; gap: 14px; background:#fff; border-radius: 18px; padding: 12px 18px;
  box-shadow: 0 6px 18px rgba(31,58,95,.08); border-left: 6px solid {c['or']}; }}
.entete img {{ width: 42px; height: 42px; }}
.entete .titre {{ font: 700 clamp(16px,1.9vw,20px)/1.2 'Inter', sans-serif; color: {c['marine']}; }}
.entete .sous {{ font: 500 13px 'Inter', sans-serif; color: {c['turquoise']}; margin-top: 2px; }}

/* --- suggestions de questions -------------------------------------------- */
.st-key-exemples button {{ background:#fff; border: 1.5px solid #DCE7EF; border-radius: 16px; color: {c['marine']};
  min-height: 66px; box-shadow: 0 3px 10px rgba(31,58,95,.05); justify-content: flex-start; }}
.st-key-exemples button * {{ white-space: normal !important; text-overflow: clip !important; overflow: visible !important;
  text-align: left; }}
.st-key-exemples button:hover {{ border-color: {c['or']}; color: {c['turquoise']}; }}
.titre-section {{ font: 700 14px 'Inter', sans-serif; color: {c['marine']}; text-transform: uppercase; letter-spacing:.5px;
  margin: 30px 0 10px; display:flex; align-items:center; gap: 10px; }}
.titre-section::before {{ content:""; width: 24px; height: 5px; background: {c['or']}; border-radius: 3px; }}

/* --- barre latérale ------------------------------------------------------- */
section[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #EEF5F9 0%, #DCEBF3 100%); }}
.carte-laterale {{ background:#fff; border-radius: 14px; padding: 10px 14px; border-left: 5px solid {c['turquoise']};
  font: 400 14px/1.45 'Inter', sans-serif; color: {c['marine']}; margin-bottom: 8px; }}

/* --- indicateurs de l'espace administrateur ------------------------------ */
[data-testid="stMetric"] {{ background:#fff; border-radius: 16px; padding: 12px 16px; border-left: 5px solid {c['or']};
  box-shadow: 0 3px 10px rgba(31,58,95,.06); }}
[data-testid="stMetricValue"] {{ font-size: 26px; color: {c['marine']}; }}

/* --- messages ------------------------------------------------------------- */
[data-testid="stChatMessage"] {{ background: #fff; border-radius: 18px; border: 1px solid #E1EAF1; padding: 14px 16px; }}

/* --- téléphone : l'image passe en haut, comme une bannière d'application -- */
@media (max-width: 900px) {{
  .block-container {{ padding-top: 3.4rem; }}
  .accueil {{ grid-template-columns: minmax(0, 1fr); border-radius: 22px; }}
  .accueil-image {{ order: -1; min-height: 240px; }}
  .accueil-image img {{ object-position: center 38%; }}
  .barre-app .nom {{ font-size: 18px; }}
  .accueil-image::after {{ background: linear-gradient(0deg, rgba(255,255,255,.9) 0%, rgba(255,255,255,0) 35%); }}
  .accueil-texte {{ padding: 20px 20px 24px; }}
  .accueil h1 {{ font-size: 26px; }}
  .accroche {{ font-size: 15px; }}
}}
</style>""")


def barre_application():
    st.html(f"""
<div class="barre-app">{image("icone_gelule.png")}
  <div class="nom">PharmaRégl <span>Maroc</span></div>
  <div class="badge">Assistant IA</div>
</div>""")


def page_accueil():
    """Carte d'accueil de l'espace utilisateur, avec l'illustration de la couverture."""
    barre_application()
    st.html(f"""
<section class="accueil">
  <div class="accueil-texte">
    <div class="surtitre">Réglementation pharmaceutique · Maroc</div>
    <h1>Posez votre question,<br><span>obtenez la réponse sourcée.</span></h1>
    <div class="trait-or"></div>
    <p class="accroche">AMM, pharmacovigilance, inspection, établissements pharmaceutiques :
      l'assistant répond à partir des lois 17-04 et 27-26 et des travaux de référence,
      vérifie sur les sites officiels, et cite toujours ses sources.</p>
    <div class="atouts">
      <div class="atout">{image("icone_balance.png")}Textes de référence</div>
      <div class="atout">{image("icone_gelule.png")}Réponses sourcées</div>
      <div class="atout">{image("icone_bouclier.png")}Sites officiels</div>
    </div>
  </div>
  <div class="accueil-image">{image("illustration.jpg", alt="Ministère de la Santé, AMMPS, loi 17-04 et établissements pharmaceutiques")}</div>
</section>""")


def entete_compact(titre: str, sous_titre: str, icone: str = "icone_gelule.png"):
    st.html(f"""
<div class="entete">{image(icone)}<div><div class="titre">{titre}</div><div class="sous">{sous_titre}</div></div></div>""")


def titre_section(texte: str):
    st.html(f'<div class="titre-section">{texte}</div>')
