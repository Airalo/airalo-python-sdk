import json
import hashlib
import re
from urllib.parse import urlencode

from airalo.resources.http_resource import HttpResource
from airalo.helpers.date_helper import DateHelper
from airalo.exceptions import AiraloException
from airalo.helpers.cached import Cached
from airalo.constants.api_constants import ApiConstants


class ExchangeRatesService:
    def __init__(self, config, curl: HttpResource, access_token: str):
        if not access_token:
            raise AiraloException("Invalid access token, please check your credentials")

        self.config = config
        self.curl = curl
        self.access_token = access_token
        self.base_url = self.config.get_url()

    def exchange_rates(self, params: dict = None):
        if params is None:
            params = {}

        self.validate_exchange_rates_request(params)
        url = self.build_url(params)

        def fetch_data():
            response = self.curl.set_headers(
                {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.access_token}",
                }
            ).get(url)
            return json.loads(response)

        result = Cached.get(fetch_data, self.get_key(url, params), 300)

        return result if result and result.get("data") else None

    def validate_exchange_rates_request(self, params: dict) -> None:
        if "date" in params and params["date"]:
            if not DateHelper.validate_date(params["date"]):
                raise AiraloException(
                    "Please enter a valid date in the format YYYY-MM-DD"
                )

        if "to" in params and params["to"]:
            if not re.match(r"^([A-Za-z]{3})(?:,([A-Za-z]{3}))*$", params["to"]):
                raise AiraloException(
                    "Please enter a comma separated list of currency codes. Each code must have 3 letters"
                )

    def build_url(self, params: dict) -> str:
        query_params = {}

        if "date" in params and params["date"]:
            query_params["date"] = params["date"]
        if "to" in params and params["to"]:
            query_params["to"] = params["to"]

        return f"{self.base_url}{ApiConstants.EXCHANGE_RATES_SLUG}?{urlencode(query_params)}"

    def get_key(self, url: str, params: dict) -> str:
        headers = self.config.get_http_headers()
        raw_key = f"{url}{json.dumps(params, sort_keys=True)}{json.dumps(headers)}{self.access_token}"
        return hashlib.md5(raw_key.encode()).hexdigest()
