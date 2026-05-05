from geopy.geocoders import Nominatim
from geopy.adapters import AioHTTPAdapter


async def normalize_city(city: str) -> str:
    try:
        async with Nominatim(user_agent="anketabot", adapter_factory=AioHTTPAdapter) as geolocator:
            location = await geolocator.geocode(city, language="ru", addressdetails=True)
            if location:
                addr = location.raw.get("address", {})
                # city > town > village — от крупного к мелкому
                name = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county")
                if name:
                    return name
    except Exception:
        pass
    return city.strip().title()
