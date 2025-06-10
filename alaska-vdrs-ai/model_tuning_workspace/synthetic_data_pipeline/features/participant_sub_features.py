import datetime
import random
from typing import Optional
from faker import Faker

from model_tuning_workspace.synthetic_data_pipeline.framework.feature import FeatureType, Feature


class AgeFeature(Feature):
    def __init__(self):
        super().__init__(
            "age",
            FeatureType.DIVERSITY,
            options=[
                "young",
                "middle",
                "senior"
            ]
        )
        self.date_of_birth: Optional[datetime.date] = None

    def get_dob(self) -> datetime.date:
        if not self.selected_value:
            raise ValueError("No age selected")

        if self.date_of_birth:
            return self.date_of_birth

        today = datetime.date.today()

        age_ranges = {
            "young": (15, 35),
            "middle": (36, 55),
            "senior": (56, 85)
        }

        if self.selected_value not in age_ranges:
            raise ValueError(f"Invalid age range: {self.selected_value}")

        min_age, max_age = age_ranges[self.selected_value]

        # Calculate date range
        earliest_date = today - datetime.timedelta(days=max_age*365)
        latest_date = today - datetime.timedelta(days=min_age*365)

        # Generate random date within range
        days_range = (latest_date - earliest_date).days
        random_days = random.randint(0, days_range)

        dob = earliest_date + datetime.timedelta(days=random_days)
        self.date_of_birth = dob
        return dob



    def build_prompt(self) -> str:
        return f"Age: {self.selected_value}"

class GenderFeature(Feature):
    def __init__(self):
        super().__init__(
            "gender",
            FeatureType.DIVERSITY,
            options=[
                "male",
                "female",
            ]
        )

    def build_prompt(self) -> str:
        return f"Gender: {self.selected_value}"


class EthnicityFeature(Feature):

    def __init__(self):
        super().__init__(
            "ethnicity",
            FeatureType.DIVERSITY,
            options=[
                "white",
                "black",
                "asian",
                "hispanic"
            ]
        )

    def build_prompt(self) -> str:
        return f"Ethnicity: {self.selected_value}"


class RelationshipFeature(Feature):
    def __init__(self, options=None):
        super().__init__(
            "relationship_status",
            FeatureType.DIVERSITY,
            options=options or ["related", "acquainted", "no_connection"]
        )
        self.related_participant_id: Optional[int] = None

    def build_prompt(self) -> str:
        if self.selected_value == "no_connection":
            return ""
        elif self.related_participant_id is not None:
            connection_type = "related to" if self.selected_value == "related" else "acquainted with"
            return f"Is {connection_type} Participant {self.related_participant_id}"
        return f"Has a {self.selected_value} connection to another participant"


class AttireFeature(Feature):
    def __init__(self):
        super().__init__(
            "attire",
            FeatureType.DIVERSITY,
            options=[
                "formal_business",
                "business_casual",
                "casual",
                "athletic_wear",
                "traditional_cultural",
                "medical_gown",
                "swimwear",
                "sleepwear",
                "partially_clothed",
                "unclothed"
            ]
        )

    def build_prompt(self) -> str:
        return f"Attire when found: {self.selected_value}"

class HeightFeature(Feature):
    def __init__(self):
        super().__init__(
            "height",
            FeatureType.DIVERSITY,
            options=[
                "short",
                "average",
                "tall"
            ]
        )

    def build_prompt(self) -> str:
        return f"Height: {self.selected_value}"

class WeightFeature(Feature):
    def __init__(self):
        super().__init__(
            "weight",
            FeatureType.DIVERSITY,
            options=[
                "extremely_underweight",
                "slightly_underweight",
                "average",
                "slightly_overweight",
                "obese",
                "extremely_obese"
            ]
        )

    def build_prompt(self) -> str:
        return f"Weight: {self.selected_value}"

class ScarsFeature(Feature):
    def __init__(self):
        super().__init__(
            "scars",
            FeatureType.DIVERSITY,
            options=[
                "none",
                "single_small",
                "single_large",
                "multiple_small",
                "multiple_large",
            ]
        )

    def build_prompt(self) -> str:
        return f"Scars: {self.selected_value}"

class TattoosFeature(Feature):
    def __init__(self):
        super().__init__(
            "tattoos",
            FeatureType.DIVERSITY,
            options=[
                "none",
                "single",
                "few",
                "many",
                "full_body"
            ]
        )

    def build_prompt(self) -> str:
        return f"Tattoos: {self.selected_value}"


def generate_name(name_type='full'):
    """
    Generate random names using Faker
    """
    fake = Faker()

    name_generators = {
        'male': fake.name_male,
        'female': fake.name_female
    }

    if name_type in name_generators:
        generator = name_generators[name_type]
    else:
        generator = fake.name

    return generator()