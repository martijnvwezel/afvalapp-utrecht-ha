"""Constants for Afvalwijzer Utrecht."""

DOMAIN = "afvalwijzer_utrecht"

# Gemeente Utrecht in Burgerportaal (the backend of the "Afvalwijzer Utrecht" app).
ORGANISATION_ID = "452048812597339479"

CONF_POSTCODE = "postcode"
CONF_HOUSE_NUMBER = "house_number"
CONF_ADDITION = "addition"
CONF_ADDRESS_ID = "address_id"

CONF_UPDATE_HOURS = "update_hours"
DEFAULT_UPDATE_HOURS = 6
CONF_TEXT_LANGUAGE = "text_language"
DEFAULT_TEXT_LANGUAGE = "nl"
# Reminder the evening before a pickup (never on the day itself).
CONF_REMINDER_TARGETS = "reminder_targets"  # notify services, e.g. "mobile_app_pixel"
CONF_REMINDER_TIME = "reminder_time"
DEFAULT_REMINDER_TIME = "18:00:00"

# API fraction code -> our key (also the translation key of the per-type sensor).
FRACTIONS = {
    "GFT": "gft", "GFTE": "gft", "GFT+E": "gft",
    "PK": "paper", "OPK": "paper", "PAPIER": "paper",
    "REST": "residual", "RESTAFVAL": "residual",
    "PMD": "pmd", "PBD": "pmd",
    "TEXTIEL": "textile",
    "KCA": "chemical",
    "GROF": "bulky", "GROFVUIL": "bulky",
    "KERST": "christmas_tree", "KERSTBOOM": "christmas_tree",
}

# Text used in the "today / tomorrow / notice" sensors and calendar events.
LABELS = {
    "nl": {
        "gft": "Groente, fruit en tuin", "paper": "Papier", "residual": "Restafval",
        "pmd": "Plastic (PMD)", "textile": "Textiel", "chemical": "Klein chemisch afval",
        "bulky": "Grofvuil", "christmas_tree": "Kerstbomen",
        "_none": "Geen", "_today": "Vandaag", "_tomorrow": "Morgen",
        "_reminder_title": "Afval morgen", "_reminder": "Zet de container vanavond buiten.",
    },
    "en": {
        "gft": "Organic waste (GFT)", "paper": "Paper", "residual": "Residual waste",
        "pmd": "Plastic (PMD)", "textile": "Textiles", "chemical": "Small chemical waste",
        "bulky": "Bulky waste", "christmas_tree": "Christmas trees",
        "_none": "None", "_today": "Today", "_tomorrow": "Tomorrow",
        "_reminder_title": "Bin day tomorrow", "_reminder": "Put the bin out tonight.",
    },
}

ICONS = {
    "gft": "mdi:leaf", "paper": "mdi:newspaper-variant-outline", "residual": "mdi:trash-can",
    "pmd": "mdi:recycle", "textile": "mdi:tshirt-crew", "chemical": "mdi:flask",
    "bulky": "mdi:sofa", "christmas_tree": "mdi:pine-tree",
}


def fraction_key(code: str) -> str:
    return FRACTIONS.get(code.upper(), code.lower())


def label(lang: str, key: str) -> str:
    table = LABELS["nl" if lang.lower().startswith("nl") else "en"]
    return table.get(key, key.upper())
