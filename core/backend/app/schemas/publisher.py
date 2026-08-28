from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PublisherBase(BaseModel):
    id:           str = Field(min_length=1)
    name:         str = Field(min_length=1)
    type:         str = "LOCAL_DEVELOPMENT"
    public_key:   Optional[str] = None
    trust_status: str = "UNTRUSTED"
    extra:        Optional[dict] = None


class PublisherCreate(PublisherBase):
    pass


class PublisherRead(PublisherBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
