from repositories import likes_repo, media_repo, premium_repo, profile_repo, schema


def init_db() -> None:
    schema.init_schema()


def delete_profile(telegram_id: int) -> bool:
    deleted = profile_repo.delete_profile(telegram_id)
    media_repo.clear_media(telegram_id)
    return deleted


def normalize_city(city: str) -> str:
    return profile_repo.normalize_city(city)


def add_profile(telegram_id: int, username: str, name: str, age: int, city: str,
                gender: str, looking_for: str, description: str) -> None:
    profile_repo.add_profile(telegram_id, username, name, age, city, gender, looking_for, description)


def get_profile(telegram_id: int) -> tuple | None:
    return profile_repo.get_profile(telegram_id)


def deactivate_profile(telegram_id: int) -> None:
    profile_repo.deactivate_profile(telegram_id)


def activate_profile(telegram_id: int) -> None:
    profile_repo.activate_profile(telegram_id)


def update_description(telegram_id: int, description: str) -> None:
    profile_repo.update_description(telegram_id, description)


def update_language(telegram_id: int, language: str) -> None:
    profile_repo.update_language(telegram_id, language)


def update_username(telegram_id: int, username: str) -> None:
    profile_repo.update_username(telegram_id, username)


def add_media(profile_id: int, file_id: str, media_type: str) -> bool:
    return media_repo.add_media(profile_id, file_id, media_type)


def clear_media(profile_id: int) -> None:
    media_repo.clear_media(profile_id)


def get_media(profile_id: int) -> list:
    return media_repo.get_media(profile_id)


def update_media(profile_id: int, media_list: list) -> None:
    media_repo.update_media(profile_id, media_list)


def add_like(from_user: int, to_user: int, action: str) -> None:
    likes_repo.add_like(from_user, to_user, action)


def check_match(user1: int, user2: int) -> bool:
    return likes_repo.check_match(user1, user2)


def get_who_liked_me(telegram_id: int) -> list:
    return likes_repo.get_who_liked_me(telegram_id)


def delete_like(from_user: int, to_user: int) -> None:
    likes_repo.delete_like(from_user, to_user)


def get_next_profile(telegram_id: int) -> tuple | None:
    return profile_repo.get_next_profile(telegram_id)


def get_lang(telegram_id: int) -> str:
    return profile_repo.get_lang(telegram_id)


def activate_premium(telegram_id: int, days: int) -> None:
    premium_repo.activate_premium(telegram_id, days)


def check_premium(telegram_id: int) -> bool:
    return premium_repo.check_premium(telegram_id)


def get_all_active_users() -> list[tuple]:
    return profile_repo.get_all_active_users()


def check_and_increment_views(telegram_id: int) -> bool:
    return profile_repo.check_and_increment_views(telegram_id)
