<<<<<<< HEAD
# Projet Clash Royale - Entrepôt de données

# Datamark
groupe : 
Emilien Jurkiewicz
Julien Enfedaque-Morer

## Jeu de données
- **Dataset** : [Clash Royale Season 18 Dataset](https://www.kaggle.com/bwandowando/clash-royale-season-18-dec-0320-dataset)
- **Contenu** : Dizaines de milliers de parties avec statistiques in-game (couronnes, elixir, trophées, cartes jouées)
- **Période** : Saison 18 (Décembre 2020 - Janvier 2021)
- **Membres de l'équipe** : Julien Enfedaque-Morer, Emilien Jurkiewicz

---

## Architecture technique

### Stack complète
- **Docker Compose** avec :
  - MySQL 8.0 pour le stockage des données
  - Jupyter Notebook pour les scripts ELT/BI
  - Metabase pour la visualisation
  - Dozzle pour la centralisation des logs

### Pipeline ELT
1. **Extraction** : Téléchargement automatique depuis Kaggle
2. **Chargement** : Import CSV dans MySQL (``raw_battles``)
3. **Transformation** :
   - Normalisation vers modèle relationnel (3NF)
   - Création du modèle dimensionnel en étoile
   - Génération de la table de faits

**Durée estimée** : 45-135 minutes pour 9 fichiers CSV

---

## Modèle relationnel (3NF)
- **Tables** : ``raw_battles``, ``player``, ``match_table``, ``match_player``, ``dim_card``
- **Clés primaires et étrangères** définies pour garantir l'intégrité
- **MCD/ERD** : Diagramme ajouté dans ``docs/erd.png`` *(à venir)*

---

## Modèle dimensionnel (Star Schema)

### Dimensions
- ``dim_player`` : Profils joueurs (tag unique)
- ``dim_time`` : Temporalité (année, mois, jour, heure)
- ``dim_card`` : Cartes du jeu (nom, rareté, élixir)

### Faits
- ``fact_match`` : Métriques de performance
  - Couronnes gagnées
  - Trophées en jeu
  - Élixir moyen utilisé
  - Indicateur de victoire

### Granularité
Par **joueur** et par **match**

### Exemples de questions analytiques
- Taux de victoire par carte jouée
- Score moyen par période temporelle
- Distribution de l'élixir consommé
- Cartes les plus performantes par niveau de trophées

## 📊 Modèles de données

### Modèle Relationnel (3NF)
Structure normalisée pour les données opérationnelles.

![Modèle Relationnel](images/erd.png)

### Modèle Dimensionnel (Star Schema)
Structure optimisée pour l'analyse (Business Intelligence).

![Star Schema](images/star_schema.png)

**Composition du Star Schema :**

#### 📍 Table de faits
- **fact_match** : Granularité = 1 ligne par joueur par match
  - Mesures : `crowns`, `trophyChange`, `elixir_average`, `win`

#### 🔷 Dimensions
- **dim_player** : Informations des joueurs (tag, nom, clan)
- **dim_time** : Dimension temporelle (année, mois, jour, weekend)
- **dim_card** : Catalogue des cartes utilisées
- **bridge_match_card** : Association N:N entre matches et cartes