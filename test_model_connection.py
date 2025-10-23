import os
import mlflow
from dotenv import load_dotenv

def test_model_loading(model_name: str, alias: str = "prod"):
    try:
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
        model_uri = f"models:/{model_name}@{alias}"
        print(f"Attempting to load model from: {model_uri}")
        model = mlflow.pyfunc.load_model(model_uri)
        print(f"✅ SUCCESS: Model '{model_name}' loaded successfully from alias '{alias}'")
    except Exception as e:
        print(f"❌ ERROR: Failed to load model '{model_name}' with alias '{alias}'\n{e}")

if __name__ == "__main__":
    load_dotenv()

    # Nom exact des modèles dans MLflow (configurable via .env)
    scaler_name = os.getenv("SCALER_NAME", "Scaler")
    prediction_model_name = os.getenv("MODEL_NAME", "EnergyForecastModel_xgboost")
    alias = os.getenv("MODEL_STAGE", "prod")

    print("=== Testing model access from MLflow ===\n")
    test_model_loading(scaler_name, alias)
    test_model_loading(prediction_model_name, alias)