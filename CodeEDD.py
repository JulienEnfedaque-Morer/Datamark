!pip install kagglehub pandas sqlalchemy pymysql matplotlib seaborn tqdm

import kagglehub
import os
import shutil
from sqlalchemy import create_engine
import pandas as pd
from tqdm import tqdm

# Télécharger dataset
#path = kagglehub.dataset_download("bwandowando/clash-royale-season-18-dec-0320-dataset")

#print("Téléchargé dans :", path)

"""
path = "/home/jovyan/work/data/versions/20"

# Dossier cible
target_dir = "/home/jovyan/work/data"

# Si le dossier existe déjà, on le supprime (optionnel)
if os.path.exists(target_dir):
    shutil.rmtree(target_dir)

# Copier tout (fichiers + sous-dossiers)
shutil.copytree(path, target_dir)

print("Dataset copié vers :", target_dir)
"""
dir = "/home/jovyan/work/data/versions/20/"


# ----------------------------
# 3️⃣ Config MySQL
# ----------------------------
# Assurez-vous que MySQL est exposé sur docker-compose
engine = create_engine('mysql+pymysql://root:rootpass@mysql:3306/ClashRoyal')

# ----------------------------
# 4️⃣ Import dimension cartes avec progression
# ----------------------------
card_folder = os.path.join(dir, "BattlesStaging_01012021_WL_tagged")
files = [f for f in os.listdir(card_folder) if f.endswith(".csv")]

total_files = len(files)
print(f"Total CSV à charger : {total_files}")

for i, file in enumerate(files, start=1):
    file_path = os.path.join(card_folder, file)
    df_cards = pd.read_csv(file_path)
    df_cards.to_sql("dim_card", engine, if_exists="append", index=False)
    
    # Affichage pourcentage
    percent = (i / total_files) * 100
    print(f"Import {i}/{total_files} ({percent:.2f}%) : {file}")

print("dim_card importée avec succès !")


# ============================================================
# 5️⃣ CHARGEMENT RAW DES BATTLES (ELT - étape LOAD)
# ============================================================

CHUNKSIZE = 100000

# Supprimer si existe
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS raw_battles"))

for folder in os.listdir(path):
    if "BattlesStaging" in folder:
        folder_path = os.path.join(path, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(".csv"):
                    file_path = os.path.join(folder_path, file)
                    print("RAW LOAD :", file_path)
                    for chunk in pd.read_csv(file_path, chunksize=CHUNKSIZE):
                        chunk.to_sql("raw_battles", engine, if_exists="append", index=False)

print("✔ RAW chargé")


# ============================================================
# 6️⃣ TRANSFORMATION RELATIONNELLE (3NF)
# ============================================================

raw_df = pd.read_sql("SELECT * FROM raw_battles", engine)

def transform_side(df, side):
    df_player = pd.DataFrame()
    df_player["match_id"] = df["Unnamed: 0"]
    df_player["player_tag"] = df[f"{side}.tag"]
    df_player["role"] = side
    df_player["crowns"] = df[f"{side}.crowns"]
    df_player["trophyChange"] = df[f"{side}.trophyChange"]
    df_player["elixir_average"] = df[f"{side}.elixir.average"]
    return df_player

winner_df = transform_side(raw_df, "winner")
loser_df = transform_side(raw_df, "loser")

match_players = pd.concat([winner_df, loser_df], ignore_index=True)


# --- table player (dimension relationnelle)
players = pd.DataFrame(match_players["player_tag"].unique(), columns=["player_tag"])
players.to_sql("player", engine, if_exists="replace", index=False)

# --- table match
match_df = raw_df[["Unnamed: 0", "battleTime"]].rename(columns={"Unnamed: 0": "match_id"})
match_df.drop_duplicates().to_sql("match_table", engine, if_exists="replace", index=False)

# --- table match_player
match_players.to_sql("match_player", engine, if_exists="replace", index=False)

print("✔ Modèle relationnel chargé")


# ============================================================
# 7️⃣ MODELE DIMENSIONNEL (STAR SCHEMA)
# ============================================================

# ---------- DIM PLAYER ----------
dim_player = players.copy()
dim_player.insert(0, "player_key", range(1, len(dim_player) + 1))
dim_player.to_sql("dim_player", engine, if_exists="replace", index=False)

# ---------- DIM TIME ----------
raw_df["battleTime"] = pd.to_datetime(raw_df["battleTime"])
dim_time = raw_df[["battleTime"]].drop_duplicates().copy()
dim_time["year"] = dim_time["battleTime"].dt.year
dim_time["month"] = dim_time["battleTime"].dt.month
dim_time["day"] = dim_time["battleTime"].dt.day
dim_time.insert(0, "time_key", range(1, len(dim_time) + 1))
dim_time.to_sql("dim_time", engine, if_exists="replace", index=False)

print("✔ Dimensions créées")


# ============================================================
# 8️⃣ TABLE DE FAITS
# ============================================================

match_players["win_flag"] = match_players["role"].apply(lambda x: 1 if x == "winner" else 0)

# jointure player_key
fact_df = match_players.merge(dim_player, on="player_tag")

# jointure time_key
fact_df = fact_df.merge(match_df, on="match_id")
fact_df = fact_df.merge(dim_time, on="battleTime")

fact_final = fact_df[[
    "player_key",
    "time_key",
    "crowns",
    "trophyChange",
    "elixir_average",
    "win_flag"
]]

fact_final.to_sql("fact_match", engine, if_exists="replace", index=False)

print("✔ Table de faits remplie")
print("🎯 PIPELINE COMPLET OK")