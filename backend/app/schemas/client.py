from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ClientCreate(BaseModel):
    nom: str
    email: Optional[str] = None
    telephone: Optional[str] = None
    date_debut_contrat: date
    forfait_n1_h: int = 4
    forfait_n2_h: int = 3
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    nom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    date_debut_contrat: Optional[date] = None
    forfait_n1_h: Optional[int] = None
    forfait_n2_h: Optional[int] = None
    echeanciers_actif: Optional[bool] = None
    notes: Optional[str] = None


class ClientOut(BaseModel):
    id: int
    user_id: Optional[int]
    nom: str
    email: Optional[str]
    telephone: Optional[str]
    date_debut_contrat: date
    forfait_n1_h: int
    forfait_n2_h: int
    actif: bool
    echeanciers_actif: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
