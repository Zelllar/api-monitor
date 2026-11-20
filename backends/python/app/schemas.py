from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from pydantic.alias_generators import to_camel


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class MonitorCreate(APIModel):
    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl
    interval_seconds: int = Field(gt=0)


class MonitorUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    url: HttpUrl | None = None
    interval_seconds: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class MonitorResponse(APIModel):
    id: int
    name: str
    url: str
    interval_seconds: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class CheckResultResponse(APIModel):
    id: int
    status: str
    status_code: int | None
    response_time_ms: int | None
    error_message: str | None
    checked_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class CheckResultCreateResponse(CheckResultResponse):
    pass