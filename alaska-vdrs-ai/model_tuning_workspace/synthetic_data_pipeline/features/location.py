from model_tuning_workspace.synthetic_data_pipeline.framework.feature import FeatureType, Feature, TopLevelFeature


class LocationTypeFeature(Feature):
    def __init__(self):
        super().__init__(
            "location_type",
            FeatureType.DIVERSITY,
            options=[
                "house",
                "apartment",
                "alley",
                "parking",
                "motel",
                "park",
                "mall",
                "school",
                "church",
                "bank",
                "casino",
                "warehouse",
                "garage",
                "store",
                "club"
            ]
        )


class LocationRelationshipToVictimFeature(Feature):
    def __init__(self):
        super().__init__(
            "location_relationship_to_victim",
            FeatureType.CORE,
            options=[
                "not_related",
                "related",
            ]
        )


class LocationBusinessNamesFeature(Feature):
    def __init__(self):
        super().__init__(
            "include_organisation_names",
            FeatureType.CORE,
            options=[
                "include",
                "exclude"
            ]
        )


class LocationStreetNamesFeature(Feature):
    def __init__(self):
        super().__init__(
            "include_location_names",
            FeatureType.CORE,
            options=[
                "include",
                "exclude"
            ]
        )


class LocationFeature(TopLevelFeature):
    def __init__(self):
        super().__init__(
            "location",
        )
        self.type = LocationTypeFeature()
        self.relationship_to_victim = LocationRelationshipToVictimFeature()
        self.business_names = LocationBusinessNamesFeature()
        self.street_names = LocationStreetNamesFeature()

    def init_sub_feature_values(self) -> None:
        self.type.select_value()
        self.relationship_to_victim.select_value()
        self.business_names.select_value()
        self.street_names.select_value()

    def build_prompt(self) -> str:
        return (f"# Location:\n"
                f"Type: {self.type.selected_value}\n"
                f"Whether the location is somehow linked or related to the victim: {self.relationship_to_victim.selected_value}\n"
                f"Whether you should include organisation names (such as local businesses/LE agencies/Hospitals, etc..): {self.business_names.selected_value}\n"
                f"Whether you should include location names (such as streets, cities/towns, etc..): {self.street_names.selected_value}")

    def validate_sub_features(self, output: str) -> bool:
        # TODO: Validate location features are present in output
        pass

    def serialize(self) -> dict:
        return {
            self.name: {
                self.type.name: self.type.selected_value,
                self.relationship_to_victim.name: self.relationship_to_victim.selected_value,
                self.business_names.name: self.business_names.selected_value,
                self.street_names.name: self.street_names.selected_value
            }
        }