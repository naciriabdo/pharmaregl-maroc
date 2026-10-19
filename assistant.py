"""
assistant.py — ÉTAPE 5 du RAG : rédiger la réponse avec un modèle d'IA hébergé par Groq (clé gratuite).

On envoie au modèle :
  - des consignes (le « prompt système ») : comment se comporter, comment citer ;
  - les passages trouvés dans VOS documents ;
  - la question.
Option : le modèle peut aussi chercher sur Internet (outil « browser_search » de Groq).
Groq ne permet pas de limiter techniquement cette recherche à certains sites : on le lui
demande dans les consignes, puis le programme TRIE les liens obtenus (sites officiels / autres).
"""
import re
from urllib.parse import urlparse

from groq import Groq

import config

PROMPT_SYSTEME = """Tu es un assistant expert en réglementation pharmaceutique marocaine (loi 17-04, loi 27-26, \
décrets d'application, AMMPS), et en référentiels internationaux (GBT de l'OMS, droit de l'Union européenne).
Tu aides des pharmaciens, des étudiants et des professionnels de santé.

Base documentaire (passages fournis entre balises <documents>) :
- Loi n° 17-04 portant Code du médicament et de la pharmacie (2006), version française et texte arabe.
- Loi n° 27-26 modifiant et complétant la loi 17-04 (BO n° 7526 du 16 juillet 2026) : texte arabe officiel, et \
une traduction française de travail non officielle (en cas de doute, le texte arabe prévaut).
- Résultats d'un travail de recherche (PFE) sur la réforme de la régulation pharmaceutique au Maroc : c'est une \
analyse, pas un texte de loi.

Règles impératives :
1. Appuie-toi d'abord sur les passages fournis. Cite chaque information avec l'identifiant du passage entre \
crochets, par exemple [D2], et, quand c'est possible, le numéro d'article.
2. {regle_web}
3. Hiérarchie des sources : le texte de loi publié au Bulletin officiel prime ; le texte arabe publié au BO fait foi, \
la version française est une traduction ; l'analyse du PFE sert à expliquer et à comparer, jamais à remplacer la loi.
4. La loi 27-26 a modifié ou ajouté les articles 6, 7, 8 bis, 15, 30, 69, 120, 130, 131, 131 bis et 156 de la loi \
17-04, remplacé « certificat de vente libre » par « certificat de produit pharmaceutique », et renommé le titre III. \
Pour ces articles, la rédaction de la loi 27-26 prévaut sur celle de 2006 : signale-le. Elle est entrée en vigueur \
à sa publication, sauf les articles 6, 8 bis et 131 bis (applicables à la publication de leurs textes d'application) \
et l'obligation de l'article 120 alinéa 2 (délai de 3 mois pour les établissements industriels).
5. Sois rigoureux sur le statut juridique : distingue un texte publié, en vigueur, en attente de texte d'application, \
ou un simple projet. Donne les numéros et les dates.
6. N'invente jamais un numéro d'article, une date, un montant ou un délai. Si l'information est introuvable, \
dis-le franchement : « non documenté dans les sources consultées » (ce qui ne signifie pas que la règle n'existe pas).
7. Réponds dans la langue de la question (français par défaut), de façon structurée : une réponse directe en 1 à 2 \
phrases, puis les détails, puis, si utile, un point de vigilance.
8. Termine TOUJOURS par une section « Sources » : une ligne par source utilisée, sous la forme \
« [D1] Nom du document, page X, article Y » puis, le cas échéant, les liens officiels consultés.
9. Tu ne donnes pas d'avis juridique engageant : pour une décision officielle, renvoie vers l'AMMPS ou le texte publié."""

REGLE_SANS_WEB = "Tu n'as pas accès à Internet : réponds uniquement à partir des passages fournis."
REGLE_WEB = ("Vérifie sur Internet, UNIQUEMENT sur ces sites officiels : {sites}, ce que les passages ne couvrent pas, "
             "ou l'existence d'un texte plus récent (décret, arrêté, ligne directrice de l'AMMPS). Ignore tout autre site. "
             "Indique clairement ce qui vient du web, et ajoute les adresses (URL) complètes dans la section « Sources ».")


