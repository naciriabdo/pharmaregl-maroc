"""
index.py — ÉTAPES 3 et 4 du RAG : indexer les passages, puis retrouver les plus pertinents.

On combine DEUX méthodes de recherche (recherche « hybride ») :

  1. Recherche par mots-clés (algorithme BM25) : excellente pour les références exactes
     comme « article 131 bis » ou « décret 2-24-729 ».
  2. Recherche par le sens (embeddings) : chaque passage est transformé en vecteur de
     nombres qui représente son sens. Deux textes qui disent la même chose avec des mots
     différents (« retrait du marché » / « rappel de lot ») ont des vecteurs proches.

Les deux classements sont ensuite fusionnés (méthode RRF), ce qui donne le meilleur des deux.
"""
import json

import numpy as np
from rank_bm25 import BM25Okapi

import config
from rag.decoupage import mots


class Index:
    def __init__(self):
        self.passages: list[dict] = []
        self.vecteurs: np.ndarray | None = None
        self.bm25 = None
        self.modele = None
        self.erreur_embeddings = None
        self._charger_modele()

    # ------------------------------------------------------------------ modèle
    def _charger_modele(self):
        """Charge le modèle d'embeddings (téléchargé automatiquement la 1re fois, ~220 Mo)."""
        try:
            from fastembed import TextEmbedding
            self.modele = TextEmbedding(model_name=config.MODELE_EMBEDDINGS)
        except Exception as e:  # pas d'Internet, modèle indisponible… : on continue en mots-clés seuls
            self.modele = None
            self.erreur_embeddings = str(e)

    def _vectoriser(self, textes: list[str]) -> np.ndarray:
        vecteurs = np.array(list(self.modele.embed(textes)), dtype=np.float32)
        # Normalisation : permet de mesurer la ressemblance par un simple produit scalaire
        return vecteurs / np.linalg.norm(vecteurs, axis=1, keepdims=True)

    # ------------------------------------------------------------------ ajout
    def ajouter(self, nouveaux: list[dict]):
        if not nouveaux:
            return
        self.passages.extend(nouveaux)
        if self.modele is not None:
            v = self._vectoriser([p["texte"] for p in nouveaux])
            self.vecteurs = v if self.vecteurs is None else np.vstack([self.vecteurs, v])
        self._reconstruire_bm25()

    def _reconstruire_bm25(self):
        self.bm25 = BM25Okapi([mots(p["texte"]) for p in self.passages]) if self.passages else None

    def retirer(self, source: str):
        """Supprime de l'index tous les passages d'un document (utilisé par l'espace administrateur)."""
        garder = [i for i, p in enumerate(self.passages) if p["source"] != source]
        self.passages = [self.passages[i] for i in garder]
        if self.vecteurs is not None:
            self.vecteurs = self.vecteurs[garder] if garder else None
        self._reconstruire_bm25()

    def sources(self) -> dict:
        """Nombre de passages par document (affiché dans la barre latérale)."""
        compte = {}
        for p in self.passages:
            compte[p["source"]] = compte.get(p["source"], 0) + 1
        return compte

    # ------------------------------------------------------------------ recherche
    def rechercher(self, question: str, k: int = config.NB_PASSAGES) -> list[dict]:
        if not self.passages:
            return []
        classements = []

        # 1) mots-clés
        scores_bm25 = self.bm25.get_scores(mots(question))
        classements.append(np.argsort(-scores_bm25)[:50])

        # 2) sens
        if self.modele is not None and self.vecteurs is not None:
            q = self._vectoriser([question])[0]
            scores_sens = self.vecteurs @ q
            classements.append(np.argsort(-scores_sens)[:50])

        # 3) fusion RRF : un passage bien classé par l'une OU l'autre méthode remonte
        fusion = {}
        for classement in classements:
            for rang, i in enumerate(classement):
                fusion[int(i)] = fusion.get(int(i), 0) + 1 / (60 + rang)
        classes = sorted(fusion, key=fusion.get, reverse=True)

        # 4) priorité aux textes officiels : au moins la moitié des passages viennent d'une loi,
        #    d'un décret… (s'il y en a parmi les candidats pertinents), le reste selon le classement.
        officiel = lambda i: self.passages[i]["source"].startswith(config.PREFIXES_TEXTES_OFFICIELS)
        lois = [i for i in classes if officiel(i)][: (k + 1) // 2]
        meilleurs = lois + [i for i in classes if i not in lois][: k - len(lois)]
        meilleurs.sort(key=fusion.get, reverse=True)
        return [dict(self.passages[i], score=round(fusion[i], 4)) for i in meilleurs]

    # ------------------------------------------------------------------ sauvegarde
    def sauvegarder(self):
        config.DOSSIER_INDEX.mkdir(parents=True, exist_ok=True)
        (config.DOSSIER_INDEX / "passages.json").write_text(json.dumps(self.passages, ensure_ascii=False), encoding="utf-8")
        fichier_vecteurs = config.DOSSIER_INDEX / "vecteurs.npy"
        if self.vecteurs is not None:
            np.save(fichier_vecteurs, self.vecteurs)
        elif fichier_vecteurs.exists():
            fichier_vecteurs.unlink()

    def charger(self) -> bool:
        fichier = config.DOSSIER_INDEX / "passages.json"
        if not fichier.exists():
            return False
        self.passages = json.loads(fichier.read_text(encoding="utf-8"))
        if not self.passages:
            return True
        vec = config.DOSSIER_INDEX / "vecteurs.npy"
        if self.modele is not None and vec.exists():
            self.vecteurs = np.load(vec)
            if len(self.vecteurs) != len(self.passages):
                self.vecteurs = self._vectoriser([p["texte"] for p in self.passages])
        elif self.modele is not None:
            self.vecteurs = self._vectoriser([p["texte"] for p in self.passages])
        self._reconstruire_bm25()
        return True
