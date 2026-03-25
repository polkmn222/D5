from datetime import datetime, timedelta, timezone

def get_kst_now():
    """Returns the current datetime in Korea Standard Time (UTC+9)."""
    return datetime.now(timezone(timedelta(hours=9)))

def get_kst_now_naive():
    """Returns the current datetime in Korea Standard Time (UTC+9) but as a naive datetime object
    for SQLAlchemy compatibility if needed.
    """
    return datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None)
