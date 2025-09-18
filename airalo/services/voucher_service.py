import json

from airalo.config import Config
from airalo.constants.api_constants import ApiConstants
from airalo.constants.sdk_constants import SdkConstants
from airalo.exceptions.airalo_exception import AiraloException
from airalo.helpers.signature import Signature
from airalo.resources.http_resource import HttpResource


class VoucherService:
    def __init__(
        self,
        config: Config,
        curl: HttpResource,
        signature: Signature,
        access_token: str,
    ):
        if not access_token:
            raise AiraloException("Invalid access token please check your credentials")

        self.config = config
        self.curl = curl
        self.signature = signature
        self.access_token = access_token

    def create_voucher(self, payload: dict) -> dict | None:
        self._validate_voucher(payload)

        headers = self._get_headers(payload)
        response = self.curl.set_headers(headers).post(
            self.config.get_url() + ApiConstants.VOUCHERS_SLUG, payload
        )

        if self.curl.code != 200:
            raise AiraloException(
                f"Voucher creation failed, status code: {self.curl.code}, response: {response}"
            )

        return json.loads(response)

    def create_esim_voucher(self, payload: dict) -> dict | None:
        self._validate_esim_voucher(payload)

        headers = self._get_headers(payload)
        response = self.curl.set_headers(headers).post(
            self.config.get_url() + ApiConstants.VOUCHERS_ESIM_SLUG, payload
        )

        if self.curl.code != 200:
            raise AiraloException(
                f"Voucher creation failed, status code: {self.curl.code}, response: {response}"
            )

        return json.loads(response)

    def _get_headers(self, payload: dict) -> list[str]:
        return [
            "Content-Type: application/json",
            f"Authorization: Bearer {self.access_token}",
            f"airalo-signature: {self.signature.get_signature(payload)}",
        ]

    def _validate_voucher(self, payload: dict) -> None:
        if "amount" not in payload or payload["amount"] == "" or payload["amount"] < 1:
            raise AiraloException(
                f"The amount is required, payload: {json.dumps(payload)}"
            )

        if payload["amount"] > SdkConstants.VOUCHER_MAX_NUM:
            raise AiraloException(
                f"The amount may not be greater than {SdkConstants.VOUCHER_MAX_NUM}"
            )

        if (
            "voucher_code" in payload
            and isinstance(payload["voucher_code"], str)
            and len(payload["voucher_code"]) > 255
        ):
            raise AiraloException("The voucher code may not exceed 255 characters.")

        if (
            "voucher_code" in payload
            and "quantity" in payload
            and payload["quantity"] > 1
        ):
            raise AiraloException(
                "The selected voucher code allows a maximum quantity of 1"
            )

        if "usage_limit" in payload and (
            payload["usage_limit"] < 1
            or payload["usage_limit"] > SdkConstants.VOUCHER_MAX_NUM
        ):
            raise AiraloException(
                f"The usage_limit may not be greater than {SdkConstants.VOUCHER_MAX_NUM}"
            )

        if (
            "quantity" not in payload
            or payload["quantity"] == ""
            or payload["quantity"] < 1
        ):
            raise AiraloException(
                f"The quantity is required, payload: {json.dumps(payload)}"
            )

        if payload["quantity"] > SdkConstants.VOUCHER_MAX_QUANTITY:
            raise AiraloException(
                f"The quantity may not be greater than {SdkConstants.VOUCHER_MAX_QUANTITY}"
            )

    def _validate_esim_voucher(self, payload: dict) -> None:
        if not payload.get("vouchers"):
            raise AiraloException(
                f"vouchers field is required, payload: {json.dumps(payload)}"
            )

        if not isinstance(payload["vouchers"], list):
            raise AiraloException(
                f"vouchers field should be an array, payload: {json.dumps(payload)}"
            )

        for voucher in payload["vouchers"]:
            if not voucher.get("package_id"):
                raise AiraloException(
                    f"The vouchers.package_id is required, payload: {json.dumps(payload)}"
                )

            if not voucher.get("quantity"):
                raise AiraloException(
                    f"The vouchers.quantity is required and should be greater than 0, payload: {json.dumps(payload)}"
                )

            if payload.get("quantity", 0) > SdkConstants.VOUCHER_MAX_QUANTITY:
                raise AiraloException(
                    f"The vouchers.quantity may not be greater than {SdkConstants.VOUCHER_MAX_QUANTITY}"
                )
