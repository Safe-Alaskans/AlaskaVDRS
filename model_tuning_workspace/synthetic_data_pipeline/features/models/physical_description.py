from dataclasses import dataclass
from typing import List

from model_tuning_workspace.synthetic_data_pipeline.features.participant_sub_features import HeightFeature, \
    WeightFeature, ScarsFeature, TattoosFeature
from model_tuning_workspace.synthetic_data_pipeline.framework.feature import Feature


@dataclass
class PhysicalDescription:
    height_feature: HeightFeature
    weight_feature: WeightFeature
    scars_feature: ScarsFeature
    tattoos_feature: TattoosFeature

    @classmethod
    def create_from_features(cls, features: List[Feature]) -> 'PhysicalDescription':
        feature_dict = {
            f"{feature.__class__.__name__.lower().replace('feature', '')}_feature": feature
            for feature in features
        }
        return cls(**feature_dict)

    def build_prompt(self) -> str:
        return f"""
Physical Description:
Height: {self.height_feature.selected_value}
Weight: {self.weight_feature.selected_value}
Scars: {self.scars_feature.selected_value}
Tattoos: {self.tattoos_feature.selected_value}
""".strip()

    def serialize(self) -> dict:
        return {
            self.height_feature.name: self.height_feature.selected_value,
            self.weight_feature.name: self.weight_feature.selected_value,
            self.scars_feature.name: self.scars_feature.selected_value,
            self.tattoos_feature.name: self.tattoos_feature.selected_value
        }