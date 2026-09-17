"""DataUpdateCoordinator dla integracji floodwatch."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_ALARM,
    ATTR_CZAS,
    ATTR_LAT,
    ATTR_LON,
    ATTR_MIEJSCE,
    ATTR_OSTRZEG,
    ATTR_PUNKTY,
    BASE_URL,
    CONF_REGION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    SENSOR_LEVEL,
)

_LOGGER = logging.getLogger(__name__)


class FloodwatchCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Koordynator danych dla jednego obszaru (wpisu konfiguracji)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Inicjalizacja: budowa URL na podstawie regionu z configu."""
        region = entry.data.get(CONF_REGION, "").strip("/")
        if not region:
            raise ValueError("Brak konfiguracji regionu we wpisie")

        self._entry = entry
        self._region = region
        # region przechowywany jest bez prefiksu "app/" (np. biala/tarnow)
        self.url = f"{BASE_URL}/app/{region}/data.php?station_values=all"

        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        if isinstance(interval, str) and interval.isdigit():
            interval = int(interval)
        interval = max(MIN_SCAN_INTERVAL, int(interval))

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{region}",
            update_interval=timedelta(seconds=interval),
        )

    @property
    def region(self) -> str:
        """Ścieżka obszaru (np. biala/tarnow)."""
        return self._region

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Pobranie i przetworzenie aktualnych pomiarów."""
        try:
            async with async_timeout.timeout(10):
                session = async_get_clientsession(self.hass)
                async with session.get(self.url) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status} z {self.url}")
                    text = await resp.text()
                    # API zwraca UTF-8 z BOM; json.loads nie toleruje BOM-a.
                    payload = json.loads(text.lstrip("\ufeff"))
        except (asyncio.TimeoutError, aiohttp.ClientError, UpdateFailed) as err:
            raise UpdateFailed(f"Nie udało się pobrać danych: {err}") from err

        if not isinstance(payload, list):
            raise UpdateFailed(
                f"Nieoczekiwany format odpowiedzi (typ: {type(payload).__name__})"
            )

        stations: dict[str, dict[str, Any]] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            stacja_id = item.get("id_ppwr")
            if not stacja_id:
                continue
            level = _to_float(item.get("wartosc"))
            czas = _to_str(item.get("czas"))
            if level is None and czas is None:
                continue

            stations[str(stacja_id)] = {
                SENSOR_LEVEL: level,
                ATTR_CZAS: czas,
                ATTR_MIEJSCE: _to_str(item.get("miejsce")),
                ATTR_LAT: _to_float(item.get("szer_geo")),
                ATTR_LON: _to_float(item.get("dl_geo")),
                ATTR_OSTRZEG: _to_float(item.get("p_ostrzegawczy")),
                ATTR_ALARM: _to_float(item.get("p_alarmowy")),
                ATTR_PUNKTY: item.get("punkty"),
            }

        if not stations:
            raise UpdateFailed("Brak stacji w odpowiedzi `station_values=all`")

        return stations


def _to_float(value: Any) -> float | None:
    """Bezpieczna konwersja do float (None gdy brak/zły typ)."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_str(value: Any) -> str | None:
    """Bezpieczna konwersja do str."""
    if value is None:
        return None
    return str(value)