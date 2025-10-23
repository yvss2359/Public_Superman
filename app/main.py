from fastapi import FastAPI, HTTPException
from app.schemas import PeriodInput, PredictionOutput
from app.utils import (
    get_data_between_dates,
    preprocess_data,
    scale_data,
    predict_with_model,
    upload_predictions_to_minio
)
from datetime import timedelta
import pandas as pd
import os
import subprocess
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

MAX_DAYS = 7  # Durée maximale autorisée

@app.post("/predict", response_model=PredictionOutput)
def predict_period(period: PeriodInput):
    # Validation de la période
    delta = (period.T2 - period.T1).days
    if delta <= 0:
        raise HTTPException(status_code=400, detail="T2 doit être après T1.")
    if delta > MAX_DAYS:
        raise HTTPException(status_code=400, detail=f"Période trop longue. Max autorisé : {MAX_DAYS} jours.")

    # Pipeline de traitement
    raw_data = get_data_between_dates(period.T1, period.T2)
    X = preprocess_data(raw_data)
    X_scaled = scale_data(X)
    predictions = predict_with_model(X_scaled)

    # Générer les timestamps correspondants
    timestamps = pd.date_range(start=period.T1, periods=len(predictions), freq="H")
    df_result = pd.DataFrame({"timestamp": timestamps, "y_pred": predictions})

    # Enregistrement local
    os.makedirs("data", exist_ok=True)
    local_path = "data/predictions.csv"
    df_result.to_csv(local_path, index=False)

    # Envoi à MinIO
    upload_predictions_to_minio(local_path, "predictions.csv")

    # Appel automatique à NannyML pour contrôle
    try:
        subprocess.run(["python", "monitoring/nannyml_runner.py"], check=True)
        logger.info("✅ NannyML runner exécuté avec succès.")
    except Exception as e:
        logger.warning(f"⚠️ Erreur lors de l’exécution de NannyML: {e}")

    return {"prediction": predictions}
