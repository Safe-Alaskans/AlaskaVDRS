from model_tuning_workspace.synthetic_data_pipeline.framework.feature import TopLevelFeature, Feature, FeatureType


class ShouldIncludeIrrelevantDrugs(Feature):

        def __init__(self):
            super().__init__(
                "should_include_irrelevant_drugs",
                FeatureType.CORE,
                options=[
                    ("yes", 0.1),
                    ("no", 0.9),
                ]
            )

class ShouldIncludeIrrelevantWeapons(Feature):

        def __init__(self):
            super().__init__(
                "should_include_irrelevant_weapons",
                FeatureType.CORE,
                options=[
                    ("yes", 0.02),
                    ("no", 0.98),
                ]
            )

        def did_include_irrelevant_weapons(self) -> bool:
            return self.selected_value == "yes"

class UnrelatedInfoFeature(TopLevelFeature):

    def __init__(self):
        super().__init__(name="unrelated_info")
        self.should_include_irrelevant_drugs = ShouldIncludeIrrelevantDrugs()
        self.should_include_irrelevant_weapons = ShouldIncludeIrrelevantWeapons()

    def init_sub_feature_values(self) -> None:
        self.should_include_irrelevant_drugs.select_value()
        self.should_include_irrelevant_weapons.select_value()

    def build_prompt(self) -> str:
        should_incl_irr_drugs = self.should_include_irrelevant_drugs.selected_value
        should_incl_irr_weapons = self.should_include_irrelevant_weapons.selected_value
        if should_incl_irr_drugs == "no" and should_incl_irr_weapons == "no":
            return ""
        return (f"# Unrelated Info:\n"
                f"{"" if should_incl_irr_drugs == 'no' else 'You should mention some drugs which were discovered on scene but which are not relevant to the case'}\n"
                f"{'' if should_incl_irr_weapons == 'no' else 'You should mention some weapons which were discovered on scene but which are not relevant to the case'}\n")


    def validate_sub_features(self, output: str) -> bool:
        pass

    def serialize(self) -> dict:
        return {
            self.name: {
                self.should_include_irrelevant_drugs.name: self.should_include_irrelevant_drugs.selected_value,
                self.should_include_irrelevant_weapons.name: self.should_include_irrelevant_weapons.selected_value
            }
        }