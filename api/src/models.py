from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MeasurementIn(BaseModel):
    time: datetime = Field(description="UTC 时间戳")
    source: str = Field(description="数据源标识")
    parameter: str = Field(description="参数名，例如 IMF_Bz, Kp")
    value: float = Field(description="数值")
    quality: Optional[int] = Field(default=None, description="质量标记，可选")


class IngestResponse(BaseModel):
    stored_raw: int
    stored_min1: int


class QueryRequest(BaseModel):
    source: str
    parameter: str
    start: datetime
    end: datetime
    series: Literal["raw", "min1"] = "raw"


class MeasurementOut(BaseModel):
    time: datetime
    source: str
    parameter: str
    value: float
    quality: Optional[int] = None


