import pandas as pd
from nannyml import PerformanceEstimator
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration email (à définir dans .env)
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

# Vérifier que les fichiers existent
reference_path = "data/reference_predictions.csv"
predictions_path = "data/predictions.csv"

if not os.path.exists(reference_path) or not os.path.exists(predictions_path):
    print("❌ Données de référence ou prédictions manquantes.")
    exit(1)

# Charger les données
reference_data = pd.read_csv(reference_path)
analysis_data = pd.read_csv(predictions_path)

# Estimation de la performance (RMSE)
estimator = PerformanceEstimator(
    y_pred='y_pred',
    timestamp_column='timestamp',
    chunk_size=100,
    metric='rmse',
)

estimator.fit(reference_data)
estimated = estimator.estimate(analysis_data)

# Dernier RMSE
last_rmse = estimated['value'].iloc[-1]
print(f"\n⭐ RMSE estimé : {last_rmse:.2f}")

# Fonction d'envoi email
def send_email_alert(rmse_value: float):
    subject = "⚠️ Alerte RMSE - Superman Inference Drift"
    body = f"""Alerte automatique 🚨

Le dernier RMSE estimé dépasse le seuil de 700.

🕒 Heure : {pd.Timestamp.now()}
📈 RMSE détecté : {rmse_value:.2f}

Merci de vérifier l'intégrité du modèle en production.

— Système de monitoring Superman
"""
    msg = MIMEMultipart()
    msg['From'] = ALERT_EMAIL_FROM
    msg['To'] = ALERT_EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(ALERT_EMAIL_FROM, ALERT_EMAIL_PASSWORD)
            server.send_message(msg)
        print("📬 Alerte envoyée par e-mail.")
    except Exception as e:
        print(f"❌ Erreur envoi mail : {e}")

# Détection & alerte
if last_rmse > 700:
    print("⚠️ Alerte critique : RMSE > 700 — drift ou dégradation détectée !")
    with open("data/alerts.log", "a") as log:
        log.write(f"[ALERTE] {pd.Timestamp.now()}: RMSE={last_rmse:.2f}\n")
    send_email_alert(last_rmse)
else:
    print("✅ RMSE en-dessous du seuil acceptable.")
