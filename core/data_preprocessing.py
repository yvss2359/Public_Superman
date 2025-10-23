import os
import pandas as pd
import requests
from zipfile import ZipFile
from io import BytesIO
import glob
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def fetch_eCO2mix_data(destination_folder: str,
                       tempo_url: str,
                       annual_url: str) -> None:
    """
    Télécharge les fichiers de consommation et TEMPO via les URLs spécifiées.
    """
    os.makedirs(destination_folder, exist_ok=True)

    urls = {
        "annual": annual_url,
        "tempo": tempo_url
    }

    for label, url in urls.items():
        try:
            print(f"⬇️  Téléchargement {label.upper()} : {url}")
            response = requests.get(url)
            response.raise_for_status()
            with ZipFile(BytesIO(response.content)) as zf:
                zf.extractall(destination_folder)
            print(f"✅ {label.upper()} téléchargé et extrait dans {destination_folder}")
        except Exception as e:
            print(f"❌ Échec du téléchargement de {label.upper()} : {e}")
            raise e


def convert_xls_eCO2mix_to_csv(input_path: str, output_path: str) -> None:
    with open(input_path, 'r', encoding='cp1252') as f:
        lines = f.readlines()

    cleaned_lines = []
    for i, line in enumerate(lines):
        if "RTE ne pourra" in line or "L'ensemble des informations disponibles" in line:
            continue

        line = line.replace('\t', ',')
        if i > 0:
            line = re.sub(r',\s*$', '', line)
        cleaned_lines.append(line.rstrip() + '\n')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)


def convert_all_xls_eCO2mix_data(xls_path: str, csv_path: str) -> None:
    os.makedirs(csv_path, exist_ok=True)
    xls_files = glob.glob(os.path.join(xls_path, "*.xls"))
    for file in xls_files:
        csv_file = os.path.join(csv_path, os.path.basename(file).replace(".xls", ".csv"))
        convert_xls_eCO2mix_to_csv(file, csv_file)


def load_data(filepath: str) -> pd.DataFrame:
    return pd.read_csv(filepath, encoding='utf-8')


def preprocess_annual_data(df: pd.DataFrame) -> pd.DataFrame:
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Datetime'] = pd.to_datetime(df['Date'].dt.strftime("%Y-%m-%d") + " " + df['Heures'], errors='coerce')
    df = df[['Date', 'Heures', 'Datetime', 'Consommation']].dropna()
    return df


def preprocess_tempo_data(df: pd.DataFrame) -> pd.DataFrame:
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    one_hot = pd.get_dummies(df['Type de jour TEMPO'], prefix='Type de jour TEMPO')
    return pd.concat([df[['Date']], one_hot], axis=1)


def concat_eCO2mix_annual_data(path_annual: str) -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(path_annual, "eCO2mix_RTE_*.csv")))
    dfs = [load_data(f) for f in files if os.path.isfile(f)]
    return pd.concat(dfs) if len(dfs) > 1 else dfs[0]


def concat_eCO2mix_tempo_data(path_tempo: str) -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(path_tempo, "eCO2mix_RTE_tempo*.csv")))
    dfs = [load_data(f) for f in files if os.path.isfile(f)]
    return pd.concat(dfs) if len(dfs) > 1 else dfs[0]


def merge_eCO2mix_data(df_annual: pd.DataFrame, df_tempo: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(df_annual, df_tempo, on="Date", how="left")
    return df


def preprocess_eCO2mix_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=['Type de jour TEMPO_BLEU', 'Type de jour TEMPO_BLANC', 'Type de jour TEMPO_ROUGE'], how='all')
    df['Consommation'] = pd.to_numeric(df['Consommation'], errors='coerce')
    return df


def preprocess_eCO2mix_data_engineered(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in df.columns if 'lag' in c.lower() or 'rolling' in c.lower()]
    df = df.dropna(subset=cols)
    return df


def split_features_target(data: pd.DataFrame, target: str) -> tuple:
    data = data.sort_values("Datetime")
    X = data.drop(columns=[target, "Date", "Heures", "Datetime"])
    y = data[[target]].astype("float32")
    return X, y
