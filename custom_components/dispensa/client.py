"""Read Dispensa's local, read-only Home Assistant endpoint."""
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
