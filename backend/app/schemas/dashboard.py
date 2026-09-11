from datetime import date
from typing import Optional

from pydantic import BaseModel


class NiveauConso(BaseModel):
    forfait_h: Optional[int]
    consomme_minutes: int
    pourcentage: Optional[float]


class ClientDashboardOut(BaseModel):
    client_id: int
    client_nom: str
    periode_debut: date
    periode_fin: date
    n1: NiveauConso
    n2: NiveauConso
    n3: NiveauConso
    alerte: bool
