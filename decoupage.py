"""
decoupage.py — ÉTAPE 2 du RAG : découper le texte en passages.

Pourquoi découper ? Le modèle ne peut pas lire 500 pages à chaque question (ce serait
lent et coûteux). On découpe donc les documents en petits passages d'environ 200 mots ;
pour chaque question, on ne lui enverra que les quelques passages pertinents.

Le « chevauchement » répète la fin d'un passage au début du suivant, pour qu'une
phrase coupée en deux ne perde pas son sens.
"""
import re

import config


def decouper(pages: list[dict]) -> list[dict]:
    passages = []
    for page in pages:
        texte = page["texte"]
        debut = 0
        while debut < len(texte):
            fin = min(debut + config.TAILLE_PASSAGE, len(texte))
            # On évite de couper au milieu d'une phrase : on recule jusqu'au dernier point.
            if fin < len(texte):
                dernier_point = max(texte.rfind(". ", debut, fin), texte.rfind("\n", debut, fin))
                if dernier_point > debut + config.TAILLE_PASSAGE // 2:
                    fin = dernier_point + 1
            morceau = texte[debut:fin].strip()
            if len(morceau) > 40:  # on ignore les fragments vides (numéros de page seuls, etc.)
                passages.append({"source": page["source"], "page": page["page"], "texte": morceau})
            if fin >= len(texte):
                break
            debut = max(fin - config.CHEVAUCHEMENT, debut + 1)
    return passages


# Découpe un texte en « mots » pour la recherche par mots-clés.
# On garde intacts les numéros juridiques : « 17-04 », « 2-24-728 », « 1461.25 ».
_MOTS_VIDES = set("""le la les de des du un une et en au aux à a l d que qui quoi dans par pour sur ou ne pas
est sont ce cette ces son sa ses leur leurs il elle ils elles se plus avec comme être été lors entre""".split())


def mots(texte: str) -> list[str]:
    texte = texte.lower()
    jetons = re.findall(r"\d+(?:[-.]\d+)+|\w+", texte)
    return [j for j in jetons if j not in _MOTS_VIDES]
