from datetime import datetime, timedelta, timezone

def get_kst_now():
    """Returns the current datetime in Korea Standard Time (UTC+9)."""
    return datetime.now(timezone(timedelta(hours=9)))

def get_kst_now_naive():
    """Returns the current datetime in Korea Standard Time (UTC+9) but as a naive datetime object
    for SQLAlchemy compatibility if needed.
    """
    return datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None)

def make_naive_kst(dt: datetime) -> datetime:
    """Converts an aware or naive datetime to a naive KST datetime."""
    if not dt:
        return datetime.min
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except (ValueError, TypeError):
            return datetime.min

    if dt.tzinfo is not None:
        # Convert aware to KST (+9) and strip
        kst = timezone(timedelta(hours=9))
        return dt.astimezone(kst).replace(tzinfo=None)
    
    # If already naive, assume it's already in the target timezone or handle as is
    return dt

