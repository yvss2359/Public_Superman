import mlflow.pyfunc
import os
from dotenv import load_dotenv

load_dotenv()

def load_model_by_alias(model_name: str, alias: str = "prod"):
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    mlflow.set_tracking_uri(tracking_uri)
    model_uri = f"models:/{model_name}@{alias}"
    return mlflow.pyfunc.load_model(model_uri)
