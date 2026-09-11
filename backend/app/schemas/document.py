from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_type: str = "autre"
    period_label: Optional[str] = None
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    uploaded_at: datetime
