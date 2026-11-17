"""Setup: type postcode + house number, done."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AfvalApi, ApiError, address_title, clean_postcode
from .const import (
    CONF_ADDITION,
    CONF_ADDRESS_ID,
    CONF_HOUSE_NUMBER,
    CONF_POSTCODE,
    CONF_TEXT_LANGUAGE,
    CONF_UPDATE_HOURS,
    DEFAULT_TEXT_LANGUAGE,
    DEFAULT_UPDATE_HOURS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_POSTCODE): str,
        vol.Required(CONF_HOUSE_NUMBER): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Optional(CONF_ADDITION, default=""): str,
    }
)


class AfvalConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AfvalOptionsFlow:
        return AfvalOptionsFlow()

    def __init__(self) -> None:
        self._choices: dict[str, dict] = {}
        self._input: dict[str, Any] = {}

    async def _create(self, address: dict) -> ConfigFlowResult:
        await self.async_set_unique_id(str(address["addressId"]))
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=address_title(address),
            data={
                CONF_ADDRESS_ID: str(address["addressId"]),
                CONF_POSTCODE: self._input[CONF_POSTCODE],
                CONF_HOUSE_NUMBER: self._input[CONF_HOUSE_NUMBER],
                CONF_ADDITION: address.get("addition") or "",
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            postcode = clean_postcode(user_input[CONF_POSTCODE])
            addition = user_input.get(CONF_ADDITION, "").strip().upper()
            self._input = {CONF_POSTCODE: postcode, CONF_HOUSE_NUMBER: user_input[CONF_HOUSE_NUMBER]}
            try:
                found = await AfvalApi(async_get_clientsession(self.hass)).addresses(
                    postcode, user_input[CONF_HOUSE_NUMBER]
                )
            except ApiError:
                _LOGGER.exception("Address lookup failed")
                errors["base"] = "cannot_connect"
            else:
                if not found:
                    errors["base"] = "address_not_found"
                else:
                    exact = [a for a in found if (a.get("addition") or "").upper() == addition]
                    if len(exact) == 1:
                        return await self._create(exact[0])
                    if addition and not exact:
                        errors[CONF_ADDITION] = "addition_not_found"
                    elif len(found) == 1 and not addition:
                        return await self._create(found[0])
                    else:
                        self._choices = {str(a["addressId"]): a for a in found}
                        return await self.async_step_choose()
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_choose(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return await self._create(self._choices[user_input[CONF_ADDRESS_ID]])
        options = {k: address_title(a) for k, a in self._choices.items()}
        return self.async_show_form(
            step_id="choose",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS_ID): vol.In(options)}),
        )


class AfvalOptionsFlow(OptionsFlow):
    """How often to fetch the calendar again (the municipality can change it)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        opts = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_HOURS,
                        default=opts.get(CONF_UPDATE_HOURS, DEFAULT_UPDATE_HOURS),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=168)),
                    vol.Required(
                        CONF_TEXT_LANGUAGE,
                        default=opts.get(CONF_TEXT_LANGUAGE, DEFAULT_TEXT_LANGUAGE),
                    ): vol.In({"nl": "Nederlands", "en": "English"}),
                }
            ),
        )
