# Afvalwijzer Utrecht for Home Assistant (unofficial)

> Community project. Not made, endorsed or supported by Gemeente Utrecht.
> Uses the same data as the official *Afvalwijzer Utrecht* app.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=martijnvwezel&repository=afvalwijzer-utrecht-ha&category=integration)

See **when your bin is collected** in Home Assistant, for every address in the
municipality of **Utrecht** (also Leidsche Rijn, Vleuten and De Meern).
You only need your **postcode and house number**. No account.

You get:

- a **calendar** with all pickup days (shows up in the HA calendar, and works with automations)
- **Today** and **Tomorrow**: e.g. `Papier` or `Geen`
- **Notice**: one line for your dashboard, e.g. `Vandaag: Papier · Morgen: Groente, fruit en tuin`
- **Pickup today or tomorrow**: on/off, to show a card only when it matters
- **Next pickup** (date) and **Next waste type** (text)
- one date sensor per waste type (GFT, Papier, ...) with the official instructions

<img src="docs/sensors.png" width="320" alt="Waste sensors in Home Assistant">

## Install

1. Install [HACS](https://hacs.xyz) if you don't have it.
2. Click **Open in HACS** above (or HACS → ⋮ → *Custom repositories* →
   `https://github.com/martijnvwezel/afvalwijzer-utrecht-ha`, type *Integration*), then *Download*.
3. Restart Home Assistant.
4. Settings → Devices & services → **Add integration** → *Afvalwijzer Utrecht*.
5. Type your postcode and house number (and addition like `A` if you have one). Done.

No HACS? Copy `custom_components/afvalwijzer_utrecht` into `/config/custom_components/` and restart.

## Show a card only when the bin goes out

```yaml
type: conditional
conditions:
  - condition: state
    entity: binary_sensor.afval_ophalen_vandaag_of_morgen
    state: "on"
card:
  type: tile
  entity: sensor.afval_melding
  icon: mdi:delete-alert
```

(Entity ids depend on your Home Assistant language. With Home Assistant in English they are
`binary_sensor.waste_pickup_today_or_tomorrow` and `sensor.waste_notice`.)

## Reminder the evening before

```yaml
triggers:
  - trigger: time
    at: "20:00:00"
conditions:
  - condition: not
    conditions:
      - condition: state
        entity_id: sensor.afval_morgen
        state: Geen
actions:
  - action: notify.notify
    data:
      message: "Morgen: {{ states('sensor.afval_morgen') }} aan de straat"
```

## Updates

The municipality can change the calendar (holidays, new routes). The integration
fetches it again every **6 hours**. Change it via *Devices & services →
Afvalwijzer Utrecht → Configure* (1 to 168 hours). "Today" and "Tomorrow" switch at midnight.

The text in the sensors and calendar is **Dutch** by default (`Papier`, `Vandaag: ...`).
Switch it to English in the same *Configure* dialog.

## Nederlands, kort

Installeer via HACS, herstart, en kies *Instellingen → Apparaten & diensten →
Integratie toevoegen → Afvalwijzer Utrecht*. Vul postcode en huisnummer in. Je krijgt een
agenda met ophaaldagen, sensoren *Vandaag*, *Morgen* en *Melding*
(`Vandaag: Papier · Morgen: Groente, fruit en tuin`), en een aan/uit-sensor
*Ophalen vandaag of morgen* om een kaart alleen te tonen als het nodig is.
