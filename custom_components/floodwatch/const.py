"""Stałe dla integracji floodwatch.

Źródło danych: https://monitoring.prospect.pl/ (RWD Prospect - system monitoringu
powodziowego). Wartości pobierane z endpointu JSON:

    <base>/data.php?station_values=all

gdzie <base> to ścieżka odcinka rzeki (np. /app/biala/tarnow).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "floodwatch"

# Domyślny interwał odświeżania [sekundy]
DEFAULT_SCAN_INTERVAL: Final[int] = 300

MIN_SCAN_INTERVAL: Final[int] = 60

# Adres serwera i wzorzec ścieżki obszaru
BASE_URL: Final[str] = "https://monitoring.prospect.pl"

# Endpoint listy obszarów (strona główna) - używany do zbudowania opcji config flow
MAIN_INDEX_URL: Final[str] = BASE_URL + "/"

# Wzorce stanów
STATE_NORMAL: Final[str] = "normalny"
STATE_OSTRZEGAW_CZY: Final[str] = "ostrzegawczy"
STATE_ALARMOWY: Final[str] = "alarmowy"

# Konfiguracja (klucze w entry.data)
CONF_REGION: Final[str] = "region"
CONF_REGION_NAME: Final[str] = "region_name"
CONF_SCAN_INTERVAL: Final[str] = "scan_interval"

# Stałe użyte w config_flow (matcher dla menu obszarów na stronie głównej)
REGION_LINK_RE: Final[str] = r'href="(/app/[^"]+)/[^"]*?(?:pomiarowa\.php\?stacja=|\.php")'

# Współrzędne / metadane z API — atrybuty sensorów
ATTR_WARTOSC: Final[str] = "wartosc"
ATTR_CZAS: Final[str] = "czas"
ATTR_MIEJSCE: Final[str] = "miejsce"
ATTR_LAT: Final[str] = "szer_geo"
ATTR_LON: Final[str] = "dl_geo"
ATTR_OSTRZEG: Final[str] = "p_ostrzegawczy"
ATTR_ALARM: Final[str] = "p_alarmowy"
ATTR_PUNKTY: Final[str] = "punkty"

# Nazwy sensorów (wzorzec po kodzie stacji)
SENSOR_LEVEL: Final[str] = "poziom"
SENSOR_STATE: Final[str] = "stan"
BINARY_WARNING: Final[str] = "ostrzegawczy"
BINARY_ALARM: Final[str] = "alarmowy"

# Atrybuty wymagane by uznać rekord stacji za kompletny
REQUIRED_KEYS: Final[tuple[str, ...]] = ("id_ppwr", "wartosc", "czas", "miejsce")


def derive_stan(
    level: float | None,
    prog_ostrzegawczy: float | None,
    prog_alarmowy: float | None,
) -> str | None:
    """Wyprowadza stan stacji z poziomu i progów (None gdy brak poziomu).

    Kolejność sprawdzeń: alarmowy > ostrzegawczy > normalny.
    """
    if level is None:
        return None
    if prog_alarmowy is not None and level >= prog_alarmowy:
        return STATE_ALARMOWY
    if prog_ostrzegawczy is not None and level >= prog_ostrzegawczy:
        return STATE_OSTRZEGAW_CZY
    return STATE_NORMAL