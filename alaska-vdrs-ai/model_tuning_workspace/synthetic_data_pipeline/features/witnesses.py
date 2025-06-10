from typing import List

from model_tuning_workspace.synthetic_data_pipeline.features.models.participant import Participant, \
    generate_participants
from model_tuning_workspace.synthetic_data_pipeline.features.participants import ParticipantCount
from model_tuning_workspace.synthetic_data_pipeline.framework.feature import TopLevelFeature


class WitnessesFeature(TopLevelFeature):
    def __init__(self):
        super().__init__(
            "witnesses",
        )
        self.witnesses: List[Participant] = []

    def init_sub_feature_values(self) -> None:
        participant_count = ParticipantCount(
            options=[
                ("0", 0.94),
                ("1", 0.05),
                ("2", 0.01),
            ]
        )
        count = participant_count.select_value()
        self.witnesses = generate_participants(int(count))

    def build_prompt(self) -> str:
        header = "# Witnesses:\n"
        if len(self.witnesses) == 0:
            return header + "No witnesses"
        return header + "".join(w.to_prompt_str() for w in self.witnesses)

    def validate_sub_features(self, output: str) -> bool:
        # TODO: Check there are n witnesses
        return True

    def serialize(self) -> dict:
        return {
            "witnesses": [w.serialize() for w in self.witnesses]
        }