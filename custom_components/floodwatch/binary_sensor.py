"""Platforma binary_sensor (ostrzegawczy, alarmowy) dla integracji floodwatch."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_ALARM, ATTR_OSTRZEG, DOMAIN, SENSOR_LEVEL
from .coordinator import FloodwatchCoordinator
from .entity import FloodwatchStationEntity, async_setup_dynamic_stations


class FloodwatchBinarySensor(FloodwatchStationEntity, BinarySensorEntity):
    """Baza binary sensora stacji: ON gdy poziom >= próg.

    Podklasy ustawiają ``_threshold_attr`` (klucz progu/pola w danych stacji).
    """

    _threshold_attr: str = ""

    @property
    def is_on(self) -> bool | None:
        data = self._station_data
        level = data.get(SENSOR_LEVEL)
        prog = data.get(self._threshold_attr)
        if level is None or prog is None:
            return None
        return level >= prog


class FloodwatchOstrzegawczySensor(FloodwatchBinarySensor):
    """Próg ostrzegawczy przekroczony."""

    _label = "Ostrzegawczy"
    _suffix = "ostrzegawczy"
    _threshold_attr = ATTR_OSTRZEG

    _attr_icon = "mdi:alert"


class FloodwatchAlarmowySensor(FloodwatchBinarySensor):
    """Próg alarmowy przekroczony."""

    _label = "Alarmowy"
    _suffix = "alarmowy"
    _threshold_attr = ATTR_ALARM

    _attr_icon = "mdi:alert-octagon"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Utworzenie binary sensorów dla stacji (także tych pojawiających się później)."""

    coordinator: FloodwatchCoordinator = hass.data[DOMAIN][entry.entry_id]

    def _factory(station_id: str) -> list[FloodwatchStationEntity]:
        return [
            FloodwatchOstrzegawczySensor(coordinator, station_id),
            FloodwatchAlarmowySensor(coordinator, station_id),
        ]

    async_setup_dynamic_stations(coordinator, async_add_entities, _factory)