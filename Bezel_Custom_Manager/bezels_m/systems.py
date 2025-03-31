systems = [
    {"name": "A2600", "id": 0, "extensions": ["cfg"]},
    {"name": "A5200", "id": 40, "extensions": ["cfg"]},
    {"name": "A7800", "id": 0, "extensions": ["cfg"]},
    {"name": "A800", "id": 0, "extensions": ["cfg"]},
    {"name": "AMIGA","id": 64,"extensions": ["cfg",]},
    {"name": "ATARIST","id": 42,"extensions": ["cfg"]},
    {"name": "ATOMISWAVE", "id": 53, "extensions": ["cfg"]},
    {"name": "C64","id": 66,"extensions": ["cfg"]},
    {"name": "CPS1", "id": 6, "extensions": ["cfg"]},
    {"name": "CPS2", "id": 7, "extensions": ["cfg"]},
    {"name": "CPS3", "id": 8, "extensions": ["cfg"]},
    {"name": "DOS","id": 135,"extensions": ["cfg"]},
    {"name": "DREAMCAST", "id": 23, "extensions": ["cfg"]},
    {"name": "EASYRPG", "id": 0, "extensions": ["cfg"]},
    {"name": "FBNEO", "id": 142, "extensions": ["cfg"]},
    {"name": "FC","id": 3,"extensions": ["cfg"]},
    {"name": "FDS", "id": 0, "extensions": ["cfg"]},
    {"name": "GB", "id": 9, "extensions": ["cfg"]},
    {"name": "GBA", "id": 12, "extensions": ["cfg"]},
    {"name": "GBC", "id": 10, "extensions": ["cfg"]},
    {"name": "GG", "id": 21, "extensions": ["cfg"]},
    {"name": "GW", "id": 52, "extensions": ["cfg"]},
    {"name": "HBMAME", "id": 0, "extensions": ["cfg"]},
    {"name": "LYNX", "id": 28, "extensions": ["cfg"]},
    {"name": "MAME", "id": 75, "extensions": ["cfg"]},
    {"name": "MD", "id": 1, "extensions": ["cfg"]},
    {"name": "MDCD","id": 20,"extensions": ["cfg"]},
    {"name": "MSX","id": 113,"extensions": ["cfg"]},
    {"name": "N64", "id": 14, "extensions": ["cfg"]},
    {"name": "NAOMI", "id": 56, "extensions": ["cfg"]},
    {"name": "NEOGEO", "id": 0, "extensions": ["cfg"]},
    {"name": "NGP", "id": 82, "extensions": ["cfg"]},
    {"name": "ONS", "id": 0, "extensions": ["cfg"]},
    {"name": "PCE", "id": 105, "extensions": ["cfg"]},
    {"name": "PCECD","id": 114,"extensions": ["cfg"]},
    {"name": "PGM2", "id": 0, "extensions": ["cfg"]},
    {"name": "PICO", "id": 234, "extensions": ["cfg"]},
    {"name": "POKE", "id": 211, "extensions": ["cfg"]},
    {"name": "PS","id": 57,"extensions": ["cfg",]},
    {"name": "PSP","id": 61,"extensions": ["cfg"]},
    {"name": "SATURN","id": 22,"extensions": ["cfg"]},
    {"name": "SCUMMVM", "id": 123, "extensions": ["cfg"]},
    {"name": "SEGA32X","id": 19,"extensions": ["cfg",]},
    {"name": "SFC", "id": 4, "extensions": ["cfg"]},
    {"name": "SMS", "id": 2, "extensions": ["cfg"]},
    {"name": "VARCADE", "id": 0, "extensions": ["cfg"]},
    {"name": "VB", "id": 11, "extensions": ["cfg"]},
    {"name": "VIC20", "id": 0, "extensions": ["cfg"]},
    {"name": "WS", "id": 45, "extensions": ["cfg"]},
]


def get_system_id(system_name: str) -> int:
    for system in systems:
        if system["name"] == system_name:
            return system["id"]
    return -1


def get_system_extension(system_name: str) -> list[str]:
    for system in systems:
        if system["name"] == system_name:
            return system["extensions"]
    return []
