from model_tuning_workspace.evaluations.cases import validator_model
from model_tuning_workspace.evaluations.cases.assets.load import load_txt_input_doc
from model_tuning_workspace.evaluations.eval_case import EvalCase
from model_tuning_workspace.evaluations.validators.date_mention_validator import DateMentionValidator
from model_tuning_workspace.evaluations.validators.key_info_validator import KeyInfoValidator
from model_tuning_workspace.evaluations.validators.length_validator import LengthValidator
from model_tuning_workspace.evaluations.validators.pii_validator import PIIValidator
from model_tuning_workspace.evaluations.validators.report_detail_validator import ReportDetailValidator
from model_tuning_workspace.prompting.user_msg import build_user_message

all_base_cases = [
    EvalCase(
        description="Base test - Checking model provides a narrative that includes key information, no PII and no dates",
        input_text=build_user_message(
            [
                load_txt_input_doc("example_5_docs", "autopsy"),
                load_txt_input_doc("example_5_docs", "me_narrative"),
                load_txt_input_doc("example_5_docs", "toxicology")
            ]
        ),
        validators=[
            PIIValidator(model_exec=validator_model),
            KeyInfoValidator(
                info_to_check=[
                    "The victim recently had a breakup with their partner",
                    "LE found the victim",
                    "A shotgun was found on the scene",
                    "The victim was shot in the head",
                    "The victim was found on a sofa",
                    "Toxicology reports showed the victim had 0.250 BAC"
                ],
                model_exec=validator_model,
            ),
            DateMentionValidator(),
            LengthValidator(),
            ReportDetailValidator(model_exec=validator_model)
        ]
    ),
    EvalCase(
        description="Testing to make sure the model does not include irrelevant information",
        input_text=build_user_message(
            [
                load_txt_input_doc("example_5_docs", "autopsy"),
                load_txt_input_doc("example_5_docs", "me_narrative_with_irrelevant_weapons_and_drugs"),
                load_txt_input_doc("example_5_docs", "toxicology")
            ],
        ),
        validators=[
            PIIValidator(model_exec=validator_model),
            KeyInfoValidator(
                info_to_check=[
                    "There is no mention of a machete",
                    "There is no mention of cannabis",
                ],
                model_exec=validator_model,
            ),
            DateMentionValidator(),
            LengthValidator(),
        ]
    ),
    EvalCase(
        description="Testing to ensure model can handle an overdose case",
        input_text=build_user_message(
            [
                load_txt_input_doc("fatal_overdose_synth_case", "autopsy"),
                load_txt_input_doc("fatal_overdose_synth_case", "me_narrative"),
                load_txt_input_doc("fatal_overdose_synth_case", "toxicology")
            ]
        ),
        validators=[
            PIIValidator(model_exec=validator_model),
            KeyInfoValidator(
                info_to_check=[
                    "The victim was found in a hotel",
                    "The victim had 1500 ng/mL concentration of amphetamines",
                    "The victim had a history of substance abuse",
                ],
                model_exec=validator_model,
            ),
            DateMentionValidator(),
            LengthValidator(),
            ReportDetailValidator(model_exec=validator_model)
        ]
    ),
    EvalCase(
        description="Testing to ensure model includes the witness in a case when present, also checking that the circumstance is recorded",
        input_text=build_user_message(
            [
                load_txt_input_doc("witness_involved_synth_case", "autopsy"),
                load_txt_input_doc("witness_involved_synth_case", "me_narrative"),
                load_txt_input_doc("witness_involved_synth_case", "toxicology")
            ],
        ),
        validators=[
            PIIValidator(model_exec=validator_model),
            KeyInfoValidator(
                info_to_check=[
                    "This shooting was self-defense",
                    "There was a witness to the shooting",
                    "Cannabinoids were found in the victim's system",
                ],
                model_exec=validator_model,
            ),
            DateMentionValidator(),
            LengthValidator(),
            ReportDetailValidator(model_exec=validator_model)
        ],
    ),
    EvalCase(
        description="Testing to ensure model describes relationship between parties in a case. Also checking that no toxicology information is included",
        input_text=build_user_message(
            [
                load_txt_input_doc("family_member_accidental_synth_case", "autopsy"),
                load_txt_input_doc("family_member_accidental_synth_case", "me_narrative"),
                load_txt_input_doc("family_member_accidental_synth_case", "toxicology")
            ],
        ),
        validators=[
            PIIValidator(model_exec=validator_model),
            KeyInfoValidator(
                info_to_check=[
                    "The suspect was the victim's brother",
                    "There is no mention of toxicology",
                    "There was an argument between the suspect and the victim due to gambling",
                ],
                model_exec=validator_model,
            ),
            DateMentionValidator(),
            LengthValidator(),
            ReportDetailValidator(model_exec=validator_model)
        ],
    ),
    EvalCase(
        description="Testing to ensure model can handle a case which is known to induce the LLM to include irrelevant clothing & toxicology information",
        input_text=build_user_message(
            [
                load_txt_input_doc("problematic_case_irr_info_0", "autopsy"),
                load_txt_input_doc("problematic_case_irr_info_0", "me_narrative"),
                load_txt_input_doc("problematic_case_irr_info_0", "toxicology")
            ],
        ),
        validators=[
            PIIValidator(model_exec=validator_model),
            KeyInfoValidator(
                info_to_check=[
                    "There is no mention of what the victim was wearing",
                    "There is no mention of toxicology findings",
                    "Explicitly includes the statements \"cause of death \" & \"manner of death\" in the narrative",
                ],
                model_exec=validator_model,
            ),
            DateMentionValidator(),
            LengthValidator(),
            ReportDetailValidator(model_exec=validator_model)
        ],
    ),
    EvalCase(
        description="Testing to ensure model can handle a case which is known to induce the LLM to include irrelevant weight info of the victim."
                    "This case also incites the LLM to talk in too much detail about the victim's injuries."
                    "This case also incites the LLM to include irrelevant toxicology information.",
        input_text=build_user_message(
            [
                load_txt_input_doc("problematic_case_irr_info_1", "autopsy"),
                load_txt_input_doc("problematic_case_irr_info_1", "me_narrative"),
                load_txt_input_doc("problematic_case_irr_info_1", "toxicology")
            ],
        ),
        validators=[
            PIIValidator(model_exec=validator_model),
            KeyInfoValidator(
                info_to_check=[
                    "There is no mention of toxicology findings",
                    "There is no mention of the victim's weight",
                ],
                model_exec=validator_model,
            ),
            DateMentionValidator(),
            LengthValidator(),
            ReportDetailValidator(model_exec=validator_model)
        ],
    ),
    EvalCase(
        description="Testing to ensure model can handle a case which is known to induce the LLM to include irrelevant weight info of the victim.",
        input_text=build_user_message(
            [
                load_txt_input_doc("problematic_case_irr_info_2", "autopsy"),
                load_txt_input_doc("problematic_case_irr_info_2", "me_narrative"),
                load_txt_input_doc("problematic_case_irr_info_2", "toxicology")
            ],
        ),
        validators=[
            PIIValidator(model_exec=validator_model),
            KeyInfoValidator(
                info_to_check=[
                    "There is no mention of the victim's height or weight",
                ],
                model_exec=validator_model,
            ),
            DateMentionValidator(),
            LengthValidator(),
            ReportDetailValidator(model_exec=validator_model)
        ],
    ),
    EvalCase(
        description="Testing to ensure model can handle a case which is known to induce the LLM to include irrelevant weight info of the victim.",
        input_text=build_user_message(
            [
                load_txt_input_doc("problematic_case_irr_info_3", "autopsy"),
                load_txt_input_doc("problematic_case_irr_info_3", "me_narrative"),
                load_txt_input_doc("problematic_case_irr_info_3", "toxicology")
            ],
        ),
        validators=[
            PIIValidator(model_exec=validator_model),
            KeyInfoValidator(
                info_to_check=[
                    "There is no mention that the victim is obese",
                ],
                model_exec=validator_model,
            ),
            DateMentionValidator(),
            LengthValidator(),
            ReportDetailValidator(model_exec=validator_model)
        ],
    )
]
