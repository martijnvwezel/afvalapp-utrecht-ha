from datetime import date
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.afvalwijzer_utrecht.api import ApiError, Pickup
from custom_components.afvalwijzer_utrecht.const import DOMAIN

API = "custom_components.afvalwijzer_utrecht.api.AfvalApi"
ADDR = {"addressId": "238127830377612675", "addition": "A", "zipcode": "3454HK",
        "street": "Rijksstraatweg", "city": "De Meern", "housenumber": 118}
ADDR_B = {**ADDR, "addressId": "999", "addition": "B"}
import pytest


@pytest.fixture(autouse=True)
def mock_calendar():
    with patch(f"{API}.calendar", AsyncMock(return_value=PICKUPS)) as m:
        yield m


TXT = "Zet uw GFT voor 8.00 uur buiten."
PICKUPS = [
    Pickup(date(2026, 11, 17), "gft", "GFT", TXT),
    Pickup(date(2026, 11, 20), "paper", "PK", ""),
    Pickup(date(2026, 11, 24), "gft", "GFT", TXT),
]


async def _flow(hass, found, data):
    with patch(f"{API}.addresses", AsyncMock(return_value=found)):
        r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        assert r["type"] is FlowResultType.FORM
        return await hass.config_entries.flow.async_configure(r["flow_id"], data)


async def test_flow_exact_addition(hass):
    r = await _flow(hass, [ADDR, ADDR_B], {"postcode": "3454 hk", "house_number": "118", "addition": "a"})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    assert r["title"] == "Rijksstraatweg 118A"
    assert r["data"] == {"address_id": ADDR["addressId"], "postcode": "3454HK",
                         "house_number": 118, "addition": "A"}


async def test_flow_choose_when_several(hass):
    r = await _flow(hass, [ADDR, ADDR_B], {"postcode": "3454HK", "house_number": 118})
    assert r["step_id"] == "choose"
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"address_id": "999"})
    assert r["type"] is FlowResultType.CREATE_ENTRY and r["title"] == "Rijksstraatweg 118B"


async def test_flow_errors(hass):
    r = await _flow(hass, [], {"postcode": "1234AB", "house_number": 1})
    assert r["errors"] == {"base": "address_not_found"}
    r = await _flow(hass, [ADDR], {"postcode": "3454HK", "house_number": 118, "addition": "Z"})
    assert r["errors"] == {"addition": "addition_not_found"}
    with patch(f"{API}.addresses", AsyncMock(side_effect=ApiError("x"))):
        r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        r = await hass.config_entries.flow.async_configure(r["flow_id"], {"postcode": "3454HK", "house_number": 118})
    assert r["errors"] == {"base": "cannot_connect"}


async def _setup(hass, lang="nl"):
    hass.config.language = "en-GB"  # text follows the option, not the HA language
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    entry = MockConfigEntry(domain=DOMAIN, unique_id=ADDR["addressId"], title="Rijksstraatweg 118A",
                            data={"address_id": ADDR["addressId"], "postcode": "3454HK",
                                  "house_number": 118, "addition": "A"},
                            options={} if lang == "nl" else {"text_language": lang})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _by_suffix(hass, domain, unique_suffix):
    from homeassistant.helpers import entity_registry as er
    reg = er.async_get(hass)
    eid = next(e.entity_id for e in reg.entities.values()
               if e.domain == domain and e.unique_id.endswith(unique_suffix))
    return hass.states.get(eid)


