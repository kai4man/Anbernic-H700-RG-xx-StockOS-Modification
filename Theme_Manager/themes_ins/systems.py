systems = [
    {"name": "themes", "id": 0, "extensions": ["zip"]},
    {"name": "bootlogo", "id": 1, "extensions": ["bmp"]}
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
