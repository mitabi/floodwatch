# floodwatch

[![Current release](https://img.shields.io/github/v/release/mitabi/floodwatch.svg?include_prereleases&label=Current%20release)](https://github.com/mitabi/floodwatch/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![downloads](https://img.shields.io/github/downloads/mitabi/floodwatch/total?label=Total%20downloads)](https://github.com/mitabi/floodwatch)

Integracja Home Assistant monitorująca stany rzek w czasie rzeczywistym na
podstawie danych z systemu monitoringu powodziowego
[RWD Prospect](https://monitoring.prospect.pl/).

Dla każdego wybranego obszaru (rzeka/baza, np. *Biała – Tarnów*, *Wisłoka – Jasło*)
integracja tworzy zestaw dynamicznych sensorów dla każdej stacji pomiarowej.

## Funkcje

- **Konfiguracja przez interfejs HA** — kreator pobiera listę obszarów ze strony
  producenta i podaje je w rozwijanej liście; możliwość ręcznego podania ścieżki
  obszaru (np. `biala/tarnow`) jako fallback.
- **Sensory poziomu** — `poziom` w centymetrach, klasa `measurement`.
- **Sensor stanu** — wyprowadzany z progów: `normalny` / `ostrzegawczy` / `alarmowy`.
- **Binary sensory progowe** — `ostrzegawczy` i `alarmowy` (ON gdy poziom
  przekroczy próg).
- **Dynamiczne stacje** — nowe stacje pojawiające się w danych są dodawane
  automatycznie, bez restartu HA.
- **Odzyskiwanie poawaryjne** — przy chwilowej przerwie sieci/strony koordynator
  sam wznawia odpytywanie (domyślnie co 5 minut; zmiana w opcjach integracji,
  min. 60 s).

## Wymagania

- Home Assistant **2024.6 lub nowszy** (Python ≥ 3.12)
- [HACS](https://hacs.xyz/) (jeśli instalujesz przez HACS)

## Instalacja

### Przez HACS (zalecane)

Dodaj repozytorium jako repozytorium **custom**:

1. HACS → trzy kropki (menu) → *Custom repositories*
2. Repozytorium: `https://github.com/mitabi/floodwatch`
3. Kategoria: **Integration**
4. Zainstaluj **Floodwatch** z listy integracji HACS i **zrestartuj Home Assistant**.

### Ręcznie

Skopiuj katalog `custom_components/floodwatch/` do
`config/custom_components/floodwatch/` w swojej instalacji HA, a następnie
zrestartuj Home Assistant.

## Konfiguracja

Cała konfiguracja odbywa się przez UI — nie ma potrzeby edycji YAML:

1. **Ustawienia → Urządzenia i usługi → Dodaj integrację → Floodwatch**.
2. Wybierz obszar z listy (lub podaj ścieżkę ręcznie, np. `biala/tarnow`).
3. Po dodaniu encje pojawią się automatycznie dla wszystkich stacji obszaru.

Możesz dodać więcej niż jeden obszar (np. osobne wpisy dla *Wisłoki – Jasło*
i *Wisłoki – Dębica*).

### Opcje

W *Konfiguruj* (ikona zębatki na kafelku integracji) możesz zmienić **interwał
odświeżania** (sekundy, min. 60).

## Encje

Dla każdej stacji (np. o kodzie `TABI`) w obszarze `biala/tarnow`:

| Encja | Typ | Znaczenie |
|---|---|---|
| `sensor.floodwatch_biala_tarnow_tabi_poziom` | sensor | Poziom wody [cm] |
| `sensor.floodwatch_biala_tarnow_tabi_stan` | sensor | Stan: `normalny` / `ostrzegawczy` / `alarmowy` |
| `binary_sensor.floodwatch_biala_tarnow_tabi_ostrzegawczy` | binary_sensor | ON gdy poziom ≥ próg ostrzegawczy |
| `binary_sensor.floodwatch_biala_tarnow_tabi_alarmowy` | binary_sensor | ON gdy poziom ≥ próg alarmowy |

Atrybuty (m.in. czas pomiaru, miejsce, współrzędne geograficzne, wartości
progowe) dostępne są na sensorze `poziom`.

## Źródło danych

- [monitoring.prospect.pl](https://monitoring.prospect.pl/) (RWD Prospect)
- Endpoint: `<base>/data.php?station_values=all`
- Pomiar: poziom wody i progi ostrzegawczy/alarmowy w centymetrach.
- Odświeżanie danych po stronie systemu Prospect nie jest gwarantowane
  w czasie rzeczywistym — interwał odpytywania dobierany jest pod własne
  potrzeby (domyślnie 300 s).

## Development

Środowisko deweloperskie oparte o [uv](https://docs.astral.sh/uv/):

```sh
uv sync          # utworzenie środowiska z narzędziami dev (ruff, mypy, pytest)
uv run ruff check custom_components/
uv run mypy custom_components/
uv run pytest
```

Repozytorium celowo **nie** zawiera pakietu `homeassistant` w locku (HA
dostarcza własne, przypięte zależności). Do type-checków przeciwko pełnemu HA:

```sh
uv venv .venv-ha
uv pip install --python .venv-ha homeassistant
```

## Wersje i wydania

Wersja jest trzymana w `manifest.json` (oraz `pyproject.toml`) i wydawana przez
[semantic-release](https://github.com/semantic-release/semantic-release)
automatycznie na gałęzi `main` (commit w formacie conventional, np. `feat:` /
`fix:`). Utrzymuj wersje w `manifest.json` i `pyproject.toml` w spójności.

## Licencja

[MIT](LICENSE)