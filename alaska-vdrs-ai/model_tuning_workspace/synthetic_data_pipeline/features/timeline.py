import random
from datetime import date
from typing import Optional

from model_tuning_workspace.synthetic_data_pipeline.framework.feature import TopLevelFeature, Feature, FeatureType


class TimeSinceMortality(Feature):
    def __init__(self):
        super().__init__(
            "time_since_mortality",
            FeatureType.DIVERSITY,
            options=[
                "less_than_1_hour",
                "1_3_hours",
                "3_6_hours",
                "6_12_hours",
                "12_24_hours",
                "24_48_hours",
                "48_72_hours",
                "3_7_days",
                "7_14_days",
                "14_30_days",
                "30_plus_days"
            ]
        )

class DateOfDeath(Feature):

    def __init__(self):
        super().__init__(
            "date_specificity",
            FeatureType.CORE,
            options=[
    # Fixed holiday states
    "explicitly_mention_holiday_christmas_eve",
    "explicitly_mention_holiday_christmas_day",
    "explicitly_mention_holiday_new_year_eve",
    "explicitly_mention_holiday_new_year_day",
    "explicitly_mention_holiday_halloween",
    "explicitly_mention_holiday_july_fourth",
    "explicitly_mention_holiday_thanksgiving",
    "explicitly_mention_holiday_labor_day",
    "explicitly_mention_holiday_memorial_day",
    "explicitly_mention_holiday_easter",
    "explicitly_mention_holiday_valentines",
    "explicitly_mention_holiday_st_patricks",
    "explicitly_mention_holiday_mothers_day",
    "explicitly_mention_holiday_fathers_day",

    # Explicit date requirements
    "explicitly_mention_date_specify_in_jan",
    "explicitly_mention_date_specify_in_feb",
    "explicitly_mention_date_specify_in_mar",
    "explicitly_mention_date_specify_in_apr",
    "explicitly_mention_date_specify_in_may",
    "explicitly_mention_date_specify_in_jun",
    "explicitly_mention_date_specify_in_jul",
    "explicitly_mention_date_specify_in_aug",
    "explicitly_mention_date_specify_in_sep",
    "explicitly_mention_date_specify_in_oct",
    "explicitly_mention_date_specify_in_nov",
    "explicitly_mention_date_specify_in_dec",

    # Generic time references
    "explicitly_mention_time_month_only",
    "explicitly_mention_time_weekday_start",
    "explicitly_mention_time_weekday_middle",
    "explicitly_mention_time_weekday_end",
    "explicitly_mention_time_weekend_any",
    "explicitly_mention_time_weekday_any",
    "explicitly_mention_time_weekday_morning",
    "explicitly_mention_time_weekday_afternoon",
    "explicitly_mention_time_weekday_evening",
    "explicitly_mention_time_weekday_night",
    "explicitly_mention_time_weekend_morning",
    "explicitly_mention_time_weekend_afternoon",
    "explicitly_mention_time_weekend_evening",

    "do_not_mention_date_or_day",
]
        )

class WhoDiscoveredBody(Feature):

    def __init__(self):
        super().__init__(
            "discovery_method",
            FeatureType.DIVERSITY,
            options=[
                "police_officer",
                "firefighter",
                "paramedic",
                "family_member",
                "friend",
                "neighbor",
                "stranger",
                "passerby",
                "landlord",
                "employer",
                "employee",
                "other"
            ]
        )

class NumKeyEvents(Feature):

    def __init__(self):
        super().__init__(
            "num_key_events",
            FeatureType.DIVERSITY,
            options=[
                "1",
                "2",
                "3",
            ]
        )

class DateOfIncident(Feature):
    def __init__(self):
        super().__init__(
            "date_specificity",
            FeatureType.CORE
        )
        self.date_of_case: Optional[date] = None

    def select_value(self) -> str:
        if self.date_of_case:
            return self.date_of_case.strftime('%Y-%m-%d')

        year = random.randint(2022, 2024)
        month = random.randint(1, 12)
        # Get the last day of the selected month to avoid invalid dates
        last_day = 31
        if month in [4, 6, 9, 11]:
            last_day = 30
        elif month == 2:
            # Handle February and leap years
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                last_day = 29
            else:
                last_day = 28

        day = random.randint(1, last_day)

        self.date_of_case = date(year, month, day)
        return self.date_of_case.strftime('%Y-%m-%d')

    def get_date_of_case(self) -> date:
        if not self.date_of_case:
            raise ValueError("Date of incident has not been selected yet")
        return self.date_of_case

class DaysAfterCase(Feature):

    def __init__(self):
        super().__init__(
            "days_after_case",
            FeatureType.DIVERSITY,
            options=[
                "0",
                "1",
                "2",
                "3",
            ]
        )


class TimelineFeature(TopLevelFeature):

    def __init__(self):
        super().__init__(
            "timeline",
        )
        self.time_since_mortality = TimeSinceMortality()
        self.date_of_death = DateOfDeath()
        self.who_discovered_body = WhoDiscoveredBody()
        self.num_key_events = NumKeyEvents()
        self.date_of_incident = DateOfIncident()
        self.days_after_case_before_autopsy = DaysAfterCase()

    def init_sub_feature_values(self) -> None:
        self.time_since_mortality.select_value()
        self.date_of_death.select_value()
        self.who_discovered_body.select_value()
        self.num_key_events.select_value()
        self.date_of_incident.select_value()
        self.days_after_case_before_autopsy.select_value()

    def build_prompt(self) -> str:
        return (f"# Timeline:\n"
                f"Date of incident: {self.date_of_incident.selected_value}\n"
                f"Time since death before body was found: {self.time_since_mortality.selected_value}\n"
                f"Date of death: {self.date_of_death.selected_value}\n"
                f"Who discovered the body: {self.who_discovered_body.selected_value}\n"
                f"Number of key events: {self.num_key_events.selected_value}\n")

    def validate_sub_features(self, output: str) -> bool:
        pass

    def serialize(self) -> dict:
        return {
            self.name: {
                self.time_since_mortality.name: self.time_since_mortality.selected_value,
                self.date_of_death.name: self.date_of_death.selected_value,
                self.who_discovered_body.name: self.who_discovered_body.selected_value,
                self.num_key_events.name: self.num_key_events.selected_value,
                self.date_of_incident.name: self.date_of_incident.selected_value,
                self.days_after_case_before_autopsy.name: self.days_after_case_before_autopsy.selected_value
            }
        }