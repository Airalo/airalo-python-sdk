"""
Cloud SIM Share Validator

Helper class for validating SIM cloud sharing data.
"""

import re
import json
from typing import Any, Dict, List

from ..exceptions.airalo_exception import AiraloException


class CloudSimShareValidator:
    """
    Validator for SIM cloud sharing payloads.
    """

    _email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    _allowed_sharing_options = {"link", "pdf"}

    @staticmethod
    def validate(
        sim_cloud_share: Dict[str, Any], required_fields: List[str] = None
    ) -> bool:
        """
        Validate the SIM cloud sharing payload.

        Args:
            sim_cloud_share: The payload dictionary.
            required_fields: List of required fields to validate.

        Raises:
            AiraloException: If validation fails.

        Returns:
            True if valid.
        """
        required_fields = required_fields or []

        CloudSimShareValidator._check_required_fields(sim_cloud_share, required_fields)

        # Validate 'to_email'
        to_email = sim_cloud_share.get("to_email")
        if to_email and not CloudSimShareValidator._email_regex.match(to_email):
            raise AiraloException(
                f"The to_email must be a valid email address, payload: {json.dumps(sim_cloud_share)}"
            )

        # Validate 'sharing_option'
        for option in sim_cloud_share.get("sharing_option", []):
            if option not in CloudSimShareValidator._allowed_sharing_options:
                allowed = " or ".join(CloudSimShareValidator._allowed_sharing_options)
                raise AiraloException(
                    f"The sharing_option may be {allowed} or both, payload: {json.dumps(sim_cloud_share)}"
                )

        # Validate 'copy_address' emails
        for cc_email in sim_cloud_share.get("copy_address", []):
            if not CloudSimShareValidator._email_regex.match(cc_email):
                raise AiraloException(
                    f"The copy_address: {cc_email} must be a valid email address, payload: {json.dumps(sim_cloud_share)}"
                )

        return True

    @staticmethod
    def _check_required_fields(
        sim_cloud_share: Dict[str, Any], required_fields: List[str]
    ) -> bool:
        """
        Ensure required fields exist and are not empty.

        Args:
            sim_cloud_share: Payload dictionary.
            required_fields: List of required keys.

        Raises:
            AiraloException: If a required field is missing or empty.

        Returns:
            True if all required fields are present.
        """
        for field in required_fields:
            if not sim_cloud_share.get(field):
                raise AiraloException(
                    f"The {field} field is required, payload: {json.dumps(sim_cloud_share)}"
                )
        return True
