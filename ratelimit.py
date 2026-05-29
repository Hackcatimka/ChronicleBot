from collections import defaultdict, deque
from datetime import datetime, timezone

_WINDOW = 60   # seconds
_LIMIT = 20    # messages per window per user

_buckets: dict[int, deque] = defaultdict(deque)


def check(user_tg_id: int) -> bool:
    """Return True if allowed, False if rate-limited."""
    now = datetime.now(timezone.utc).timestamp()
    q = _buckets[user_tg_id]
    while q and now - q[0] > _WINDOW:
        q.popleft()
    if len(q) >= _LIMIT:
        return False
    q.append(now)
    return True
