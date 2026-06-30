from typing import Any, Dict

class LocationNormalizer:
    """
    Standardizes location dicts into city, region, and ISO-3166 alpha-2 country.
    """
    COUNTRY_MAP = {
        "united states": "US", "united states of america": "US", "usa": "US", "us": "US",
        "india": "IN", "ind": "IN", "in": "IN",
        "united kingdom": "GB", "uk": "GB", "great britain": "GB", "gb": "GB",
        "germany": "DE", "deutschland": "DE", "de": "DE",
        "canada": "CA", "can": "CA", "ca": "CA",
        "singapore": "SG", "sg": "SG",
        "australia": "AU", "aus": "AU", "au": "AU",
        "france": "FR", "fr": "FR",
        "japan": "JP", "jp": "JP"
    }

    @staticmethod
    def normalize(location_raw: Dict[str, Any]) -> Dict[str, Any]:
        if not location_raw:
            return {"city": None, "region": None, "country": None}

        city = location_raw.get("city")
        region = location_raw.get("region")
        country = location_raw.get("country")

        # Standardize country to ISO-3166 Alpha-2
        norm_country = None
        if country:
            country_clean = country.strip().lower()
            norm_country = LocationNormalizer.COUNTRY_MAP.get(country_clean)
            if not norm_country:
                # If it's already a 2-character country code, keep it capitalized
                if len(country_clean) == 2 and country_clean.isalpha():
                    norm_country = country_clean.upper()
                else:
                    norm_country = country.strip()

        # Clean city & region
        norm_city = city.strip().title() if city else None
        norm_region = region.strip().title() if region else None

        return {
            "city": norm_city,
            "region": norm_region,
            "country": norm_country
        }

