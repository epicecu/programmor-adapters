from datetime import datetime


def diff_ms(now: datetime, then: datetime, precision: int = None) -> int:
    return round((now - then).total_seconds()*1000, precision)
