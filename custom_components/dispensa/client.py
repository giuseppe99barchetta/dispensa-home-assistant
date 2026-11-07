"""Read Dispensa's local Home Assistant snapshot and record meal outcomes (never stock)."""
from urllib.parse import urlsplit

import aiohttp


class DispensaError(Exception):
    """Connection or response error."""


def normalize_url(value):
    if not isinstance(value, str):
        raise ValueError("Indirizzo non valido")
    url = value.strip().rstrip("/")
    parsed = urlsplit(url)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment):
        raise ValueError("Indirizzo non valido")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Porta non valida") from exc
    return url


class DispensaClient:
    def __init__(self, session, url):
        self.session = session
        self.url = normalize_url(url)

    async def snapshot(self):
        try:
            async with self.session.get(self.url + "/api/home-assistant", allow_redirects=False,
                                        timeout=aiohttp.ClientTimeout(total=20)) as response:
                response.raise_for_status()
                data = await response.json()
            if (not isinstance(data, dict) or data.get("integration") != "dispensa" or data.get("version") != 1
                    or not isinstance(data.get("meals"), dict)):
                raise DispensaError("Risposta Dispensa non valida")
            return data
        except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
            raise DispensaError("Impossibile leggere Dispensa") from exc

    async def set_eaten(self, date, meal, eaten, rating=None, tags=None, note=None):
        """Record a meal as eaten (or not) and optionally rate it. Dispensa never touches Grocy stock here."""
        body = {"date": date, "meal": meal, "eaten": eaten}
        for key, value in (("rating", rating), ("tags", tags), ("note", note)):
            if value is not None:
                body[key] = value
        try:
            async with self.session.post(self.url + "/api/meal/eaten", json=body, allow_redirects=False,
                                         timeout=aiohttp.ClientTimeout(total=20)) as response:
                try:
                    data = await response.json()
                except (aiohttp.ClientError, ValueError):
                    data = {}
                if response.status >= 400:
                    detail = data.get("error") if isinstance(data, dict) else None
                    raise DispensaError(detail or "Dispensa ha rifiutato la richiesta (%s)" % response.status)
                return data
        except (aiohttp.ClientError, TimeoutError) as exc:
            raise DispensaError("Impossibile contattare Dispensa") from exc
