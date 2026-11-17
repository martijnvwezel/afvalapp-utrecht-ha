# Afvalapp Utrecht for Home Assistant (unofficial)

> [!IMPORTANT]
> **Uses the new Utrechtse Afvalapp, not the old Afvalwijzer.**
> Since 2026 the municipality of Utrecht has its own *Afvalapp*. The old *Afvalwijzer*
> (mijnafvalwijzer.nl) stops for Utrecht at the end of 2026. Integrations built on the
> Afvalwijzer will stop working then; this one reads the same data as the new app, so it keeps working.

> Community project. Not made, endorsed or supported by Gemeente Utrecht.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=martijnvwezel&repository=afvalapp-utrecht-ha&category=integration)

See **when your bin is collected** in Home Assistant, for every address in the
municipality of **Utrecht** (also Leidsche Rijn, Vleuten and De Meern).
You only need your **postcode and house number**. No account.

<p>
  <img src="docs/sensors.png" width="300" alt="Waste sensors in Home Assistant">
  &nbsp;
  <img src="docs/settings.png" width="300" alt="Settings: reminder on your phone">
</p>

## What you get

One device **Waste** (*Afval*) per address, with:

| Entity | Example | Use it for |
|---|---|---|
| **Notice** | `Vandaag: Papier · Morgen: Groente, fruit en tuin` | One line on your dashboard |
| **Today** | `Papier` or `Geen` | What goes out today |
| **Tomorrow** | `Groente, fruit en tuin` or `Geen` | What goes out tomorrow |
| **Pickup today or tomorrow** | `on` / `off` | Show a card only when it matters |
| **Next pickup** | `2026-11-20` (+ `days_until`) | Date of the next pickup, any type |
| **Next waste type** | `Papier` | What the next pickup is |
| **Organic waste (GFT)**, **Paper**, ... | `2026-11-24` (+ `days_until`, `upcoming`, `instructions`) | Next date per waste type (only the types collected at your address) |
| **Pickup days** (calendar) | all-day events `Papier`, `Groente, fruit en tuin` | HA calendar, automations |
| **Reminder** (setting) | push *"Morgen: Papier. Zet de container vanavond buiten."* | Your phone, the evening before |

Entity ids follow your Home Assistant language, e.g. `sensor.waste_notice` (English)
or `sensor.afval_melding` (Dutch).

## Install

1. Install [HACS](https://hacs.xyz) if you don't have it.
2. Click **Open in HACS** above (or HACS → ⋮ → *Custom repositories* →
   `https://github.com/martijnvwezel/afvalapp-utrecht-ha`, type *Integration*), then *Download*.
3. Restart Home Assistant.
4. Settings → Devices & services → **Add integration** → *Afvalapp Utrecht*.
5. Type your postcode and house number (and addition like `A` if you have one). Done.

No HACS? Copy `custom_components/afvalapp_utrecht` into `/config/custom_components/` and restart.

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

## Settings: reminder on your phone

Get a push message **the evening before** a pickup day, e.g.
*"Morgen: Papier. Zet de container vanavond buiten."* Never on the pickup day itself.

1. Settings → Devices & services → **Afvalapp Utrecht**.
2. Click the **gear** (⚙) next to your address.
3. Under **Send a reminder the evening before to**, tick your phone.
   (Your phone shows up here once the Home Assistant Companion app is installed and logged in.)
4. Set **Time of the reminder** (default 18:00).
5. **Submit**. Done.

<img src="docs/settings.png" width="320" alt="Settings dialog">

The same dialog has two more settings:

- **Language of the waste names**: Dutch (default, e.g. `Papier`, `Vandaag: ...`) or English.
  Used in Today, Tomorrow, Notice, the calendar and the reminder.
- **Check for calendar changes every ... hours** (default 6): the municipality sometimes
  moves pickup days (holidays, new routes); this is how often Home Assistant checks.
  "Today" and "Tomorrow" always switch at midnight, whatever you pick here.

## Nederlands, kort

Deze integratie gebruikt de gegevens van de **nieuwe Utrechtse Afvalapp**, niet van de oude
Afvalwijzer (mijnafvalwijzer.nl). Die stopt eind 2026 voor Utrecht; deze integratie blijft werken.


Installeer via HACS, herstart, en kies *Instellingen → Apparaten & diensten →
Integratie toevoegen → Afvalapp Utrecht*. Vul postcode en huisnummer in. Je krijgt een
agenda met ophaaldagen, sensoren *Vandaag*, *Morgen* en *Melding*
(`Vandaag: Papier · Morgen: Groente, fruit en tuin`), en een aan/uit-sensor
*Ophalen vandaag of morgen* om een kaart alleen te tonen als het nodig is.

**Herinnering op je telefoon** (de avond van tevoren, nooit op de ophaaldag zelf):
*Instellingen → Apparaten & diensten → Afvalapp Utrecht → tandwiel (⚙) bij je adres* →
vink je telefoon aan bij *Herinnering de avond van tevoren sturen naar*, kies de tijd
(standaard 18:00) → *Verzenden*. Je telefoon moet de Home Assistant-app hebben.

## License

[MIT](LICENSE)
