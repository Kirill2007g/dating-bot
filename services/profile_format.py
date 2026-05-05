def build_profile_caption(name: str, age: int, city: str, description: str) -> str:
    return f"{name}, {age}, {city}" + (f"\n{description}" if description else "")


def build_profile_caption_from_row(profile: tuple) -> str:
    _, _, name, age, city, _, _, description, _, _, _, _, _ = profile
    return build_profile_caption(name, age, city, description)
