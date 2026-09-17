# Changelog

Wszystkie istotne zmiany w integracji floodwatch.

Format oparty o [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/).
Historia wydań: [GitHub Releases](https://github.com/mitabi/floodwatch/releases).

> Plik jest automatycznie rozszerzany przez semantic-release przy każdym
> wydaniu (sekcja per wersja). Poniższa sekcja `[Unreleased]` opisuje stan
> repozytorium przed pierwszym opublikowanym wydaniem.

## [Unreleased]

### Dodane

- **Integracja floodwatch dla Home Assistant** — monitoring powodziowy RWD
  Prospect ([prospect.pl](https://monitoring.prospect.pl/)):
  - config flow z listą obszarów (rzeka/baza) i fallbackiem ręcznym,
  - koordynator danych z automatycznym odzyskiwaniem po przerwie sieci,
  - sensory `poziom` (cm) i `stan` (normalny/ostrzegawczy/alarmowy),
  - binary sensory `ostrzegawczy` i `alarmowy` (przekroczenie progów),
  - dynamiczne dodawanie nowych stacji bez restartu HA,
  - opcja interwału odświeżania (min. 60 s).
- **Gotowość do publikacji w HACS**: `hacs.json` (zip_release), README
  z instrukcją instalacji i konfiguracji, `LICENSE` (MIT).
- **Środowisko deweloperskie** oparte o uv (`pyproject.toml`, `uv.lock`):
  ruff, mypy, pytest; konfiguracja wersjonowania (semantic-release).
- **CI** — workflowy GitHub Actions: walidacja HACS + hassfest oraz
  automatyczny release na gałęzi `main`.

### Poprawione

- **"Invalid handler specified"** w interfejsie konfiguracji — brakowało pliku
  `config_flow.py` (manifest deklarował `config_flow: true`, a handler nie
  istniał).
- **Zrywanie połączenia z HA** — uszkodzony `coordinator.py` (błędy składni
  i błędne wcięcia powodowały pad setupu i brak odzyskiwania); obsługa BOM
  UTF-8 w odpowiedzi API (inyaczej `json.loads` padał na realnych danych).

### Zmienione

- Vjałose indywidualne: tylko dokumentacja i narzędzia — bez wpływu na
  działanie integracji.