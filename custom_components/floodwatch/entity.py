"""Wspólne elementy encji dynamicznych dla integracji floodwatch."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ALARM,
    ATTR_CZAS,
    ATTR_LAT,
    ATTR_LON,
    ATTR_MIEJSCE,
    ATTR_OSTRZEG,
    DOMAIN,
)
from .coordinator import FloodwatchCoordinator

#: Zwraca listę encji dla nowo wykrytej stacji.
StationEntityFactory = Callable[[str], list[CoordinatorEntity]]


def _stacja_atrybuty(data: dict[str, Any]) -> dict[str, Any]:
    """Wspólne atrybuty stacji (bez wartości None)."""
    attrs: dict[str, Any] = {
        ATTR_CZAS: data.get(ATTR_CZAS),
        ATTR_MIEJSCE: data.get(ATTR_MIEJSCE),
        ATTR_LAT: data.get(ATTR_LAT),
        ATTR_LON: data.get(ATTR_LON),
        ATTR_OSTRZEG: data.get(ATTR_OSTRZEG),
        ATTR_ALARM: data.get(ATTR_ALARM),
    }
    return {k: v for k, v in attrs.items() if v is not None}


class FloodwatchStationEntity(CoordinatorEntity[FloodwatchCoordinator]):
    """Baza encji powiązanej z jedną stacją pomiarową.

    Podklasy ustawiają: ``_label`` (nazwa encji) i ``_suffix`` (unikalny
    przyrostek, np. ``poziom``) oraz implementują ``native_value``/``is_on``.
    """

    _label: str = ""
    _suffix: str = ""

    def __init__(self, coordinator: FloodwatchCoordinator, station_id: str) -> None:
        super().__init__(coordinator)
        self._station_id = station_id

    @property
    def _station_data(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._station_id, {})

    @property
    def _station_name(self) -> str:
        return self._station_data.get(ATTR_MIEJSCE) or self._station_id

    @property
    def name(self) -> str:
        return f"{self._station_name} - {self._label}"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.coordinator.region}_{self._station_id}_{self._suffix}"

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and (
            self._station_id in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _stacja_atrybuty(self._station_data)


def async_setup_dynamic_stations(
    coordinator: FloodwatchCoordinator,
    async_add_entities,
    entity_factory: StationEntityFactory,
) -> None:
    """Tworzy encje dla wszystkich stacji, także pojawiających się później.

    ``entity_factory(station_id)`` zwraca listę encji dla jednej stacji.
    Wołać z ``async_setup_entry`` platformy.
    """
    added_ids: set[str] = set()

    def _build_for(station_id: str):
        added_ids.add(station_id)
        return entity_factory(station_id)

    def _update_stations() -> None:
        new_ids = [sid for sid in coordinator.data if sid not in added_ids]
        if new_ids:
            async_add_entities(
                [entity for sid in new_ids for entity in _build_for(sid)]
            )

    _update_stations()
    coordinator.async_add_listener(_update_stations)
