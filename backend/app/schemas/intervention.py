import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Niveau = Literal["N1", "N2", "N3"]


class InterventionBlocIn(BaseModel):
    niveau: Niveau
    duree_minutes: int = Field(gt=0)
    description: str = Field(min_length=1)


class InterventionCreate(BaseModel):
    client_id: int
    date_intervention: date
    blocs: list[InterventionBlocIn] = Field(min_length=1)


class InterventionUpdate(BaseModel):
    client_id: Optional[int] = None
    date_intervention: Optional[date] = None
    niveau: Optional[Niveau] = None
    duree_minutes: Optional[int] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, min_length=1)


class InterventionOut(BaseModel):
    id: int
    client_id: int
    user_id: Optional[int]
    date_intervention: date
    niveau: Niveau
    duree_minutes: int
    description: str
    groupe_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
