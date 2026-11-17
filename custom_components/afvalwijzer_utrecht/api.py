"""Tiny client for Burgerportaal, the backend of the Afvalwijzer Utrecht app."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import time

import aiohttp

from .const import ORGANISATION_ID, fraction_key

# Public Firebase web key of the Burgerportaal app (anonymous sign-in).
API_KEY = "AIzaSyA6NkRqJypTfP-cjWzrZNFJzPUbBaGjOdk"
TOKEN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key={API_KEY}"
BASE = "https://europe-west3-burgerportaal-production.cloudfunctions.net/exposed"
# Requests without a browser-like User-Agent get 403.
HEADERS = {"User-Agent": "Mozilla/5.0 (Home Assistant afvalwijzer_utrecht)"}
TIMEOUT = aiohttp.ClientTimeout(total=30)


class ApiError(Exception):
    """Could not reach or read Burgerportaal."""


@dataclass(frozen=True)
class Pickup:
    day: date
    fraction: str  # our key, e.g. "gft"
    code: str  # raw API code, e.g. "GFT"
    description: str


class AfvalApi:
    def __init__(self, session: aiohttp.ClientSession, org: str = ORGANISATION_ID) -> None:
        self._session = session
        self._org = org
        self._token_value: str | None = None
        self._token_until = 0.0

    async def _get(self, url: str, method: str = "GET", **kw):
        try:
            async with self._session.request(
                method, url, headers={**HEADERS, **kw.pop("headers", {})}, timeout=TIMEOUT, **kw
            ) as r:
                if r.status >= 400:
                    raise ApiError(f"{r.status} from {url.split('?')[0]}")
                return await r.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ApiError(str(err)) from err

    async def _token(self) -> str:
        # Firebase ID tokens live 1 hour; reuse within that window.
        if self._token_value is None or time.monotonic() > self._token_until:
            data = await self._get(TOKEN_URL, "POST", json={"returnSecureToken": True})
            self._token_value = data["idToken"]
            self._token_until = time.monotonic() + int(data.get("expiresIn", 3600)) - 300
        return self._token_value

    async def addresses(self, postcode: str, house_number: int) -> list[dict]:
        token = await self._token()
        return await self._get(
            f"{BASE}/organisations/{self._org}/address",
            params={"zipcode": postcode, "housenumber": str(house_number)},
            headers={"authorization": token},
        ) or []

    async def calendar(self, address_id: str) -> list[Pickup]:
        token = await self._token()
        rows = await self._get(
            f"{BASE}/organisations/{self._org}/address/{address_id}/calendar",
            headers={"authorization": token},
        ) or []
        out = {
            Pickup(
                day=date.fromisoformat(r["collectionDate"][:10]),
                fraction=fraction_key(r["fraction"]),
                code=r["fraction"],
                description=(r.get("placementPeriod") or r.get("placementDescription") or "").strip(),
            )
            for r in rows
        }
        return sorted(out, key=lambda p: (p.day, p.fraction))


def clean_postcode(value: str) -> str:
    return "".join(value.split()).upper()


def address_title(a: dict) -> str:
    return f"{a.get('street', '')} {a.get('housenumber', '')}{a.get('addition') or ''}".strip()
