from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class InvitationCreate(BaseModel):
    email: EmailStr
    name: str
    client_id: Optional[int] = None


class InvitationCreateOut(BaseModel):
    token: str
    invitation_url: str


class InvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    token: str
    email: EmailStr
    name: str
    client_id: Optional[int] = None
    created_at: datetime
    used: bool
