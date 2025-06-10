from typing import Optional
from model_tuning_workspace.synthetic_data_pipeline.framework.feature import Feature, FeatureType, TopLevelFeature


class MortalityCauseType(Feature):
    def __init__(self):
        super().__init__(
            "cause_type",
            FeatureType.CORE,
            options=["manslaughter", "suicide", "murder", "accident"]
        )


class MortalityMethodType(Feature):
    def __init__(self):
        super().__init__(
            "method_type",
            FeatureType.CORE,
            options=[
                "firearm",
                "bladed_weapon",
                "blunt_object",
                "poison_drugs",
                "other"
            ]
        )

    def is_poison_or_drugs(self) -> bool:
        return self.selected_value == "poison_drugs"


class MethodDetails(Feature):
    def __init__(self, method_type: str):
        options = self._get_options_for_method(method_type)
        super().__init__(
            "method_details",
            FeatureType.DIVERSITY,
            options=options
        )

    def _get_options_for_method(self, method_type: str) -> list[str]:
        options_map = {
            "firearm": [
                "revolver",
                "semi_automatic_pistol",
                "hunting_rifle",
                "assault_rifle",
                "shotgun",
                "submachine_gun",
                "carbine",
                "derringer",
                "lever_action_rifle",
                "bolt_action_rifle",
                "automatic_pistol",
                "target_pistol",
                "sawed_off_shotgun",
                "break_action_shotgun",
                "pump_action_shotgun",
                "machine_pistol",
                "machine_gun",
                "sniper_rifle",
                "antique_firearm",
            ],
            "bladed_weapon": [
                "kitchen_knife",
                "hunting_knife",
                "pocket_knife",
                "switchblade",
                "butterfly_knife",
                "machete",
                "sword",
                "dagger",
                "bayonet",
                "razor_blade",
                "utility_knife",
                "combat_knife",
                "cleaver",
                "scalpel",
                "box_cutter",
                "bowie_knife",
                "folding_knife",
                "katana"
            ],
            "blunt_object": [
                "baseball_bat",
                "metal_pipe",
                "hammer",
                "crowbar",
                "wooden_stick",
                "golf_club",
                "tire_iron",
                "wrench",
                "brass_knuckles",
                "brick",
                "rock",
                "steel_rod",
                "pool_cue",
                "chair",
                "bottle",
                "flashlight",
                "walking_stick",
                "trophy",
                "fireplace_poker",
                "shovel",
                "table_leg",
                "rolling_pin",
                "chain"
            ],
            "poison_drugs": [
                "opioid_painkillers",
                "sleeping_pills",
                "antidepressants",
                "anxiety_medication",
                "heart_medication",
                "insulin",
                "heroin",
                "cocaine",
                "methamphetamine",
                "fentanyl",
                "rat_poison",
                "pesticides",
                "cleaning_products",
                "antifreeze",
                "carbon_monoxide",
                "cyanide",
                "mercury",
                "arsenic",
                "bleach",
                "drain_cleaner",
                "paint_thinner",
                "fertilizer",
                "mushrooms",
                "plant_toxins"
            ],
            "other": [
                "strangulation",
                "hanging",
                "drowning",
                "fall_from_height",
                "fall_down_stairs",
                "vehicular_collision",
                "vehicular_hit_and_run",
                "vehicle_push_off_road",
                "suffocation",
                "electrocution",
                "exposure_to_elements",
                "buried_alive",
                "trapped_in_confined_space",
                "industrial_accident"
            ]
        }
        return options_map.get(method_type, ["unknown"])


class InjuryCount(Feature):
    def __init__(self):
        super().__init__(
            "injury_count",
            FeatureType.CORE,
            options=[
                "single",
                "multiple_between_2_3",
                "multiple_3_plus",
            ]
        )


class MortalityCauseFeature(TopLevelFeature):
    def __init__(self):
        super().__init__("mortality_cause")
        self.cause_type = MortalityCauseType()
        self.method_type = MortalityMethodType()
        self.method_details: Optional[MethodDetails] = None
        self.injury_count: Optional[InjuryCount] = None

    def init_sub_feature_values(self) -> None:
        self.cause_type.select_value()
        selected_method = self.method_type.select_value()

        methods_which_do_not_require_injury_count = ["poison_drugs", "other"]
        if selected_method not in methods_which_do_not_require_injury_count:
            self.injury_count = InjuryCount()
            if self.cause_type.selected_value in ["accident", "suicide"]:
                self.injury_count.selected_value = "single"
            else:
                self.injury_count.select_value()

        self.method_details = MethodDetails(selected_method)
        self.method_details.select_value()

    def build_prompt(self) -> str:
        if not all([self.cause_type, self.method_type, self.method_details]):
            raise ValueError(
                f"Not all features have been initialized: Cause Type: {self.cause_type}, Method Type: {self.method_type}, Method Details: {self.method_details}")

        value = (f"# Mortality Cause:\n"
                 f"Cause: {self.cause_type.selected_value}\n"
                 f"Method: {self.method_type.selected_value}\n"
                 f"Details: {self.method_details.selected_value}\n")

        if self.injury_count:
            value += f"Injury Count: {self.injury_count.selected_value}\n"

        return value

    def validate_sub_features(self, output: str) -> bool:
        # TODO: Implement validation to check if:
        # - The cause type is mentioned in the output
        # - The method type is mentioned in the output
        # - The method details are consistent with the output
        return True

    def serialize(self) -> dict:
        ft_dict = {self.name: {
            self.cause_type.name: self.cause_type.selected_value,
            self.method_type.name: self.method_type.selected_value,
            self.method_details.name: self.method_details.selected_value,
        }}

        if self.injury_count:
            ft_dict[self.name][self.injury_count.name] = self.injury_count.selected_value

        return ft_dict