def _bloc_documents(passages: list[dict]) -> str:
    lignes = ["<documents>"]
    for i, p in enumerate(passages, start=1):
        page = f" page {p['page']}" if p.get("page") else ""
        lignes.append(f'<passage id="D{i}" source="{config.titre(p["source"])}{page}">\n{p["texte"]}\n</passage>')
    lignes.append("</documents>")
    return "\n".join(lignes)


def est_officiel(url: str) -> bool:
    """Vrai si l'adresse appartient à un site de la liste blanche (sous-domaines compris)."""
    hote = (urlparse(url).hostname or "").lower()
    return any(hote == d or hote.endswith("." + d) for d in config.SITES_OFFICIELS)


def _collecter_liens(objet, trouves: dict):
    """Parcourt la réponse de Groq et récupère toutes les paires (url, titre) des résultats de recherche."""
    if isinstance(objet, dict):
        if isinstance(objet.get("url"), str):
            trouves.setdefault(objet["url"], objet.get("title") or objet["url"])
        for v in objet.values():
            _collecter_liens(v, trouves)
    elif isinstance(objet, list):
        for v in objet:
            _collecter_liens(v, trouves)


def repondre(question: str, passages: list[dict], historique: list[dict], cle_api: str,
             recherche_web: bool = False) -> dict:
    """
    Renvoie {"texte": réponse, "sources_web": [{"titre", "url"}], "autres_liens": [...], "recherches": [...]}.
    historique : les échanges précédents [{"role": "user"/"assistant", "content": "texte"}]
    """
    client = Groq(api_key=cle_api)

    regle = REGLE_WEB.format(sites=", ".join(config.SITES_OFFICIELS)) if recherche_web else REGLE_SANS_WEB
    messages = [{"role": "system", "content": PROMPT_SYSTEME.format(regle_web=regle)}]
    messages += [{"role": m["role"], "content": m["content"]} for m in historique[-2:]]  # dernier échange (quota gratuit limité)
    messages.append({"role": "user", "content": f"{_bloc_documents(passages)}\n\nQuestion : {question}"})

    parametres = dict(
        model=config.MODELE_GROQ,
        messages=messages,
        temperature=0.2,                       # faible = réponses plus stables et factuelles
        max_completion_tokens=config.MAX_TOKENS_REPONSE,
    )
    if config.MODELE_GROQ.startswith("openai/gpt-oss"):
        parametres["include_reasoning"] = False   # on ne veut que la réponse finale, pas le raisonnement
        parametres["reasoning_effort"] = "low"     # raisonnement court : la réponse tient dans le quota gratuit
        if recherche_web:
            parametres["tools"] = [{"type": "browser_search"}]
            parametres["tool_choice"] = "auto"

    reponse = client.chat.completions.create(**parametres)
    message = reponse.choices[0].message

    texte = message.content or ""
    texte = re.sub(r"【[^】]*】", "", texte).strip()          # retire les marqueurs internes de citation web
    if not texte:
        texte = ("La réponse n'a pas pu être rédigée en entier (limite de longueur du quota gratuit). "
                 "Reformulez la question de façon plus précise, ou consultez les passages ci-dessous.")

    # Liens consultés : résultats de recherche renvoyés par Groq + adresses écrites dans la réponse
    liens = {}
    try:
        _collecter_liens(message.model_dump().get("executed_tools") or [], liens)
    except Exception:
        pass
    for url in re.findall(r"https?://[^\s)\]>\"'»]+", texte):
        liens.setdefault(url.rstrip(".,;"), url.rstrip(".,;"))

    officiels = [{"titre": t, "url": u} for u, t in liens.items() if est_officiel(u)]
    autres = [{"titre": t, "url": u} for u, t in liens.items() if not est_officiel(u)]
    return {"texte": texte, "sources_web": officiels, "autres_liens": autres, "recherches": []}