async def test_entities_and_midnight(hass, freezer):
    freezer.move_to("2026-11-16 12:00:00+01:00")
    await _setup(hass)
    s = lambda d, k: _by_suffix(hass, d, k)
    assert s("sensor", "_today").state == "Geen"
    assert s("sensor", "_tomorrow").state == "Groente, fruit en tuin"
    assert s("sensor", "_notice").state == "Morgen: Groente, fruit en tuin"
    assert s("binary_sensor", "_today_or_tomorrow").state == "on"
    assert s("sensor", "_next_date").state == "2026-11-17"
    assert s("sensor", "_next_type").state == "Groente, fruit en tuin"
    assert s("sensor", "_type_paper").state == "2026-11-20"
    assert s("sensor", "_type_gft").attributes["instructions"] == TXT
    cal = s("calendar", "_calendar")
    assert cal.attributes["message"] == "Groente, fruit en tuin"

    # Day rolls over: states follow without new data.
    freezer.move_to("2026-11-18 00:00:10+01:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert s("sensor", "_today").state == "Geen"
    assert s("sensor", "_tomorrow").state == "Geen"
    assert s("binary_sensor", "_today_or_tomorrow").state == "off"
    assert s("sensor", "_next_type").state == "Papier"

    freezer.move_to("2026-11-20 08:00:00+01:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert s("sensor", "_notice").state == "Vandaag: Papier"


async def test_english_and_calendar_events(hass, freezer):
    freezer.move_to("2026-11-17 07:00:00+01:00")
    await _setup(hass, "en")
    assert _by_suffix(hass, "sensor", "_notice").state == "Today: Organic waste (GFT)"
    cal = _by_suffix(hass, "calendar", "_calendar").entity_id
    r = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": cal, "start_date_time": "2026-11-01 00:00:00", "end_date_time": "2026-11-30 00:00:00"},
        blocking=True, return_response=True)
    events = r[cal]["events"]
    assert events[0]["start"] == "2026-11-17" and events[0]["description"] == TXT
    assert [e["summary"] for e in events] == ["Organic waste (GFT)", "Paper", "Organic waste (GFT)"]


async def test_options_interval(hass):
    entry = await _setup(hass)
    r = await hass.config_entries.options.async_init(entry.entry_id)
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"update_hours": 1, "text_language": "en"})
    await hass.async_block_till_done()
    assert r["type"] is FlowResultType.CREATE_ENTRY
    assert entry.runtime_data.update_interval.total_seconds() == 3600
    assert entry.runtime_data.lang == "en"


async def test_reminder_evening_before_only(hass, freezer):
    from homeassistant.core import ServiceCall
    calls: list[ServiceCall] = []

    async def fake(call):
        calls.append(call)

    hass.services.async_register("notify", "mobile_app_phone", fake)
    freezer.move_to("2026-11-16 12:00:00+01:00")
    entry = await _setup(hass)
    r = await hass.config_entries.options.async_init(entry.entry_id)
    r = await hass.config_entries.options.async_configure(
        r["flow_id"], {"update_hours": 6, "text_language": "nl",
                       "reminder_targets": ["mobile_app_phone"], "reminder_time": "18:00:00"})
    await hass.async_block_till_done()

    # Evening before GFT (17 nov): one push.
    freezer.move_to("2026-11-16 18:00:00+01:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data == {"title": "Afval morgen",
                             "message": "Morgen: Groente, fruit en tuin. Zet de container vanavond buiten."}

    # The pickup day itself (nothing tomorrow): no push.
    freezer.move_to("2026-11-17 18:00:00+01:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(calls) == 1

    # Evening before paper (20 nov): push again.
    freezer.move_to("2026-11-19 18:00:00+01:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(calls) == 2 and "Papier" in calls[1].data["message"]


async def test_options_show_phone_names(hass):
    from custom_components.afvalwijzer_utrecht.config_flow import _notify_options

    async def noop(call):
        return None

    MockConfigEntry(domain="mobile_app", title="Pixel 11", data={"device_name": "Pixel 11"}).add_to_hass(hass)
    hass.services.async_register("notify", "mobile_app_pixel_11", noop)
    hass.services.async_register("notify", "persistent_notification", noop)
    hass.services.async_register("notify", "send_message", noop)
    opts = _notify_options(hass)
    assert [o["value"] for o in opts] == ["mobile_app_pixel_11", "persistent_notification"]
    assert opts[0]["label"] == "📱 Pixel 11"
