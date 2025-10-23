from fastapi.testclient import TestClient
from app.main import app
from datetime import date, timedelta

client = TestClient(app)

def test_prediction_period():
    today = date.today()
    payload = {
        "T1": str(today - timedelta(days=3)),
        "T2": str(today - timedelta(days=1))
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert "prediction" in response.json()
    assert isinstance(response.json()["prediction"], list)
