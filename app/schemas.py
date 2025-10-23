from pydantic import BaseModel
from datetime import date

class PeriodInput(BaseModel):
    T1: date
    T2: date

class PredictionOutput(BaseModel):
    prediction: list
