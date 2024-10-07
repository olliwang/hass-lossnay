"""Platform for fan integration."""
from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)

from typing import Any, Optional

import adafruit_mcp4725
import busio
import board

from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Blueair fans from config entry."""
    async_add_entities([LossnayFan()])

async def async_remove_entry(hass, entry):
    """Handle removal of an entry."""
    # Perform necessary cleanup actions
    if DOMAIN in hass.data:
        del hass.data[DOMAIN]

class LossnayFan(FanEntity):
    """Controls Fan."""

    def __init__(self):
        """Initialize the temperature sensor."""
        i2c = busio.I2C(board.SCL, board.SDA)
        self._dac = adafruit_mcp4725.MCP4725(i2c)

        self._is_on = False
        self._max_speed = 4
        self._name = "Lossnay Ventilation"
        self._percentage = None
        self._speed_step = 100 / self._max_speed
        self._unique_id = "lossnay_ventilation"

    async def async_set_percentage(self, percentage: int) -> None:
        """Sets fan speed percentage."""
        self._percentage = percentage
        self.update_fan_speed()
        self._is_on = (percentage > 0)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the fan off."""
        self._is_on = False
        self._percentage = None
        self.async_write_ha_state()

    async def async_turn_on(self, percentage, preset_mode, **kwargs: Any):
        self._is_on = True

        if percentage is not None:
            self._percentage = percentage
        elif self._percentage is None:
            self._percentage = 25

        self.async_write_ha_state()

    @property
    def is_on(self) -> int:
        return self._is_on

    @property
    def name(self):
        """Return the name of the fan."""
        return self._name

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        if self._percentage is None:
            self._percentage = self._speed_step
        return self._percentage

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return self._max_speed

    @property
    def supported_features(self):
        """Flag supported features."""
        return FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

    @property
    def unique_id(self):
        """Return the unique ID of the fan."""
        return self._unique_id

    def update_fan_speed(self):
        half_speed_step = self._speed_step / 2
        speed = 0
        percentage = 0
        while speed < self._max_speed:
            if abs(self.percentage - percentage) <= half_speed_step:
                break
            percentage += self._speed_step
            speed += 1

        self._percentage = percentage

        SPEED_DAC_VALUES = (0, 0.2, 0.4, 0.6, 0.9)
        self._dac.normalized_value = SPEED_DAC_VALUES[speed]
