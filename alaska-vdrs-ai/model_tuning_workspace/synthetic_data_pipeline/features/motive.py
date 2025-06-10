from model_tuning_workspace.synthetic_data_pipeline.framework.feature import Feature, FeatureType, TopLevelFeature

class MotiveType(Feature):
    def __init__(self):
        super().__init__(
            "motive_type",
            FeatureType.DIVERSITY,
            options=[
                # Financial motives
                "robbery",
                "insurance_fraud",
                "inheritance",
                "debt_collection",
                "business_dispute",
                "gambling_debt",
                "extortion",
                "embezzlement_coverup",

                # Personal relationships
                "domestic_dispute",
                "jealousy",
                "revenge",
                "rejection",
                "infidelity",
                "custody_dispute",
                "family_honor",
                "stalking_escalation",
                "breakup",
                "long_term_abuse",

                # Criminal
                "gang_related",
                "organized_crime",
                "witness_elimination",
                "drug_territory",
                "criminal_initiation",

                # Professional conflicts
                "workplace_grievance",
                "professional_rivalry",
                "wrongful_termination",
                "whistleblower_retaliation",
                "workplace_bullying",
                "client_dispute",
                "professional_jealousy",
                "contract_dispute",

                # Property disputes
                "boundary_dispute",
                "inheritance_property",
                "homeowners_association",
                "noise_complaint_escalation",
                "trespassing_dispute",
                "shared_property_conflict",
                "construction_dispute"
            ]
        )

class MotiveFeature(TopLevelFeature):
    def __init__(self):
        super().__init__("motive")
        self.motive_type = MotiveType()

    def init_sub_feature_values(self) -> None:
        self.motive_type.select_value()

    def build_prompt(self) -> str:
        if not self.motive_type:
            raise ValueError("Motive type has not been initialized")

        return f"# Motive:\nType: {self.motive_type.selected_value}"

    def validate_sub_features(self, output: str) -> bool:
        return True

    def serialize(self) -> dict:
        return {
            self.name: {
                self.motive_type.name: self.motive_type.selected_value
            }
        }