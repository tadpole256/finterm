from datetime import datetime
from typing import Literal

from pydantic import BaseModel

FreshnessStatus = Literal["fresh", "stale", "degraded"]


class FreshnessEnvelope(BaseModel):
    source_provider: str
    as_of: datetime
    delay_seconds: int
    freshness_status: FreshnessStatus
    is_stale: bool
