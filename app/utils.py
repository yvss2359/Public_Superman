import os
import json
import pandas as pd
from datetime import date
from dotenv import load_dotenv
import logging
import boto3
from botocore.client import Config

# Import modules métier
from core.data_preprocessing import (
    fetch_eCO2mix_data,
    convert_all_xls_eCO2mix_data,
    concat_eCO2mix_annual_data,
    concat_eCO2mix_tempo_data,
    preprocess_annual_data,
    preprocess_tempo_data,
    merge_eCO2mix_data,
    preprocess_eCO2mix_data,
    preprocess_eCO2mix_data_engineered,
    split_features_target
)
from core.features_engineering import (
    create_date_features,
    create_hour_features,
    create_lag_features,
    create_rolling_features,
)

logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

# === Config Kafka ===
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")

producer = None

def send_to_kafka(payload: dict):
    global producer
    try:
        if producer is None:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
        producer.send(KAFKA_TOPIC, payload)
    except Exception as e:
        print(f"[WARNING] Kafka not available. Skipping send. Error: {e}")

# === Upload predictions to MinIO ===

def upload_predictions_to_minio(local_path: str, object_name: str):
    """
    Upload un fichier local vers un bucket MinIO.
    """
    try:
        minio_endpoint = os.getenv("MINIO_ENDPOINT")
        minio_key = os.getenv("MINIO_ACCESS_KEY")
        minio_secret = os.getenv("MINIO_SECRET_KEY")
        bucket = os.getenv("MINIO_BUCKET")

        s3 = boto3.client(
            's3',
            endpoint_url=minio_endpoint,
            aws_access_key_id=minio_key,
            aws_secret_access_key=minio_secret,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',
        )
        s3.upload_file(local_path, bucket, object_name)
        logger.info(f"✅ Fichier '{object_name}' envoyé sur MinIO ({bucket})")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l’upload MinIO : {e}")
# === MLOps logique ===

def get_data_between_dates(T1: date, T2: date) -> pd.DataFrame:
    """
    Récupère les données brutes de consommation + tempo entre T1 et T2.
    Applique les étapes de téléchargement, conversion, nettoyage, fusion et filtrage temporel.
    """
    # Validation des dates
    today = date.today()
    if T1 < today:
        raise ValueError(f"T1 doit être ≥ aujourd’hui ({today})")
    if (T2 - T1).days > 7:
        raise ValueError("La période demandée ne doit pas dépasser 7 jours.")
    
    # Construction dynamique de l'URL tempo
    tempo_season = f"{T2.year - 1}-{T2.year}"
    tempo_url = f"https://eco2mix.rte-france.com/curves/downloadCalendrierTempo?season={tempo_season}"
    annual_url = "https://eco2mix.rte-france.com/download/eco2mix/eCO2mix_RTE_En-cours-TR.zip"

    # Étape 1 : Télécharger les fichiers zip depuis RTE
    fetch_eCO2mix_data(destination_folder="./data/01_raw", 
                       tempo_url=tempo_url, 
                       annual_url=annual_url)

    # Étape 2 : Convertir tous les fichiers .xls téléchargés en .csv propres
    convert_all_xls_eCO2mix_data(xls_path="./data/01_raw", csv_path="./data/02_external")

    # Étape 3 : Concaténer et prétraiter les fichiers annual et tempo
    annual_data = concat_eCO2mix_annual_data("./data/02_external")
    tempo_data = concat_eCO2mix_tempo_data("./data/02_external")

    annual_cleaned = preprocess_annual_data(annual_data)
    tempo_cleaned = preprocess_tempo_data(tempo_data)

    # Étape 4 : Fusion des deux sources
    merged = merge_eCO2mix_data(annual_cleaned, tempo_cleaned)

    # Étape 5 : Nettoyage post-fusion
    preprocessed = preprocess_eCO2mix_data(merged)

    # Étape 6 : Filtrage sur la période T1–T2
    mask = (preprocessed["Date"] >= pd.to_datetime(T1)) & (preprocessed["Date"] <= pd.to_datetime(T2))
    filtered = preprocessed.loc[mask].copy()

    return filtered


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique les étapes de feature engineering et nettoyage avancé sur le dataframe filtré.
    """
    df = create_date_features(df, "Date")
    df = create_hour_features(df)
    df = create_lag_features(df, target_column="Consommation", lags=[1, 2, 3])
    df = create_rolling_features(df, target_column="Consommation", window=3)
    df = preprocess_eCO2mix_data_engineered(df)

    # Séparer les features de la cible
    X, _ = split_features_target(df, target="Consommation")
    return X


def scale_data(X: pd.DataFrame) -> pd.DataFrame:
    """
    Applique le modèle Scaler loggé dans MLflow pour transformer X.
    """
    scaler = load_model_by_alias("Scaler_standard", "prod")
    X_scaled = scaler.predict(X)
    return pd.DataFrame(X_scaled, columns=X.columns)


def predict_with_model(X_scaled: pd.DataFrame) -> list:
    """
    Applique le modèle XGBoost loggé dans MLflow pour prédire les valeurs cibles.
    """
    model = load_model_by_alias("EnergyForecastModel_xgboost", "prod")
    y_pred = model.predict(X_scaled)
    return y_pred.tolist()
