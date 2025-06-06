import random
from dataclasses import dataclass
from typing import List, Optional

from model_tuning_workspace.synthetic_data_pipeline.features.models.physical_description import PhysicalDescription
from model_tuning_workspace.synthetic_data_pipeline.features.participant_sub_features import AgeFeature, GenderFeature, \
    EthnicityFeature, RelationshipFeature, AttireFeature, HeightFeature, WeightFeature, \
    ScarsFeature, TattoosFeature, generate_name


@dataclass
class Participant:
    id: int
    age_feature: AgeFeature
    gender_feature: GenderFeature
    ethnicity_feature: EthnicityFeature
    relationship_feature: RelationshipFeature
    full_name: str = "unknown"
    attire_feature: Optional[AttireFeature] = None # Just for victims
    physical_description: Optional[PhysicalDescription] = None # Just for victims
    is_victim: bool = False

    def to_prompt_str(self, include_relationship=False) -> str:
        role = "victim" if self.is_victim else "participant"
        base_str = f"{role.capitalize()}: {self.age_feature.build_prompt()}. {self.gender_feature.build_prompt()}. {self.ethnicity_feature.build_prompt()}"

        if self.full_name != "unknown":
            base_str += f". Name: {self.full_name}"

        if include_relationship and hasattr(self, 'relationship_feature') and self.relationship_feature:
            base_str += f". {self.relationship_feature.build_prompt()}"

        if hasattr(self, 'attire_feature') and self.attire_feature:
            base_str += f". {self.attire_feature.build_prompt()}"

        if hasattr(self, 'physical_description') and self.physical_description:
            base_str += f". {self.physical_description.build_prompt()}"
        return base_str

    def serialize(self) -> dict:
        base_dict = {
            "id": self.id,
            self.age_feature.name: self.age_feature.selected_value,
            self.gender_feature.name: self.gender_feature.selected_value,
            self.ethnicity_feature.name: self.ethnicity_feature.selected_value,
            "full_name": self.full_name,
            "is_victim": self.is_victim
        }

        if self.relationship_feature:
            base_dict[self.relationship_feature.name] = self.relationship_feature.selected_value
            if hasattr(self.relationship_feature, 'related_participant_id'):
                base_dict['related_participant_id'] = self.relationship_feature.related_participant_id

        if self.attire_feature:
            base_dict[self.attire_feature.name] = self.attire_feature.selected_value

        if self.physical_description:
            base_dict['physical_description'] = self.physical_description.serialize()

        return base_dict

def generate_participants(count: int, include_victim: bool = False, include_relationships: bool = False) -> List[Participant]:
    participants = []

    for i in range(count):
        age_feature = AgeFeature()
        gender_feature = GenderFeature()
        ethnicity_feature = EthnicityFeature()
        # Only create relationship feature if we have more than 1 participant and relationships are enabled
        relationship_feature = RelationshipFeature() if (count > 1 and include_relationships) else None

        age_feature.select_value()
        gender_feature.select_value()
        ethnicity_feature.select_value()
        if relationship_feature:
            relationship_feature.select_value()

        new_participant = Participant(
            i + 1,
            age_feature,
            gender_feature,
            ethnicity_feature,
            relationship_feature
        )
        participants.append(new_participant)

    if include_victim and participants:
        victim_count = 1 # Hardcoded for now, can be increased later
        victim_indices = random.sample(range(len(participants)), victim_count)

        # For each victim, potentially establish a relationship with another participant
        for idx in victim_indices:
            participants[idx].is_victim = True

            participants[idx].attire_feature = AttireFeature()
            participants[idx].attire_feature.select_value()

            participants[idx].full_name = generate_name(name_type=participants[idx].gender_feature.selected_value)

            phys_feature_classes = [HeightFeature, WeightFeature, ScarsFeature, TattoosFeature]
            selected_phys_features = []
            for FeatureClass in phys_feature_classes:
                feature = FeatureClass()
                feature.select_value()
                selected_phys_features.append(feature)
            participants[idx].physical_description = PhysicalDescription.create_from_features(selected_phys_features)

            if (include_relationships and count > 1 and
                    participants[idx].relationship_feature and
                    participants[idx].relationship_feature.selected_value != "no_connection"):

                # Find a non-victim participant to establish relationship with
                available_participants = [i for i in range(len(participants))
                                          if i != idx and not participants[i].is_victim]
                if available_participants:
                    related_idx = random.choice(available_participants)
                    participants[idx].relationship_feature.related_participant_id = participants[related_idx].id

    return participants
