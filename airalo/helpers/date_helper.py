# date_helper.py
from datetime import datetime


class DateHelper:
    @staticmethod
    def validate_date(date_str: str, date_format: str = "%Y-%m-%d") -> bool:
        try:
            datetime.strptime(date_str, date_format)
            return True
        except ValueError:
            return False
