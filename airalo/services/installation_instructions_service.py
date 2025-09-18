import json
import hashlib

from typing import Optional, Dict, Any
from ..config import Config
from ..constants.api_constants import ApiConstants
from ..constants.sdk_constants import SdkConstants
from ..helpers.cached import Cached
from ..resources.http_resource import HttpResource
from ..exceptions.airalo_exception import AiraloException


class InstallationInstructionsService:
    def __init__(self, config, curl: HttpResource, access_token: str):
        if not access_token:
            raise AiraloException("Invalid access token please check your credentials")

        self.config = config
        self.curl = curl
        self.access_token = access_token
        self.base_url = self.config.get_url()

    def get_instructions(self, params=None) -> Optional[Dict[str, Any]]:
        if params is None:
            params = {}

        url = self._build_url(params)

        result = Cached.get(
            lambda: self._fetch(url, params),
            self._get_key(url, params),
            SdkConstants.DEFAULT_CACHE_TTL,
        )

        if result and result["data"]:
            return result
        return None

    def _fetch(self, url, params):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept-Language": params.get("language", ""),
        }
        response = self.curl.set_headers(headers).get(url)
        result = json.loads(response)
        return result

    def _build_url(self, params):
        if "iccid" not in params:
            raise AiraloException('The parameter "iccid" is required.')

        iccid = str(params["iccid"])
        url = f"{self.base_url}{ApiConstants.SIMS_SLUG}/{iccid}/{ApiConstants.INSTRUCTIONS_SLUG}"
        return url

    def _get_key(self, url, params):
        data = (
            url
            + json.dumps(params)
            + json.dumps(self.config.get_http_headers())
            + self.access_token
        )
        return hashlib.md5(data.encode("utf-8")).hexdigest()
