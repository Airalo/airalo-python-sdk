import json
from typing import Optional, Dict, Any
from ..constants.api_constants import ApiConstants
from airalo.exceptions import AiraloException


class CompatibilityDevicesService:
    def __init__(self, config, curl, access_token: str):
        if not access_token:
            raise AiraloException("Invalid access token, please check your credentials")

        self.config = config
        self.curl = curl
        self.access_token = access_token
        self.base_url = self.config.get_url()

    def get_compatible_devices(self) -> Optional[Dict[str, Any]]:
        url = self._build_url()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        response = self.curl.set_headers(headers).get(url)
        result = json.loads(response)

        if result.get("data"):
            return result
        else:
            return None

    def _build_url(self) -> str:
        return f"{self.base_url}{ApiConstants.COMPATIBILITY_SLUG}"
