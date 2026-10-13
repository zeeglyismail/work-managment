import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class LoginIn(BaseModel):
    username: str
    password: str


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = "#4f46e5"
    archived: bool = False

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @field_validator("color")
    @classmethod
    def check_color(cls, v: str) -> str:
        if not HEX_COLOR.match(v):
            raise ValueError("color must look like #RRGGBB")
        return v.lower()


class ProjectOut(BaseModel):
    id: int
    name: str
    color: str
    archived: bool


class EntryIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = Field(default="", max_length=5000)
    project_id: int | None = None
    started_at: datetime
    ended_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v

    @field_validator("started_at", "ended_at")
    @classmethod
    def naive(cls, v: datetime | None) -> datetime | None:
        # Times are local wall-clock; drop any offset the client sent.
        return v.replace(tzinfo=None, second=0, microsecond=0) if v else v

    @model_validator(mode="after")
    def check_order(self):
        if self.ended_at is not None and self.ended_at <= self.started_at:
            raise ValueError("end time must be after start time")
        return self


class TimerStartIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = Field(default="", max_length=5000)
    project_id: int | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v


class EntryOut(BaseModel):
    id: int
    title: str
    notes: str
    project_id: int | None
    project_name: str | None
    project_color: str | None
    started_at: datetime
    ended_at: datetime | None
    minutes: int
    running: bool


def month_param(value: str) -> str:
    if not MONTH.match(value):
        raise ValueError("month must be YYYY-MM")
    return value
