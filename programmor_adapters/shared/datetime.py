from datetime import datetime
from typing import Optional


def diff_ms(now: datetime, then: datetime, precision: Optional[int] = None) -> float:
    return round((now - then).total_seconds()*1000, precision)
