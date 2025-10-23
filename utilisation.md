
# 📘 Manuel d’Exploitation – Projet Superman 🔌⚡

## 1. 🎯 Objectif

L’API **Superman** permet :
- D'effectuer des prédictions de consommation électrique sur une période donnée (`T1`, `T2`)
- De normaliser les données automatiquement
- D’utiliser un modèle hébergé sur MLflow pour générer les prédictions
- De pousser les résultats vers Kafka + sauvegarde MinIO
- De lancer automatiquement le monitoring via NannyML
- D’afficher un dashboard visuel via Streamlit

---

## 2. 🧱 Architecture globale

```
[API FastAPI] --> [Téléchargement + Prétraitement]
                --> [MLflow : Scaler + Modèle]
                --> [Kafka] + [MinIO]
                --> [Monitoring NannyML]
                --> [Dashboard Streamlit]
```

---

## 3. ⚙️ Prérequis

- Docker + Docker Compose
- `.env` correctement configuré
- Accès à Internet pour télécharger les données RTE

---

## 4. 🚀 Lancer toute la stack

```bash
docker-compose up --build
```

🟢 Cela lance :
- API FastAPI : [http://localhost:8000/docs](http://localhost:8000/docs)
- Dashboard Streamlit : [http://localhost:8501](http://localhost:8501)
- Kafka (localhost:9092)
- MinIO (localhost:9000 + console sur :9001)

---

## 5. 🧪 Exemple d’inférence

### ➤ Étape 1 : Swagger UI

🔗 [http://localhost:8000/docs](http://localhost:8000/docs)

### ➤ Étape 2 : POST /predict

```json
{
  "T1": "2024-12-01",
  "T2": "2024-12-05"
}
```

### ➤ Résultat

```json
{
  "prediction": [1234.5, 1201.3, 1222.8, ...]
}
```

---

## 6. 📊 Dashboard Streamlit

[http://localhost:8501](http://localhost:8501)

- 📈 Courbes de prédiction horodatées
- ✅ État système
- 📂 Fichier : `data/predictions.csv`

---

## 7. 📧 Alertes e-mail

- RMSE > 700 → e-mail à `ALERT_EMAIL_TO`
- Log : `data/alerts.log`

---

## 8. 📦 .env exemple

```env
MLFLOW_TRACKING_URI=https://your-mlflow-endpoint
MODEL_NAME=EnergyForecastModel_xgboost
SCALER_NAME=Scaler_standard
MODEL_STAGE=prod

KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=inference_topic

MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=predictions

ALERT_EMAIL_FROM=monitoring.ai@example.com
ALERT_EMAIL_TO=admin@example.com
ALERT_EMAIL_PASSWORD=app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

---

## 9. 📁 Fichiers importants

| Chemin | Rôle |
|--------|------|
| `app/main.py` | FastAPI |
| `app/utils.py` | Prétraitement, Kafka, MinIO |
| `monitoring/nannyml_runner.py` | RMSE Monitoring |
| `monitoring/dashboard.py` | Streamlit |
| `data/predictions.csv` | Dernières prédictions |
| `data/reference_predictions.csv` | Référence RMSE |
| `.env` | Configuration |
| `docker-compose.yml` | Services |

---

## 10. 🛠 Commandes utiles (manuelles)

| Action | Commande |
|--------|----------|
| Lancer tous les services | `docker-compose up --build` |
| Accès API | `http://localhost:8000/docs` |
| Dashboard | `streamlit run monitoring/dashboard.py` |
| Exécuter NannyML | `python monitoring/nannyml_runner.py` |

---

## 11. ✅ Bonnes pratiques

- Max 7 jours de prédiction
- Mettre à jour `reference_predictions.csv` après changement de modèle
- Vérifier les dates Swagger
- Cronjob optionnel pour NannyML

