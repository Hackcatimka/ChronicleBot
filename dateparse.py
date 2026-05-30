import re
from datetime import date

_MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

_MONTHS_EN = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_MONTHS_EN_PAT = "|".join(sorted(_MONTHS_EN.keys(), key=len, reverse=True))
_MONTHS_RU_PAT = "|".join(_MONTHS_RU.keys())


def _make(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _resolve(d: date | None, today: date, has_year: bool) -> date | None:
    if d is None:
        return None
    if d > today and not has_year:
        d = _make(d.year - 1, d.month, d.day)
    if d is None or d > today:
        return None
    return d


def extract_win_date(text: str, today: date) -> date | None:
    lower = text.lower()

    # DD.MM.YYYY or DD/MM/YYYY
    for m in re.finditer(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b", text):
        d = _make(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        if d and d <= today:
            return d

    # DD.MM or DD/MM — require 2-digit month to avoid matching "5.5 km" etc.
    for m in re.finditer(r"\b(\d{1,2})[./](\d{2})\b", text):
        day, month = int(m.group(1)), int(m.group(2))
        if not (1 <= month <= 12 and 1 <= day <= 31):
            continue
        d = _resolve(_make(today.year, month, day), today, False)
        if d:
            return d

    # "29 мая" / "29 мая 2026"
    for m in re.finditer(rf"\b(\d{{1,2}})\s+({_MONTHS_RU_PAT})(?:\s+(\d{{4}}))?\b", lower):
        month = _MONTHS_RU[m.group(2)]
        year = int(m.group(3)) if m.group(3) else today.year
        d = _resolve(_make(year, month, int(m.group(1))), today, bool(m.group(3)))
        if d:
            return d

    # "29 May" / "May 29"
    for m in re.finditer(rf"\b(\d{{1,2}})\s+({_MONTHS_EN_PAT})(?:\s+(\d{{4}}))?\b", lower):
        month = _MONTHS_EN[m.group(2)]
        year = int(m.group(3)) if m.group(3) else today.year
        d = _resolve(_make(year, month, int(m.group(1))), today, bool(m.group(3)))
        if d:
            return d

    for m in re.finditer(rf"\b({_MONTHS_EN_PAT})\s+(\d{{1,2}})(?:\s+(\d{{4}}))?\b", lower):
        month = _MONTHS_EN[m.group(1)]
        year = int(m.group(3)) if m.group(3) else today.year
        d = _resolve(_make(year, month, int(m.group(2))), today, bool(m.group(3)))
        if d:
            return d

    return None
