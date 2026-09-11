from typing import Literal

from pydantic import BaseModel


class AlerteOut(BaseModel):
    client_id: int
    client_nom: str
    niveau: Literal["N1", "N2"]
    pourcentage: float
