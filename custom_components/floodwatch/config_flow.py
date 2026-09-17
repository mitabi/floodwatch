"""Config flow dla integracji floodwatch (monitoring RWD Prospect)."""

from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import (
    BASE_URL,
    CONF_REGION,
    CONF_REGION_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAIN_INDEX_URL,
    MIN_SCAN_INTERVAL,
    REGION_LINK_RE,
)

_LOGGER = logging.getLogger(__name__)

# Stała z const.py jest wzorcem tekstowym — kompilujemy do regexa.
_REGION_RE = re.compile(REGION_LINK_RE)

# Generyczne etykiety linków (mapa/wykres) — zamiast nich używamy nazwy z <h5>.
_GENERIC_LABELS = {
    "mapa obszaru",
    "zestawienie wykresów",
    "zestawienie",
    "mapa",
    "zobacz wizualizację",
}


def _link_label(html: str, match: re.Match[str]) -> str:
    """Tekst linku dla dopasowania REGION_LINK_RE (po ostatnim `>` przed `</a>`).

    Anchory zawierają przed tekstem ikony (np. ``<i class="fa ..."></i>``),
    dlatego bierzemy fragment po ostatnim tagu.
    """
    segment = html[match.end() : match.end() + 512]
    end_a = segment.find("</a>")
    if end_a != -1:
        segment = segment[:end_a]
    gt = segment.rfind(">")
    if gt == -1:
        return ""
    return segment[gt + 1 :].strip()


def _area_label(html: str, match: re.Match[str]) -> str:
    """Etykieta obszaru: tekst linku, a dla generycznych (m.in. "Mapa obszaru")
    nazwa z najbliższego ``<h5>...</h5>`` bezpośrednio przed linkiem.
    """
    label = _link_label(html, match)
    if label and label.lower() not in _GENERIC_LABELS:
        return label

    before = html[max(0, match.start() - 400) : match.start()]
    heading = re.search(r"<h5[^>]*>([^<]*)</h5>", before, re.IGNORECASE | re.DOTALL)
    if heading:
        name = heading.group(1).strip()
        if name:
            return name
    return label


class FloodwatchConfigFlow(  # type: ignore[call-arg]
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Konfiguracja integracji floodwatch przez UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Krok główny: wybór obszaru z listy (lub fallback ręczny)."""
        regions: dict[str, str] = {}
        try:
            regions = await self._async_get_regions()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("Nie udało się pobrać listy obszarów: %s", err)

        if user_input is not None and regions:
            return await self._async_create_from_region(user_input)

        if not regions:
            # Fallback: ręczne podanie ścieżki obszaru (np. biala/tarnow)
            return self.async_show_form(
                step_id="manual",
                data_schema=self._manual_schema(),
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_REGION): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=path, label=label)
                                for path, label in regions.items()
                            ],
                            mode="dropdown",
                        )
                    ),
                    vol.Optional(CONF_REGION_NAME, default=""): cv.string,
                }
            ),
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Ręczne podanie ścieżki obszaru (np. biala/tarnow)."""
        if user_input is None:
            return self.async_show_form(
                step_id="manual",
                data_schema=self._manual_schema(),
            )
        return await self._async_create_from_region(user_input)

    async def _async_create_from_region(
        self, user_input: dict[str, Any]
    ) -> config_entries.FlowResult:
        """Normalizacja ścieżki regionu i utworzenie wpisu."""
        region = str(user_input.get(CONF_REGION, "")).strip("/").removeprefix("app/")
        name = str(user_input.get(CONF_REGION_NAME) or "").strip() or region
        if not region:
            return self.async_show_form(
                step_id="manual",
                data_schema=self._manual_schema(),
                errors={CONF_REGION: "invalid_region"},
            )

        await self.async_set_unique_id(region)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=name,
            data={CONF_REGION: region, CONF_REGION_NAME: name},
        )

    async def _async_get_regions(self) -> dict[str, str]:
        """Lista obszarów {ścieżka: etykieta} pobrana ze strony głównej."""
        session = async_get_clientsession(self.hass)
        async with session.get(MAIN_INDEX_URL) as resp:
            if resp.status != 200:
                raise aiohttp.ClientError(f"HTTP {resp.status} z {MAIN_INDEX_URL}")
            html = await resp.text()

        # Normalizacja href: bezwzględne URL-e oraz brak wiodącego "/"
        html = html.replace(f'href="{BASE_URL}', 'href="')
        html = html.replace('href="app/', 'href="/app/')

        regions: dict[str, str] = {}
        for match in _REGION_RE.finditer(html):
            # Ścieżka względem /app/ (np. biala/tarnow). Pomijamy 1-segmentowe
            # ścieżki (tylko rzeka: biala, wisloka, global) — to strony wykresów
            # bez danych `station_values=all`. Pierwsza niepusta etykieta wygrywa.
            path = match.group(1).strip("/").removeprefix("app/")
            if not path or path.count("/") < 1:
                continue
            label = _area_label(html, match)
            if label:
                regions.setdefault(path, label)
            else:
                regions.setdefault(path, path)
        return regions

    @staticmethod
    def _manual_schema() -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_REGION): cv.string,
                vol.Optional(CONF_REGION_NAME, default=""): cv.string,
            }
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FloodwatchOptionsFlow:
        return FloodwatchOptionsFlow(config_entry)


class FloodwatchOptionsFlow(config_entries.OptionsFlow):
    """Opcje integracji (interwał odświeżania)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self._entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=current
                    ): vol.All(cv.positive_int, vol.Clamp(min=MIN_SCAN_INTERVAL)),
                }
            ),
        )
