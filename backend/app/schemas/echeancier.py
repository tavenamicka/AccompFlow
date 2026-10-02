from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

TypeEcheance = Literal["pack", "formation", "autre"]
StatutEcheance = Literal["attente", "paye"]


class EcheanceCreate(BaseModel):
    date_facturation: Optional[date] = None
    date_echeance: Optional[date] = None
    montant: Optional[float] = Field(default=None, ge=0)
    numero_facture: Optional[str] = Field(default=None, max_length=50)
    statut: StatutEcheance = "attente"
    date_paiement: Optional[date] = None
    note: Optional[str] = None


class EcheanceUpdate(BaseModel):
    date_facturation: Optional[date] = None
    date_echeance: Optional[date] = None
    montant: Optional[float] = Field(default=None, ge=0)
    numero_facture: Optional[str] = Field(default=None, max_length=50)
    statut: Optional[StatutEcheance] = None
    date_paiement: Optional[date] = None
    note: Optional[str] = None


class EcheanceOut(BaseModel):
    id: int
    date_facturation: Optional[date]
    date_echeance: Optional[date]
    montant: Optional[float]
    numero_facture: Optional[str]
    statut: StatutEcheance
    date_paiement: Optional[date]
    note: Optional[str]
    en_retard: bool

    model_config = {"from_attributes": True}


class EcheancierCreate(BaseModel):
    titre: str = Field(min_length=1, max_length=200)
    type_echeance: TypeEcheance = "autre"
    notes: Optional[str] = None


class EcheancierUpdate(BaseModel):
    titre: Optional[str] = Field(default=None, min_length=1, max_length=200)
    type_echeance: Optional[TypeEcheance] = None
    notes: Optional[str] = None


class EcheancierOut(BaseModel):
    id: int
    client_id: int
    titre: str
    type_echeance: TypeEcheance
    notes: Optional[str]
    echeances: list[EcheanceOut]

    model_config = {"from_attributes": True}
