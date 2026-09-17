"""Platforma sensorów (poziom, stan) dla integracji floodwatch."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_ALARM,
    ATTR_OSTRZEG,
    DOMAIN,
    SENSOR_LEVEL,
    STATE_ALARMOWY,
    STATE_OSTRZEGAW_CZY,
    derive_stan,
)
from .coordinator import FloodwatchCoordinator
from .entity import FloodwatchStationEntity, async_setup_dynamic_stations


class FloodwatchPoziomSensor(FloodwatchStationEntity, SensorEntity):
    """Sensor poziomu wody (cm)."""

    _label = "Poziom"
    _suffix = "poziom"

    _attr_native_unit_of_measurement = "cm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:waves"

    @property
    def native_value(self) -> float | None:
        return self._station_data.get(SENSOR_LEVEL)


class FloodwatchStanSensor(FloodwatchStationEntity, SensorEntity):
    """Sensor stanu (normalny/ostrzegawczy/alarmowy), wyprowadzony z progów."""

    _label = "Stan"
    _suffix = "stan"

    _attr_icon = "mdi:water"

    @property
    def native_value(self) -> str | None:
        data = self._station_data
        return derive_stan(
            data.get(SENSOR_LEVEL),
            data.get(ATTR_OSTRZEG),
            data.get(ATTR_ALARM),
        )

    @property
    def icon(self) -> str:
        stan = self.native_value
        if stan == STATE_OSTRZEGAW_CZY:
            return "mdi:alert"
        if stan == STATE_ALARMOWY:
            return "mdi:alert-octagon"
        return "mdi:water"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Utworzenie sensorów dla stacji (także tych pojawiających się później)."""

    coordinator: FloodwatchCoordinator = hass.data[DOMAIN][entry.entry_id]

    def _factory(station_id: str) -> list[FloodwatchStationEntity]:
        return [
            FloodwatchPoziomSensor(coordinator, station_id),
            FloodwatchStanSensor(coordinator, station_id),
        ]

    async_setup_dynamic_stations(coordinator, async_add_entities, _factory)