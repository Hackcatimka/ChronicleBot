"""Smoke tests for pure-function critical paths."""
from datetime import date


# ---------------------------------------------------------------------------
# dateparse — moment date extraction
# ---------------------------------------------------------------------------

from dateparse import extract_win_date

TODAY = date(2026, 6, 1)


def test_dateparse_full_dot():
    assert extract_win_date("finished 25.12.2025", TODAY) == date(2025, 12, 25)


def test_dateparse_full_slash():
    assert extract_win_date("25/12/2025 done it", TODAY) == date(2025, 12, 25)


def test_dateparse_short_two_digit_month():
    # 15.05 → today is June 1 2026, May 15 is in the past this year
    assert extract_win_date("ran 10k on 15.05", TODAY) == date(2026, 5, 15)


def test_dateparse_short_rolls_back_year():
    # 10.07 → July 10, which is in the future relative to June 1 2026
    # → should roll back to July 10 2025
    assert extract_win_date("camping trip 10.07", TODAY) == date(2025, 7, 10)


def test_dateparse_false_positive_distance():
    # "5.5 km" must NOT be parsed as a date (single-digit month)
    assert extract_win_date("ran 5.5 km", TODAY) is None


def test_dateparse_russian_with_year():
    assert extract_win_date("29 мая 2026 — сдал проект", TODAY) == date(2026, 5, 29)


def test_dateparse_russian_no_year_past():
    # "3 апреля" — April 3 is in the past relative to June 1 2026
    assert extract_win_date("3 апреля сдал экзамен", TODAY) == date(2026, 4, 3)


def test_dateparse_russian_no_year_rolls_back():
    # "15 июля" — July 15 is in the future → roll back to 2025
    assert extract_win_date("15 июля поехал в горы", TODAY) == date(2025, 7, 15)


def test_dateparse_english_month_day():
    assert extract_win_date("May 29 2026 shipped it", TODAY) == date(2026, 5, 29)


def test_dateparse_english_day_month():
    assert extract_win_date("29 May — big win", TODAY) == date(2026, 5, 29)


def test_dateparse_invalid_date():
    # February 31 does not exist
    assert extract_win_date("31.02.2025", TODAY) is None


def test_dateparse_future_explicit_year():
    # Explicit future year must be rejected
    assert extract_win_date("01.01.2030", TODAY) is None


def test_dateparse_no_date():
    assert extract_win_date("just a normal entry with no date", TODAY) is None


# ---------------------------------------------------------------------------
# ratelimit — sliding-window AI rate limiter
# ---------------------------------------------------------------------------

import importlib
import ratelimit as _rl_mod


def _fresh_check():
    """Reload module to get a clean bucket state for this test."""
    import importlib
    mod = importlib.reload(_rl_mod)
    return mod.check


def test_ratelimit_allows_first_call():
    check = _fresh_check()
    assert check(1) is True


def test_ratelimit_allows_up_to_limit():
    check = _fresh_check()
    results = [check(2) for _ in range(20)]
    assert all(results)


def test_ratelimit_blocks_over_limit():
    check = _fresh_check()
    for _ in range(20):
        check(3)
    assert check(3) is False


def test_ratelimit_different_users_independent():
    check = _fresh_check()
    for _ in range(20):
        check(10)
    # user 11 is fresh — must be allowed
    assert check(11) is True


# ---------------------------------------------------------------------------
# locales — t() lookup and fallback
# ---------------------------------------------------------------------------

from locales import t


def test_locales_en_key_returns_string():
    result = t("en", "choose_language")
    assert isinstance(result, str) and len(result) > 0


def test_locales_ru_key_returns_string():
    result = t("ru", "choose_language")
    assert isinstance(result, str) and len(result) > 0


def test_locales_unknown_lang_falls_back_to_en():
    assert t("xx", "choose_language") == t("en", "choose_language")


def test_locales_missing_key_returns_key_itself():
    assert t("en", "__nonexistent_key__") == "__nonexistent_key__"


def test_locales_kwargs_interpolated():
    # Use a key that accepts kwargs — e.g. "deadline_reminder" uses {title} and {date}
    result = t("en", "deadline_reminder", title="my goal", date="2026-07-01")
    assert "my goal" in result
    assert "2026-07-01" in result


# ---------------------------------------------------------------------------
# admin — ADMIN_TG_ID loaded from config (not hardcoded)
# ---------------------------------------------------------------------------

def test_admin_tg_id_comes_from_settings():
    """Ensure admin.py no longer defines ADMIN_TG_ID as a module-level constant."""
    import importlib, types
    # We can't import admin.py without a full env, so inspect the source directly.
    import pathlib
    src = pathlib.Path(__file__).parent.parent / "handlers" / "admin.py"
    text = src.read_text(encoding="utf-8")
    assert "ADMIN_TG_ID = " not in text, "ADMIN_TG_ID must not be hardcoded in admin.py"
    assert "settings.ADMIN_TG_ID" in text, "admin.py must use settings.ADMIN_TG_ID"
