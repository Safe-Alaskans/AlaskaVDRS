from typing import List, Tuple
import re
import holidays
from datetime import datetime
from model_tuning_workspace.evaluations.validators.result_entities import ValidationResult
from model_tuning_workspace.evaluations.validators.validator_base import Validator


class DateMentionValidator(Validator):
    def __init__(self):
        # Common month names and abbreviations
        self.months = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
            "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept",
            "oct", "nov", "dec"
        ]

        # Seasons
        self.seasons = ["summer", "winter", "spring", "fall", "autumn"]

        # Initialize holidays for multiple years to catch references
        current_year = datetime.now().year
        self.holiday_list = []
        us_holidays = holidays.country_holidays("US", years=[current_year, current_year - 1]).items()
        for date, holiday_name in us_holidays:
            self.holiday_list.append(holiday_name)
            self.holiday_list.append(holiday_name.lower())

        # Common time-related words
        self.time_indicators = [
            "yesterday", "today", "tomorrow", "weekend", "weekday",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "mon", "tue", "wed", "thu", "fri", "sat", "sun"
        ]

    def _find_dates(self, text: str) -> List[Tuple[str, str]]:
        found_mentions = []
        text_lower = text.lower()

        # 1. Check for dates with regex
        date_regex = r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"
        matches = re.finditer(date_regex, text_lower)
        for match in matches:
            found_mentions.append((text[match.start():match.end()], "date"))

        # 2. Check for month mentions
        for month in self.months:
            matches = re.finditer(r'\b' + month + r'\b', text_lower)
            for match in matches:
                found_mentions.append((text[match.start():match.end()], "month"))

        # 3. Check for season mentions
        for season in self.seasons:
            matches = re.finditer(r'\b' + season + r'\b', text_lower)
            for match in matches:
                found_mentions.append((text[match.start():match.end()], "season"))

        # 4. Check for holiday mentions
        for holiday in self.holiday_list:
            holiday_name = holiday.lower()
            if holiday_name in text_lower:
                found_mentions.append((holiday, "holiday"))

        # 5. Check for time indicators
        for indicator in self.time_indicators:
            matches = re.finditer(r'\b' + indicator + r'\b', text_lower)
            for match in matches:
                found_mentions.append((text[match.start():match.end()], "time_reference"))

        # Remove duplicates while preserving order
        seen = set()
        return [x for x in found_mentions if not (x in seen or seen.add(x))]

    def validate(self, output: str, eval_case_id: str) -> ValidationResult:
        # Find all date mentions
        found_mentions = self._find_dates(output)

        # Create details string in CSV format
        details = ""
        if found_mentions:
            details = "text,category\n" + "\n".join(
                f"{mention},{category}"
                for mention, category in found_mentions
            )

        return ValidationResult(
            validator=self.__class__.__name__,
            eval_case_id=eval_case_id,
            validator_description="Checking for presence of dates, days, and time period references",
            passed=len(found_mentions) == 0,
            details=details
        )