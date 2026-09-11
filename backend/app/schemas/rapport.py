from datetime import date

from pydantic import BaseModel

from app.schemas.dashboard import NiveauConso
from app.schemas.intervention import InterventionOut


class RapportOut(BaseModel):
    client_id: int
    client_nom: str
    periode_debut: date
    periode_fin: date
    n1: NiveauConso
    n2: NiveauConso
    n3: NiveauConso
    heures_supp_minutes: int
    interventions: list[InterventionOut]


class PeriodeResumeOut(BaseModel):
    periode_id: str
    periode_debut: date
    periode_fin: date
    n1: NiveauConso
    n2: NiveauConso
    n3: NiveauConso
    heures_supp_minutes: int
