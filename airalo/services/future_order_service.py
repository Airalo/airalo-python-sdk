import json
from datetime import datetime

from ..config import Config
from ..helpers.signature import Signature
from ..exceptions.airalo_exception import AiraloException
from ..resources.http_resource import HttpResource
from ..constants.api_constants import ApiConstants
from ..constants.sdk_constants import SdkConstants
from ..helpers.cloud_sim_share_validator import CloudSimShareValidator


class FutureOrderService:
    def __init__(
        self,
        config: Config,
        http_resource: HttpResource,
        signature: Signature,
        access_token: str,
    ):
        if not access_token:
            raise AiraloException(
                "Invalid access token, please check your credentials."
            )

        self.config = config
        self.http = http_resource
        self.signature = signature
        self.access_token = access_token
        self.base_url = self.config.get_url()

    def create_future_order(self, payload: dict) -> dict:
        self._validate_future_order(payload)
        self._validate_cloud_sim_share(payload)

        payload = {k: v for k, v in payload.items() if v}

        url = self.base_url + ApiConstants.FUTURE_ORDERS
        headers = self._get_headers(payload)

        response = self.http.set_headers(headers).post(url, payload)

        if self.http.code != 200:
            raise AiraloException(
                f"Future order creation failed, status code: {self.http.code}, response: {response}"
            )

        return json.loads(response)

    def cancel_future_order(self, payload: dict) -> dict:
        self._validate_cancel_future_order(payload)

        url = self.base_url + ApiConstants.CANCEL_FUTURE_ORDERS
        headers = self._get_headers(payload)

        response = self.http.set_headers(headers).post(url, payload)

        if self.http.code != 200:
            raise AiraloException(
                f"Future order cancellation failed, status code: {self.http.code}, response: {response}"
            )

        return json.loads(response)

    def _get_headers(self, payload: dict) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "airalo-signature": self.signature.get_signature(payload),
        }

    def _validate_future_order(self, payload: dict) -> None:
        if not payload.get("package_id"):
            raise AiraloException(
                f"The package_id is required, payload: {json.dumps(payload)}"
            )

        if payload.get("quantity", 0) < 1:
            raise AiraloException(
                f"The quantity is required, payload: {json.dumps(payload)}"
            )

        if payload["quantity"] > SdkConstants.FUTURE_ORDER_LIMIT:
            raise AiraloException(
                f"The packages count may not be greater than {SdkConstants.BULK_ORDER_LIMIT}"
            )

        due_date = payload.get("due_date")
        if not due_date:
            raise AiraloException(
                f"The due_date is required (format: Y-m-d H:i), payload: {json.dumps(payload)}"
            )

        try:
            parsed_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
            if parsed_date.strftime("%Y-%m-%d %H:%M") != due_date:
                raise ValueError()
        except ValueError:
            raise AiraloException(
                f"The due_date must be in the format Y-m-d H:i, payload: {json.dumps(payload)}"
            )

    def _validate_cancel_future_order(self, payload: dict) -> None:
        if (
            not isinstance(payload.get("request_ids"), list)
            or not payload["request_ids"]
        ):
            raise AiraloException(
                f"The request_ids is required, payload: {json.dumps(payload)}"
            )

    def _validate_cloud_sim_share(self, sim_cloud_share: dict) -> None:
        CloudSimShareValidator.validate(sim_cloud_share)
