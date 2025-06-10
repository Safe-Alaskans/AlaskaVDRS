from typing import List

from model_tuning_workspace.synthetic_data_pipeline.features.models.participant import Participant, \
    generate_participants
from model_tuning_workspace.synthetic_data_pipeline.features.mortality_cause import MortalityCauseFeature
from model_tuning_workspace.synthetic_data_pipeline.framework.feature import Feature, FeatureType, TopLevelFeature


class ParticipantCount(Feature):
    def __init__(self, options=None):
        super().__init__(
            "participant_count",
            FeatureType.DIVERSITY,
            options=options or ["1", "2", "3", "4"]
        )

    def build_prompt(self) -> str:
        return f"Participant count: {self.selected_value}"

class ParticipantsFeature(TopLevelFeature):
    def __init__(self, mortality_cause_ft: MortalityCauseFeature):
        super().__init__("participants")
        self.participants: List[Participant] = []
        self.mortality_cause_ft = mortality_cause_ft

    def init_sub_feature_values(self) -> None:
        count_options = ParticipantCount().options
        mortality_cause = self.mortality_cause_ft.cause_type.selected_value
        if mortality_cause == "manslaughter":
            count_options = ["2", "3"]
        elif mortality_cause == "suicide":
            count_options = ["1"]

        participant_count = ParticipantCount(options=count_options)
        count = participant_count.select_value()
        self.participants = generate_participants(count=int(count), include_victim=True, include_relationships=True)

    def build_prompt(self) -> str:
        if not self.participants:
            raise ValueError("No participants generated")
        return "# Participants:\n" + "".join(p.to_prompt_str(include_relationship=True) + "\n" for p in self.participants)

    def get_victim(self) -> Participant:
        return next(p for p in self.participants if p.is_victim)

    def validate_sub_features(self, output: str) -> bool:
        # TODO: Check there are n participants
        return True

    def serialize(self) -> dict:
        return {
            self.name: [p.serialize() for p in self.participants]
       }