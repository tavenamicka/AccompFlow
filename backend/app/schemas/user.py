from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr

Role = Literal["owner", "staff", "client"]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str | None = None
    role: Role = "client"


class UserWithClientOut(UserOut):
    # Fiche client liée, si elle existe (None pour un compte orphelin,
    # généralement issu d'une invitation créée avant qu'elle ne crée
    # automatiquement la fiche).
    client_id: int | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
