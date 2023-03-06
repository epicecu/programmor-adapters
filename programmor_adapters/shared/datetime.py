from datetime import datetime


def diff_ms(now: datetime, then: datetime) -> int:
    return round((now - then).total_seconds()*1000)
